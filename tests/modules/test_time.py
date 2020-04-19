import time

import pytest

from i3pyblocks.modules import time as m_time


@pytest.mark.asyncio
async def test_local_time_module(mocker):
    mocker.patch.object(
        time, "localtime", return_value=time.strptime("Fri Aug 16 21:00:00 2019")
    )

    # Use a non locale dependent format
    instance = m_time.LocalTimeModule(format_time="%H:%M:%S", format_date="%y-%m-%d")
    await instance.run()

    assert instance.result()["full_text"] == "21:00:00"

    # Simulate click
    await instance.click_handler()

    assert instance.result()["full_text"] == "19-08-16"
