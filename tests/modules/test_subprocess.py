import asyncio
from asyncio import subprocess

import pytest
from unittest.mock import call, patch
from asynctest import CoroutineMock

from i3pyblocks import types
from i3pyblocks.modules import subprocess as m_sub


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
            (types.Mouse.LEFT_BUTTON, "left-button"),
            (types.Mouse.MIDDLE_BUTTON, "middle-button"),
            (types.Mouse.RIGHT_BUTTON, "right-button"),
            (types.Mouse.SCROLL_UP, "scroll-up"),
            (types.Mouse.SCROLL_DOWN, "scroll-down"),
        ),
    )

    communicate_result = asyncio.Future()
    communicate_result.set_result((b"stdout\n", b"stderr\n"))

    with patch("asyncio.create_subprocess_shell", new=CoroutineMock()) as shell_mock:
        process_mock = shell_mock.return_value
        process_mock.communicate.return_value = communicate_result
        await instance.click_handler(types.Mouse.LEFT_BUTTON)
        shell_mock.assert_has_calls(
            [
                call(
                    "left-button",
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ]
        )

    with patch("asyncio.create_subprocess_shell", new=CoroutineMock()) as shell_mock:
        process_mock = shell_mock.return_value
        process_mock.communicate.return_value = communicate_result
        await instance.click_handler(types.Mouse.MIDDLE_BUTTON)
        shell_mock.assert_has_calls(
            [
                call(
                    "middle-button",
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ]
        )

    with patch("asyncio.create_subprocess_shell", new=CoroutineMock()) as shell_mock:
        process_mock = shell_mock.return_value
        process_mock.communicate.return_value = communicate_result
        await instance.click_handler(types.Mouse.RIGHT_BUTTON)
        shell_mock.assert_has_calls(
            [
                call(
                    "right-button",
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ]
        )

    with patch("asyncio.create_subprocess_shell", new=CoroutineMock()) as shell_mock:
        process_mock = shell_mock.return_value
        process_mock.communicate.return_value = communicate_result
        await instance.click_handler(types.Mouse.SCROLL_UP)
        shell_mock.assert_has_calls(
            [
                call(
                    "scroll-up",
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ]
        )

    with patch("asyncio.create_subprocess_shell", new=CoroutineMock()) as shell_mock:
        process_mock = shell_mock.return_value
        process_mock.communicate.return_value = communicate_result
        await instance.click_handler(types.Mouse.SCROLL_DOWN)
        shell_mock.assert_has_calls(
            [
                call(
                    "scroll-down",
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            ]
        )
