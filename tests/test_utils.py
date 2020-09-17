import asyncio
import doctest

from i3pyblocks import utils


def test_utils_docstrings():
    failure_count, test_count = doctest.testmod(utils)
    assert test_count == 3
    assert failure_count == 0


def test_pango_markup():
    assert utils.pango_markup("Hello") == "<span>Hello</span>"
    assert (
        utils.pango_markup("Blue text", foreground="blue", size="x-large")
        == '<span foreground="blue" size="x-large">Blue text</span>'
    )
    assert (
        utils.pango_markup("Big italic", tag="i", size="x-large")
        == '<i size="x-large">Big italic</i>'
    )


def test_asyncio_run():
    async def fn():
        await asyncio.sleep(0.1)
        return "Hello!"

    result = utils.asyncio_run(fn())
    assert result == "Hello!"
