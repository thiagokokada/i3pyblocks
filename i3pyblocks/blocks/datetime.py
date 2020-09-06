"""Blocks based on `datetime`_.

.. _datetime:
  https://docs.python.org/3/library/datetime.html
"""

from datetime import datetime

from i3pyblocks import blocks


class DateTimeBlock(blocks.PollingBlock):
    """Block that shows date and time for current location.

    This blocks alternates between Time and Date display by clicks in the
    Block. Keep in mind that ``format_date`` and ``format_time`` names are
    arbitrary and both formats have capacity to display both date and time.

    Args:
      format_date:
        Format string when showing date. Uses `strftime`_ placeholders.
      format_time:
        Format string when showing time. Uses `strftime`_ placeholders.
      sleep:
        Sleep in seconds between each call to ``run()``. If you're not showing
        seconds in this block it makes sense to increase this value.
      **kwargs:
        Extra arguments to be passed to ``PollingBlock`` class.

    .. _strftime:
      https://strftime.org/
    """

    def __init__(
        self,
        format_date: str = "%D",
        format_time: str = "%T",
        sleep: int = 1,
        *,
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
