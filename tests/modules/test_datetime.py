import pytest
from freezegun import freeze_time

from i3pyblocks.modules import datetime as m_datetime


@freeze_time("2020-04-19T17:00:00")
@pytest.mark.asyncio
async def test_datetime_module():
    # Use a non locale dependent format
    instance = m_datetime.DateTimeModule(format_time="%H:%M:%S", format_date="%y-%m-%d")
    await instance.run()

    assert instance.result()["full_text"] == "17:00:00"

    # Simulate click
    await instance.click_handler()
    assert instance.result()["full_text"] == "20-04-19"

    # Simulate another click, should go back to hours
    await instance.click_handler()
    assert instance.result()["full_text"] == "17:00:00"
