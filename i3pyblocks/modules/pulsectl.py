import pulsectl

from i3pyblocks import core, utils


class PulseAudioModule(core.PollingModule):
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
        self.pulse = pulsectl.Pulse(__name__)
        self._find_default_sink()
        self._update_sink_info()

    def _find_default_sink(self) -> None:
        server_info = self.pulse.server_info()

        for sink in self.pulse.sink_list():
            if sink.name == server_info.default_sink_name:
                self.sink = sink
                return

    def _update_sink_info(self) -> None:
        self.sink = self.pulse.sink_info(self.sink.index)

    def click_handler(self, button: int, **kwargs):
        if button == utils.Mouse.RIGHT_BUTTON:
            if self.sink.mute:
                self.pulse.mute(self.sink, mute=False)
            else:
                self.pulse.mute(self.sink, mute=True)
        elif button == utils.Mouse.SCROLL_UP:
            self.pulse.volume_change_all_chans(self.sink, 0.05)
        elif button == utils.Mouse.SCROLL_DOWN:
            self.pulse.volume_change_all_chans(self.sink, -0.05)

        super().click_handler(**kwargs)

    def run(self) -> None:
        self._update_sink_info()

        if self.sink.mute:
            self.update(self.format_mute.format(), color=utils.Color.URGENT)
        else:
            volume = self.pulse.volume_get_all_chans(self.sink) * 100
            color = utils.calculate_threshold(self.colors, volume)
            icon = utils.calculate_threshold(self.icons, volume)
            self.update(self.format.format(volume=volume, icon=icon), color=color)
