from asyncio import subprocess

import pytest

from i3pyblocks import utils


def test_calculate_threshold():
    fixture = [(-1, "item0"), (0, "item1"), (5.5, "item2"), (10, "item3")]

    # Works with both a Dict and a Dictable
    # (i.e.: something that can be converted to Dict)
    assert utils.calculate_threshold(dict(fixture), -3) is None
    assert utils.calculate_threshold(fixture, -2) is None
    assert utils.calculate_threshold(dict(fixture), -1) == "item0"
    assert utils.calculate_threshold(fixture, 0) == "item1"
    assert utils.calculate_threshold(dict(fixture), 5) == "item1"
    assert utils.calculate_threshold(fixture, 5.5) == "item2"
    assert utils.calculate_threshold(dict(fixture), 6) == "item2"
    assert utils.calculate_threshold(fixture, 10) == "item3"
    assert utils.calculate_threshold(dict(fixture), 11) == "item3"


def test_non_nullable_dict():
    assert utils.non_nullable_dict(foo="bar", spams=None) == {"foo": "bar"}


@pytest.mark.asyncio
async def test_shell_run():
    stdout, stderr, process = await utils.shell_run(
        command="""
        cat -
        echo Hello World | cut -d" " -f2
        echo Someone 1>&2
        exit 1
        """,
        input=b"Hello ",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert stdout == b"Hello World\n"
    assert stderr == b"Someone\n"
    assert process.returncode == 1


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
