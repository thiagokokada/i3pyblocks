import time

from i3pyblocks.core import PollingModule


class Color:
    GOOD = "#00FF00"
    NEUTRAL = None
    URGENT = "#FF0000"
    WARN = "#FFFF00"


class LocalTimeModule(PollingModule):
    def __init__(
        self, format_date: str = "%D", format_time: str = "%T", **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.format_date = format_date
        self.format_time = format_time
        self.format = self.format_time

    def click_handler(self, *args, **kwargs) -> None:
        if self.format == self.format_date:
            self.format = self.format_time
        else:
            self.format = self.format_date

        super().click_handler(*args, **kwargs)

    def run(self) -> None:
        current_time = time.localtime()
        self.update(time.strftime(self.format, current_time))


# Import sub-modules so they're available for imports
import i3pyblocks.modules.psutil  # noqa: E402, F401
