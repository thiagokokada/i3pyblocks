from asyncio import subprocess

import pytest
from helpers import misc
from mock import call, patch

from i3pyblocks import types
from i3pyblocks.blocks import shell


@pytest.mark.asyncio
async def test_shell_block():
    # This test is not mocked, since basic Linux tools should be available
    # in any place that have an i3 setup
    instance = shell.ShellBlock(
        command="""
        echo Hello World | cut -d" " -f1
        echo Someone 1>&2
        exit 1
        """,
        format="{output} {output_err}",
        color_by_returncode={1: types.Color.URGENT},
    )
    await instance.run()

    result = instance.result()

    assert result["full_text"] == "Hello Someone"
    assert result["color"] == types.Color.URGENT


@pytest.mark.asyncio
async def test_shell_block_click_handler():
    with patch(
        "i3pyblocks.blocks.shell.subprocess", autospec=True, spec_set=True
    ) as mock_subprocess:
        mock_subprocess.configure_mock(
            **{
                "arun.return_value": (
                    misc.AttributeDict(
                        stdout="stdout\n",
                        stderr="stderr\n",
                        returncode=0,
                    )
                ),
                "PIPE": subprocess.PIPE,
            }
        )
        instance = shell.ShellBlock(
            command="exit 0",
            command_on_click={
                types.MouseButton.LEFT_BUTTON: "LEFT_BUTTON",
                types.MouseButton.MIDDLE_BUTTON: "MIDDLE_BUTTON",
                types.MouseButton.RIGHT_BUTTON: "RIGHT_BUTTON",
                types.MouseButton.SCROLL_UP: "SCROLL_UP",
                types.MouseButton.SCROLL_DOWN: "SCROLL_DOWN",
            },
        )

        for button in [
            "LEFT_BUTTON",
            "RIGHT_BUTTON",
            "MIDDLE_BUTTON",
            "SCROLL_UP",
            "SCROLL_DOWN",
        ]:
            await instance.click_handler(getattr(types.MouseButton, button))
            mock_subprocess.arun.assert_has_calls(
                [
                    call(button),
                    call(
                        "exit 0",
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    ),
                ]
            )
            mock_subprocess.arun.reset_mock()


@pytest.mark.asyncio
async def test_toggle_block(tmpdir):
    file_on = tmpdir / "on"
    file_off = tmpdir / "off"

    # This test is not mocked, since basic Linux tools should be available
    # in any place that have an i3 setup
    instance = shell.ToggleBlock(
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
