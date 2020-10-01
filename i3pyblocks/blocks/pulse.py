"""Blocks related to PulseAudio, based on `pulsectl`_.

This module contains PulseAudioBlock, that uses ``pulsectl`` to show/adjust
volume in systems that runs `PulseAudio`_.

``pulsectl`` uses its own event loop so this module is based on
``SyncBlock`` running it in a separate thread, but this module should be
pretty efficient since it react to events from PulseAudio itself.

Needs PulseAudio installed in your computer, or you will receive the following
error when trying to run this module::

    OSError: libpulse.so.0: cannot open shared object file: No such file or directory

.. _pulsectl:
    https://github.com/mk-fg/python-pulse-control
.. _PulseAudio:
    https://www.freedesktop.org/wiki/Software/PulseAudio/
"""

from typing import Optional

import pulsectl

from i3pyblocks import blocks, logger, types
from i3pyblocks._internal import misc, models, subprocess


# Based on: https://git.io/fjbHp
class PulseAudioBlock(blocks.SyncBlock):
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
        :class:`~i3pyblocks.blocks.base.SyncBlock` class.

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
        command: models.CommandArgs = ("pavucontrol",),
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.format_mute = format_mute
        self.colors = colors
        self.color_mute = color_mute
        self.icons = icons
        self.command = command

    def _event_callback(self, event: pulsectl.PulseEventInfo) -> None:
        if event.facility == "server":
            self.find_sink_index()

        self.update_status()

    def find_sink_index(self) -> None:
        with pulsectl.Pulse("find-sink") as pulse:
            server_info = pulse.server_info()

            default_sink_name = server_info.default_sink_name
            logger.debug(f"Found new default sink: {default_sink_name}")

            sink_list = pulse.sink_list()
            logger.debug(f"Current available sinks: {sink_list}")

            self.sink_index = next(
                # Find the sink with default_sink_name
                (sink.index for sink in sink_list if sink.name == default_sink_name),
                # Returns the first from the list as fallback
                0,
            )

    def update_status(self) -> None:
        """Update the PulseAudioBlock state."""
        with pulsectl.Pulse("update-status") as pulse:
            sink = pulse.sink_info(self.sink_index)

            if sink.mute:
                self.update(self.format_mute, color=self.color_mute)
            else:
                volume = pulse.volume_get_all_chans(sink) * 100
                color = misc.calculate_threshold(self.colors, volume)
                icon = misc.calculate_threshold(self.icons, volume)
                self.update(
                    self.ex_format(self.format, volume=volume, icon=icon),
                    color=color,
                )

    def toggle_mute(self) -> None:
        """Toggle mute on/off."""
        with pulsectl.Pulse("toggle-mute") as pulse:
            sink = pulse.sink_info(self.sink_index)

            if sink.mute:
                pulse.mute(sink, mute=False)
            else:
                pulse.mute(sink, mute=True)

    def change_volume(self, volume: float) -> None:
        """Change volume of the current PulseAudio sink.

        :param volume: Float to be increased/decreased relative to the current
            volume. To decrease the volume use a negative value.
        """
        # TODO: Use self.pulse instead of our own Pulse instance here
        # Using self.pulse.volume_change_all_chans() may cause a deadlock
        # when successive operations are done
        # We probably need have better control over loop in pulsectl
        with pulsectl.Pulse("volume-changer") as pulse:
            sink = pulse.sink_info(self.sink_index)
            pulse.volume_change_all_chans(sink, volume)

    def signal_handler_sync(self, **_kwargs):
        self.update_status()

    def click_handler_sync(self, button: int, **_kwargs) -> None:
        """PulseAudioBlock click handlers

        On left click it opens the command specified in ``command`` attribute.
        On right click it toggles mute.
        On scroll up it increases the volume.
        On scroll down it decreases the volume.
        """
        if button == types.MouseButton.LEFT_BUTTON:
            subprocess.popener(self.command)
        elif button == types.MouseButton.RIGHT_BUTTON:
            self.toggle_mute()
        elif button == types.MouseButton.SCROLL_UP:
            self.change_volume(0.05)
        elif button == types.MouseButton.SCROLL_DOWN:
            self.change_volume(-0.05)

        self.update_status()

    def start_sync(self) -> None:
        self.find_sink_index()
        self.update_status()

        with pulsectl.Pulse("event-loop") as pulse:
            pulse.event_mask_set("sink", "server")
            pulse.event_callback_set(self._event_callback)
            pulse.event_listen()
