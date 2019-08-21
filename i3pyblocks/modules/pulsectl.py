import asyncio

import pulsectl

from i3pyblocks import core, utils

# Based on:
# https://github.com/lf-/aiopanel/blob/2786f1116aa2ea0dfe7f331b174104843972fec2/aiopanel.py#L437
class PulseAudioModule(core.Module):
    def __init__(
        self,
        format: str = "V: {volume:.0f}%",
        format_mute: str = "V: MUTE",
        colors: utils.Items = [
            (0, utils.Color.URGENT),
            (10, utils.Color.WARN),
            (25, utils.Color.NEUTRAL),
        ],
        icons: utils.Items = [
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ],
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.format_mute = format_mute
        self.colors = colors
        self.icons = icons
        # https://pypi.org/project/pulsectl/#event-handling-code-threads
        self.pulse = pulsectl.Pulse(__name__, threading_lock=True)
        self._find_default_sink()
        self._update_sink_info()

    def __exit__(self, *args):
        self.pulse.close()

    def _find_default_sink(self) -> None:
        server_info = self.pulse.server_info()

        for sink in self.pulse.sink_list():
            if sink.name == server_info.default_sink_name:
                self.sink = sink
                return

    def _update_sink_info(self) -> None:
        self.sink = self.pulse.sink_info(self.sink.index)

    def _handle_event(self, event):
        if event.facility == "server":
            self._find_default_sink()
            self._update_sink_info()
        elif event.facility == "sink":
            self._update_sink_info()

    def _event_callback(self, event):
        self.event = event
        raise pulsectl.PulseLoopStop()

    def _loop(self) -> None:
        self.run()
        self.pulse.event_mask_set("sink", "server")
        self.pulse.event_callback_set(self._event_callback)

        while True:
            self.run()

            self.pulse.event_listen()

            self._handle_event(self.event)

    async def loop(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._loop)

    def signal_handler(self, *_, **__):
        self.run()

    def click_handler(self, button: int, **kwargs):
        def toggle_mute():
            if self.sink.mute:
                self.pulse.mute(self.sink, mute=False)
            else:
                self.pulse.mute(self.sink, mute=True)

        if button == utils.Mouse.RIGHT_BUTTON:
            toggle_mute()
        elif button == utils.Mouse.SCROLL_UP:
            self.pulse.volume_change_all_chans(self.sink, 0.05)
        elif button == utils.Mouse.SCROLL_DOWN:
            self.pulse.volume_change_all_chans(self.sink, -0.05)

        self.run()

    def run(self) -> None:
        if self.sink.mute:
            self.update(self.format_mute.format(), color=utils.Color.URGENT)
        else:
            volume = self.pulse.volume_get_all_chans(self.sink) * 100
            color = utils.calculate_threshold(self.colors, volume)
            icon = utils.calculate_threshold(self.icons, volume)
            self.update(self.format.format(volume=volume, icon=icon), color=color)
