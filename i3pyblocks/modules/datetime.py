from datetime import datetime

from i3pyblocks import modules


class DateTimeModule(modules.PollingModule):
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
        current_time = datetime.now()
        self.update(current_time.strftime(self.format))
