from datetime import datetime

from i3pyblocks import blocks


class DateTimeBlock(blocks.PollingBlock):
    def __init__(
        self,
        format_date: str = "%D",
        format_time: str = "%T",
        *,
        sleep: int = 1,
        _datetime=datetime,
        **kwargs
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format_date = format_date
        self.format_time = format_time
        self.format = self.format_time
        self.datetime = _datetime

    async def click_handler(self, **_kwargs) -> None:
        if self.format == self.format_date:
            self.format = self.format_time
        else:
            self.format = self.format_date

        await self.run()

    async def run(self) -> None:
        current_time = self.datetime.now()
        self.update(current_time.strftime(self.format))
