import pytest
from asynctest import CoroutineMock
from unittest.mock import call, MagicMock

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
    mock_utils = MagicMock()
    instance = m_sub.ShellModule(
        command="exit 0",
        command_on_click=(
            (types.Mouse.LEFT_BUTTON, "LEFT_BUTTON"),
            (types.Mouse.MIDDLE_BUTTON, "MIDDLE_BUTTON"),
            (types.Mouse.RIGHT_BUTTON, "RIGHT_BUTTON"),
            (types.Mouse.SCROLL_UP, "SCROLL_UP"),
            (types.Mouse.SCROLL_DOWN, "SCROLL_DOWN"),
        ),
        _utils=mock_utils,
    )

    for button in [
        "LEFT_BUTTON",
        "RIGHT_BUTTON",
        "MIDDLE_BUTTON",
        "SCROLL_UP",
        "SCROLL_DOWN",
    ]:

        mock_utils.shell_run = CoroutineMock()
        mock_utils.shell_run.return_value = (
            b"stdout\n",
            b"stderr\n",
            misc.AttributeDict(returncode=0),
        )
        await instance.click_handler(getattr(types.Mouse, button))
        mock_utils.shell_run.assert_has_calls([call(button)])


@pytest.mark.asyncio
async def test_toggle_module(tmpdir):
    instance = m_sub.ToggleModule(
        command_state="echo",
        command_on=f"touch {tmpdir}/on",
        command_off=f"touch {tmpdir}/off",
    )

    await instance.run()

    result = instance.result()
    # OFF since it is an empty echo
    assert result["full_text"] == "OFF"

    await instance.click_handler()
    # Will call command_off since the state == False
    assert (tmpdir / "on").exists()

    instance.command_state = "echo ON"

    await instance.click_handler()
    # Will call command_on since the state == True
    assert (tmpdir / "off").exists()

    result = instance.result()
    # ON since it is an non-empty echo
    assert result["full_text"] == "ON"
