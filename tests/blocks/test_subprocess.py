import pytest
from asynctest import Mock
from helpers import misc

from i3pyblocks import types, utils
from i3pyblocks.blocks import subprocess as m_sub


@pytest.mark.asyncio
async def test_shell_block():
    # This test is not mocked, since basic Linux tools should be available
    # in any place that have an i3 setup
    instance = m_sub.ShellBlock(
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
async def test_shell_block_click_handler():
    mock_utils = Mock(utils)

    instance = m_sub.ShellBlock(
        command="exit 0",
        command_on_click=(
            (types.MouseButton.LEFT_BUTTON, "LEFT_BUTTON"),
            (types.MouseButton.MIDDLE_BUTTON, "MIDDLE_BUTTON"),
            (types.MouseButton.RIGHT_BUTTON, "RIGHT_BUTTON"),
            (types.MouseButton.SCROLL_UP, "SCROLL_UP"),
            (types.MouseButton.SCROLL_DOWN, "SCROLL_DOWN"),
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
        mock_utils.shell_run.return_value = (
            b"stdout\n",
            b"stderr\n",
            misc.AttributeDict(returncode=0),
        )
        await instance.click_handler(getattr(types.MouseButton, button))
        mock_utils.shell_run.assert_called_once_with(button)
        mock_utils.shell_run.reset_mock()


@pytest.mark.asyncio
async def test_toggle_block(tmpdir):
    file_on = tmpdir / "on"
    file_off = tmpdir / "off"

    # This test is not mocked, since basic Linux tools should be available
    # in any place that have an i3 setup
    instance = m_sub.ToggleBlock(
        command_state="echo",
        command_on=f"touch {file_on}",
        command_off=f"touch {file_off}",
    )

    await instance.run()

    result = instance.result()
    # OFF since it is an empty echo
    assert result["full_text"] == "OFF"

    await instance.click_handler()
    # Will call command_on since the state == False
    assert (file_on).exists()

    instance.command_state = "echo ON"

    await instance.click_handler()
    # Will call command_off since the state == True
    assert (file_off).exists()

    result = instance.result()
    # ON since it is an non-empty echo
    assert result["full_text"] == "ON"
