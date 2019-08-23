import asyncio
import subprocess
from typing import Sequence

import pulsectl

from i3pyblocks import core, utils


# Based on: https://git.io/fjbHp
class PulseAudioModule(core.Module):
    def __init__(
        self,
        format: str = "V: {volume:.0f}%",
        format_mute: str = "V: MUTE",
        colors: utils.Items = (
            (0, utils.Color.URGENT),
            (10, utils.Color.WARN),
            (25, utils.Color.NEUTRAL),
        ),
        icons: utils.Items = (
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
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.format_mute = format_mute
        self.colors = colors
        self.icons = icons
        self.command = command

        # https://pypi.org/project/pulsectl/#event-handling-code-threads
        self.pulse = pulsectl.Pulse(__name__, threading_lock=True)

        self._find_default_sink()
        self._update_sink_info()
        self._setup_event_callback()

    def __exit__(self, *_) -> None:
        self.pulse.close()

    def _setup_event_callback(self) -> None:
        def event_callback(event):
            self.event = event
            raise pulsectl.PulseLoopStop()

        self.pulse.event_mask_set("sink", "server")
        self.pulse.event_callback_set(event_callback)

    def _find_default_sink(self) -> None:
        server_info = self.pulse.server_info()

        for sink in self.pulse.sink_list():
            if sink.name == server_info.default_sink_name:
                self.sink = sink
                return

        self.sink = None

    def _update_sink_info(self) -> None:
        if self.sink:
            self.sink = self.pulse.sink_info(self.sink.index)

    def _handle_event(self, event) -> None:
        if event.facility == "server":
            self._find_default_sink()
            self._update_sink_info()
        elif event.facility == "sink":
            self._update_sink_info()

    def _loop(self) -> None:
        while True:
            self.run()

            self.pulse.event_listen()

            self._handle_event(self.event)

    async def loop(self) -> None:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._loop)
        except Exception as e:
            utils.Log.exception(f"Exception in {self.name}")
            self.update(f"Exception in {self.name}: {e}", urgent=True)

    def signal_handler(self, *_, **__) -> None:
        self.run()

    def click_handler(self, button: int, *_, **__) -> None:  # type: ignore
        def toggle_mute():
            if self.sink.mute:
                self.pulse.mute(self.sink, mute=False)
            else:
                self.pulse.mute(self.sink, mute=True)

        if button == utils.Mouse.LEFT_BUTTON:
            subprocess.Popen(self.command)
        elif button == utils.Mouse.RIGHT_BUTTON:
            toggle_mute()
        elif button == utils.Mouse.SCROLL_UP:
            self.pulse.volume_change_all_chans(self.sink, 0.05)
        elif button == utils.Mouse.SCROLL_DOWN:
            self.pulse.volume_change_all_chans(self.sink, -0.05)

        self.run()

    def run(self) -> None:
        if not self.sink:
            return

        if self.sink.mute:
            self.update(self.format_mute.format(), color=utils.Color.URGENT)
        else:
            volume = self.pulse.volume_get_all_chans(self.sink) * 100
            color = utils.calculate_threshold(self.colors, volume)
            icon = utils.calculate_threshold(self.icons, volume)
            self.update(self.format.format(volume=volume, icon=icon), color=color)
