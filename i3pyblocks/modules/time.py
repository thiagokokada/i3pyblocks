import time

from i3pyblocks import modules


class LocalTimeModule(modules.PollingModule):
    def __init__(
        self, format_date: str = "%D", format_time: str = "%T", **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.format_date = format_date
        self.format_time = format_time
        self.format = self.format_time

    async def click_handler(self, *_, **__) -> None:
        if self.format == self.format_date:
            self.format = self.format_time
        else:
            self.format = self.format_date

        await self.run()

    async def run(self) -> None:
        current_time = time.localtime()
        self.update(time.strftime(self.format, current_time))
