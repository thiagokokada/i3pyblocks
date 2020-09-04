import subprocess
import time
from typing import NoReturn, Optional, Sequence

import pulsectl
from pulsectl import PulseError, PulseLoopStop

from i3pyblocks import blocks, types
from i3pyblocks._internal import utils


# Based on: https://git.io/fjbHp
class PulseAudioBlock(blocks.ExecutorBlock):
    def __init__(
        self,
        format: str = "V: {volume:.0f}%",
        format_mute: str = "V: MUTE",
        colors: types.Dictable[int, Optional[str]] = (
            (0, types.Color.URGENT),
            (10, types.Color.WARN),
            (25, types.Color.NEUTRAL),
        ),
        icons: types.Dictable[float, str] = (
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ),
        command: Sequence[str] = ("pavucontrol",),
        *,
        _pulsectl=pulsectl,
        _subprocess=subprocess,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.format_mute = format_mute
        self.colors = dict(colors)
        self.icons = dict(icons)
        self.command = command
        self.pulsectl = _pulsectl
        self.subprocess = _subprocess

        # https://pypi.org/project/pulsectl/#event-handling-code-threads
        self.pulse = self.pulsectl.Pulse(__name__, connect=False)
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
        except PulseError:
            # Waiting a little before trying to connect again so we don't
            # burn CPU in a infinity loop
            time.sleep(0.5)
            self._initialize_pulse()

    def _event_callback(self, event) -> NoReturn:
        self.event = event
        raise PulseLoopStop()

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
        if self.sink.mute:
            self.update(self.format_mute.format(), color=types.Color.URGENT)
        else:
            volume = self.pulse.volume_get_all_chans(self.sink) * 100
            color = utils.calculate_threshold(self.colors, volume)
            icon = utils.calculate_threshold(self.icons, volume)
            self.update(self.format.format(volume=volume, icon=icon), color=color)

    def toggle_mute(self):
        if self.sink.mute:
            self.pulse.mute(self.sink, mute=False)
        else:
            self.pulse.mute(self.sink, mute=True)

    def change_volume(self, volume: float):
        # TODO: Use self.pulse instead of our own Pulse instance here
        # Using self.pulse.volume_change_all_chans() may cause a deadlock
        # when successive operations are done
        # We probably need have better control over loop in pulsectl
        with self.pulsectl.Pulse("volume-changer") as pulse:
            pulse.volume_change_all_chans(self.sink, volume)

    async def click_handler(self, button: int, **_kwargs) -> None:
        if button == types.MouseButton.LEFT_BUTTON:
            self.subprocess.Popen(self.command)
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
