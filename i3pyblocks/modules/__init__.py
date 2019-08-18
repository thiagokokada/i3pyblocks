import time

from i3pyblocks.core import PollingModule

# Import sub-modules so they're available for imports
import i3pyblocks.modules.psutil  # noqa: F401


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
