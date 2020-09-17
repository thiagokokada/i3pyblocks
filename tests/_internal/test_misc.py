import asyncio
from unittest.mock import patch

import pytest

from i3pyblocks._internal import misc


def test_calculate_threshold():
    fixture = [(-1, "item0"), (0, "item1"), (5.5, "item2"), (10, "item3")]

    # Works with both a Dict and a Dictable
    # (i.e.: something that can be converted to Dict)
    assert misc.calculate_threshold(dict(fixture), -3) is None
    assert misc.calculate_threshold(fixture, -2) is None
    assert misc.calculate_threshold(dict(fixture), -1) == "item0"
    assert misc.calculate_threshold(fixture, 0) == "item1"
    assert misc.calculate_threshold(dict(fixture), 5) == "item1"
    assert misc.calculate_threshold(fixture, 5.5) == "item2"
    assert misc.calculate_threshold(dict(fixture), 6) == "item2"
    assert misc.calculate_threshold(fixture, 10) == "item3"
    assert misc.calculate_threshold(dict(fixture), 11) == "item3"


def test_non_nullable_dict():
    assert misc.non_nullable_dict(foo="bar", spams=None) == {"foo": "bar"}
    assert misc.non_nullable_dict(
        bool=False,
        float=0.0,
        int=0,
        none=None,
        string="",
    ) == {
        "bool": False,
        "float": 0.0,
        "int": 0,
        "string": "",
    }

    # It is not recursive
    some_dict = {
        "nobody": None,
        "some": "body",
        "to": {"love": None},
    }
    assert misc.non_nullable_dict(**some_dict) == {
        "some": "body",
        "to": {"love": None},
    }


# TODO: Validate if we can actually read from stdin here
@pytest.mark.asyncio
async def test_get_aio_reader(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.return_value = b"Hello!"

        loop = asyncio.get_event_loop()

        with capsys.disabled():
            reader = await misc.get_aio_reader(loop)
            assert isinstance(reader, asyncio.StreamReader)
