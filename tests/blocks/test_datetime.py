from datetime import datetime
from unittest.mock import Mock

import pytest

from i3pyblocks.blocks import datetime as m_datetime


@pytest.mark.asyncio
async def test_datetime_block():
    mock_datetime = Mock(datetime)
    mock_datetime.now.return_value = datetime(2020, 8, 25, 23, 30, 0)

    # Use a non locale dependent format
    instance = m_datetime.DateTimeBlock(
        format_time="%H:%M:%S", format_date="%y-%m-%d", _datetime=mock_datetime
    )
    await instance.run()

    assert instance.result()["full_text"] == "23:30:00"

    # Simulate click
    await instance.click_handler()
    assert instance.result()["full_text"] == "20-08-25"

    # Simulate another click, should go back to hours
    await instance.click_handler()
    assert instance.result()["full_text"] == "23:30:00"
