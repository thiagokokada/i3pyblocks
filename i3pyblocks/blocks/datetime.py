"""Blocks based on `datetime`_.

.. _datetime:
    https://docs.python.org/3/library/datetime.html
"""

from datetime import datetime

from i3pyblocks import blocks


class DateTimeBlock(blocks.PollingBlock):
    r"""Block that shows date and time for current location.

    This blocks alternates between Time and Date display by clicks in the
    Block. Keep in mind that ``format_date`` and ``format_time`` names are
    arbitrary and both formats have capacity to display both date and time.

    :param format_date: Format string when showing date. Uses `strftime`_
        placeholders.

    :param format_time: Format string when showing time. Uses `strftime`_
        placeholders.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`. If you're not
        showing seconds in this block it makes sense to increase this value.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.

    .. _strftime:
        https://strftime.org/
    """

    def __init__(
        self,
        format_date: str = "%D",
        format_time: str = "%T",
        sleep: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format_date = format_date
        self.format_time = format_time
        self.format = self.format_time

    def toggle_date_time(self) -> None:
        if self.format == self.format_date:
            self.format = self.format_time
        else:
            self.format = self.format_date

    async def click_handler(self, **_kwargs) -> None:
        self.toggle_date_time()
        await self.run()

    async def run(self) -> None:
        current_time = datetime.now()
        self.update(current_time.strftime(self.format))
