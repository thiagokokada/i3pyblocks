import pytest
from asynctest import CoroutineMock
from unittest.mock import call, patch

from i3pyblocks import types
from i3pyblocks.modules import subprocess as m_sub

from helpers import misc


@pytest.mark.asyncio
async def test_shell_module():
    # This test is not mocked, since basic Linux tools should be available
    # in any place that have an i3 setup
    instance = m_sub.ShellModule(
        command="""
        echo Hello World | cut -d" " -f1
        echo Someone 1>&2
        exit 1
        """,
        format="{output} {output_err}",
        color_by_returncode=((1, types.Color.URGENT),),
    )
    await instance.run()

    result = instance.result()

    assert result["full_text"] == "Hello Someone"
    assert result["color"] == types.Color.URGENT


@pytest.mark.asyncio
async def test_shell_module_click_handler():
    instance = m_sub.ShellModule(
        command="exit 0",
        command_on_click=(
            (types.Mouse.LEFT_BUTTON, "LEFT_BUTTON"),
            (types.Mouse.MIDDLE_BUTTON, "MIDDLE_BUTTON"),
            (types.Mouse.RIGHT_BUTTON, "RIGHT_BUTTON"),
            (types.Mouse.SCROLL_UP, "SCROLL_UP"),
            (types.Mouse.SCROLL_DOWN, "SCROLL_DOWN"),
        ),
    )

    for button in [
        "LEFT_BUTTON",
        "RIGHT_BUTTON",
        "MIDDLE_BUTTON",
        "SCROLL_UP",
        "SCROLL_DOWN",
    ]:
        with patch("i3pyblocks.utils.shell_run", new=CoroutineMock()) as shell_mock:
            shell_mock.return_value = (
                b"stdout\n",
                b"stderr\n",
                misc.AttributeDict(returncode=0),
            )
            await instance.click_handler(getattr(types.Mouse, button))
            shell_mock.assert_has_calls([call(button)])


@pytest.mark.asyncio
async def test_toggle_module():
    instance = m_sub.ToggleModule(
        command_state="echo", command_on="state on", command_off="state off"
    )

    await instance.run()

    result = instance.result()
    assert result["full_text"] == "OFF"  # OFF since it is an empty echo

    with patch("i3pyblocks.utils.shell_run", new=CoroutineMock()) as shell_mock:
        shell_mock.return_value = (
            b"stdout\n",
            b"\n",
            misc.AttributeDict(returncode=0),
        )
        await instance.click_handler()
        result = instance.result()
        assert result["full_text"] == "ON"

    with patch("i3pyblocks.utils.shell_run", new=CoroutineMock()) as shell_mock:
        shell_mock.return_value = (
            b"\n",
            b"\n",
            misc.AttributeDict(returncode=0),
        )
        await instance.click_handler()
        result = instance.result()
        assert result["full_text"] == "OFF"
