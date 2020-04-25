import asyncio

import aionotify
import pytest
from asynctest import CoroutineMock
from unittest.mock import call, patch

from i3pyblocks import types
from i3pyblocks.modules import aionotify as m_aionotify

from helpers import misc


@pytest.mark.asyncio
async def test_file_watcher_module(tmpdir):
    tmpfile = str(tmpdir / "tmpfile.txt")
    with open(tmpfile, "w"):
        pass

    async def update_file():
        await asyncio.sleep(0.1)
        with open(tmpfile, "w") as f:
            f.write("Hello World!")

    class ValidFileWatcherModule(m_aionotify.FileWatcherModule):
        def __init__(self):
            super().__init__(path=tmpfile, flags=aionotify.Flags.MODIFY)

        async def run(self):
            with open(self.path) as f:
                contents = f.readline().strip()
                self.update(contents)

    module = ValidFileWatcherModule()
    module_task = asyncio.create_task(module.start())
    update_file_task = asyncio.create_task(update_file())

    await asyncio.wait([module_task, update_file_task], timeout=0.5)

    module_task.cancel()
    update_file_task.cancel()

    result = module.result()
    assert result["full_text"] == "Hello World!"


@pytest.mark.asyncio
async def test_backlight_module(tmpdir):
    brightness_tmpfile = str(tmpdir / "brightness")
    with open(brightness_tmpfile, "w") as f:
        f.write("450")

    max_brightness_tmpfile = str(tmpdir / "max_brightness")
    with open(max_brightness_tmpfile, "w") as f:
        f.write("1500")

    async def update_file():
        await asyncio.sleep(0.1)
        with open(brightness_tmpfile, "w") as f:
            f.write("550")

    module = m_aionotify.BacklightModule(
        format="{percent:.1f} {brightness} {max_brightness}", path=str(tmpdir)
    )

    await module.run()
    result = module.result()
    assert result["full_text"] == "30.0 450 1500"

    module_task = asyncio.create_task(module.start())
    update_file_task = asyncio.create_task(update_file())

    await asyncio.wait([module_task, update_file_task], timeout=0.5)

    module_task.cancel()
    update_file_task.cancel()

    result = module.result()
    assert result["full_text"] == "36.7 550 1500"


@pytest.mark.asyncio
async def test_backlight_module_click_handler():
    instance = m_aionotify.BacklightModule(
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
