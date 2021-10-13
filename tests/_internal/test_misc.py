import asyncio
from inspect import Parameter, Signature, signature

import pytest
from mock import patch

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


def test_delegates():
    def foo(a, b):
        pass

    @misc.delegates(foo)
    def bar(*args):
        foo(*args)

    s = signature(bar)
    assert s == Signature(
        parameters=[
            Parameter("a", Parameter.POSITIONAL_OR_KEYWORD),
            Parameter("b", Parameter.POSITIONAL_OR_KEYWORD),
        ]
    )

    class Test:
        def baz(self, x, y):
            pass

        @misc.delegates(baz)
        def quux(self, **kwargs):
            self.foo(**kwargs)

    s = signature(Test.quux)
    assert s == Signature(
        parameters=[
            Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),
            Parameter("x", Parameter.POSITIONAL_OR_KEYWORD),
            Parameter("y", Parameter.POSITIONAL_OR_KEYWORD),
        ]
    )


@pytest.mark.asyncio
async def test_run_async():
    def foo(bar, spam):
        return bar, spam

    result = misc.run_async(foo)
    assert await result("bar", spam="spam") == ("bar", "spam")


# TODO: Validate if we can actually read from stdin here
@pytest.mark.asyncio
async def test_get_aio_reader(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.return_value = b"Hello!"

        loop = asyncio.get_running_loop()

        with capsys.disabled():
            reader = await misc.get_aio_reader(loop)
            assert isinstance(reader, asyncio.StreamReader)
