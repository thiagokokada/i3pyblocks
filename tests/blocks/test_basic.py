import pytest

from i3pyblocks.blocks import basic


@pytest.mark.asyncio
async def test_basic_block():
    instance = basic.TextBlock(
        "Hello World",
        block_name="foo",
        short_text="Hello",
    )

    await instance.start()

    assert instance.block_name == "foo"
    assert instance.result()["full_text"] == "Hello World"
    assert instance.result()["short_text"] == "Hello"
