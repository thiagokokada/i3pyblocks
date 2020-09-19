"""Blocks related to PulseAudio, based on `pulsectl`_.

This module contains PulseAudioBlock, that uses ``pulsectl`` to show/adjust
volume in systems that runs `PulseAudio`_.

``pulsectl`` uses its own event loop so this module is based on
``ExecutorBlock`` running it in a separate thread, but this module should be
pretty efficient since it react to events from PulseAudio itself.

Needs PulseAudio installed in your computer, or you will receive the following
error when trying to run this module::

    OSError: libpulse.so.0: cannot open shared object file: No such file or directory

.. _pulsectl:
    https://github.com/mk-fg/python-pulse-control
.. _PulseAudio:
    https://www.freedesktop.org/wiki/Software/PulseAudio/
"""

import subprocess
import time
from typing import Optional

import pulsectl

from i3pyblocks import blocks, types
from i3pyblocks._internal import misc, models


# Based on: https://git.io/fjbHp
class PulseAudioBlock(blocks.ExecutorBlock):
    r"""Block that shows volume and other info from default PulseAudio sink.

    This Block shows the volume of the current default PulseAudio sink, and
    also includes a ``click_handler()`` allowing you to mute the default sink
    using right button or increase/decrease the volume using scroll up/down.
    It will also open a program on the left click, by default it calls the
    `pavucontrol`_ but this is configurable.

    :param format: Format string showed when the audio sink is not mute. Supports
        both ``{volume}`` and ``{icon}`` placeholders.

    :param format_mute: Format string showing when the audio sink is mute. It
        will be shown with ``color_mute`` set.

    :param colors: A mapping that represents the color that will be shown in each
        volume interval. For example::

            {
                0: "000000",
                10: "#FF0000",
                50: "#FFFFFF",
            }

        When the volume is between [0, 10) the color is set to "000000", from
        [10, 50) is set to "FF0000" and from 50 and beyond it is "#FFFFFF".

    :param color_mute: Color used when the sound is mute.

    :param icons: Similar to ``colors``, but for icons. Can be used to create a
        graphic representation of the volume. Only displayed when ``format``
        includes ``{icon}`` placeholder.

    :param command: Program to run when this block is right clicked.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.ExecutorBlock` class.

    .. _pavucontrol:
      https://freedesktop.org/software/pulseaudio/pavucontrol/
    """

    def __init__(
        self,
        format: str = "V: {volume:.0f}%",
        format_mute: str = "V: MUTE",
        colors: models.Threshold = {
            0: types.Color.URGENT,
            10: types.Color.WARN,
            25: types.Color.NEUTRAL,
        },
        color_mute: Optional[str] = types.Color.URGENT,
        icons: models.Threshold = {
            0.0: "▁",
            12.5: "▂",
            25.0: "▃",
            37.5: "▄",
            50.0: "▅",
            62.5: "▆",
            75.0: "▇",
            87.5: "█",
        },
        command: str = "pavucontrol",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.format_mute = format_mute
        self.colors = colors
        self.color_mute = color_mute
        self.icons = icons
        self.command = command

        # https://pypi.org/project/pulsectl/#event-handling-code-threads
        self.pulse = pulsectl.Pulse(__name__, connect=False)
        self._initialize_pulse()

    def _initialize_pulse(self):
        self.pulse.connect(autospawn=True)

        self._find_sink_index()
        self._update_sink_info()
        self._setup_event_callback()

    def _find_sink_index(self) -> None:
        server_info = self.pulse.server_info()
        default_sink_name = server_info.default_sink_name
        sink_list = self.pulse.sink_list()

        assert len(sink_list) > 0, "No sinks found"

        self.sink_index = next(
            # Find the sink with default_sink_name
            (sink.index for sink in sink_list if sink.name == default_sink_name),
            # Returns the first from the list as fallback
            0,
        )

    def _update_sink_info(self) -> None:
        try:
            self.sink = self.pulse.sink_info(self.sink_index)
        except pulsectl.PulseError:
            # Waiting a little before trying to connect again so we don't
            # burn CPU in a infinity loop
            time.sleep(0.5)
            self._initialize_pulse()

    def _event_callback(self, event) -> None:
        self.event = event
        raise pulsectl.PulseLoopStop()

    def _setup_event_callback(self) -> None:
        self.pulse.event_mask_set("sink", "server")
        self.pulse.event_callback_set(self._event_callback)

    def handle_event(self) -> None:
        self.pulse.event_listen()

        if self.event.facility == "server":
            self._find_sink_index()
            self._update_sink_info()
        elif self.event.facility == "sink":
            self._update_sink_info()

    def update_status(self):
        """Update the PulseAudioBlock state."""
        if self.sink.mute:
            self.update(self.format_mute, color=self.color_mute)
        else:
            volume = self.pulse.volume_get_all_chans(self.sink) * 100
            color = misc.calculate_threshold(self.colors, volume)
            icon = misc.calculate_threshold(self.icons, volume)
            self.update(
                self.ex_format(self.format, volume=volume, icon=icon),
                color=color,
            )

    def toggle_mute(self):
        """Toggle mute on/off."""
        with pulsectl.Pulse("toggle-mute") as pulse:
            if self.sink.mute:
                pulse.mute(self.sink, mute=False)
            else:
                pulse.mute(self.sink, mute=True)

    def change_volume(self, volume: float):
        """Change volume of the current PulseAudio sink.

        :param volume: Float to be increased/decreased relative to the current
            volume. To decrease the volume use a negative value.
        """
        # TODO: Use self.pulse instead of our own Pulse instance here
        # Using self.pulse.volume_change_all_chans() may cause a deadlock
        # when successive operations are done
        # We probably need have better control over loop in pulsectl
        with pulsectl.Pulse("volume-changer") as pulse:
            pulse.volume_change_all_chans(self.sink, volume)

    async def click_handler(self, button: int, **_kwargs) -> None:
        """PulseAudioBlock click handlers

        On left click it opens the command specified in ``command`` attribute.
        On right click it toggles mute.
        On scroll up it increases the volume.
        On scroll down it decreases the volume.
        """
        if button == types.MouseButton.LEFT_BUTTON:
            subprocess.Popen(self.command, shell=True)
        elif button == types.MouseButton.RIGHT_BUTTON:
            self.toggle_mute()
        elif button == types.MouseButton.SCROLL_UP:
            self.change_volume(0.05)
        elif button == types.MouseButton.SCROLL_DOWN:
            self.change_volume(-0.05)

        self.update_status()

    def run(self) -> None:
        while True:
            self.update_status()
            self.handle_event()
