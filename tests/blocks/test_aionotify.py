import asyncio

import pytest
from asynctest import Mock
from helpers import misc, task

from i3pyblocks import types
from i3pyblocks._internal import utils

aionotify = pytest.importorskip("aionotify")
m_aionotify = pytest.importorskip("i3pyblocks.blocks.aionotify")


@pytest.mark.asyncio
async def test_file_watcher_block(tmpdir):
    tmpfile = tmpdir / "tmpfile.txt"

    def update_file(text):
        with open(tmpfile, "w") as f:
            f.write(text)

    async def update_file_async(text):
        await asyncio.sleep(0.1)
        update_file(text)

    class ValidFileWatcherBlock(m_aionotify.FileWatcherBlock):
        def __init__(self):
            super().__init__(path=tmpfile, flags=aionotify.Flags.MODIFY)

        async def run(self):
            with open(self.path) as f:
                contents = f.readline().strip()
                self.update(contents)

    block = ValidFileWatcherBlock()

    update_file("Run!")
    await block.run()
    assert block.result()["full_text"] == "Run!"

    update_file("Click!")
    await block.click_handler()
    assert block.result()["full_text"] == "Click!"

    update_file("Signal!")
    await block.signal_handler()
    assert block.result()["full_text"] == "Signal!"

    await task.runner(
        [
            block.start(),
            update_file_async("Async!"),
        ],
        timeout=0.2,
    )

    assert block.result()["full_text"] == "Async!"


@pytest.mark.asyncio
async def test_file_watcher_block_with_non_existing_path():
    class EmptyFileWatcherBlock(m_aionotify.FileWatcherBlock):
        def __init__(self):
            super().__init__(path="/non/existing/path")

        async def run(self):
            pass

    block = EmptyFileWatcherBlock()

    await task.runner([block.start()])

    assert block.frozen
    result = block.result()
    assert result["full_text"] == "File not found /non/existing/path"


@pytest.mark.asyncio
async def test_backlight_block(tmpdir):
    brightness_tmpfile = tmpdir / "brightness"
    with open(brightness_tmpfile, "w") as f:
        f.write("450")

    max_brightness_tmpfile = tmpdir / "max_brightness"
    with open(max_brightness_tmpfile, "w") as f:
        f.write("1500")

    async def update_file():
        await asyncio.sleep(0.1)
        with open(brightness_tmpfile, "w") as f:
            f.write("550")

    block = m_aionotify.BacklightBlock(
        format="{percent:.1f} {brightness} {max_brightness}",
        base_path=tmpdir,
        device_glob=None,
    )

    await block.run()
    result = block.result()
    assert result["full_text"] == "30.0 450 1500"

    await task.runner([block.start(), update_file()], timeout=0.2)

    result = block.result()
    assert result["full_text"] == "36.7 550 1500"


@pytest.mark.asyncio
async def test_backlight_block_with_device_glob(tmpdir):
    device_path = tmpdir.mkdir("test_device")

    brightness_tmpfile = device_path / "brightness"
    with open(brightness_tmpfile, "w") as f:
        f.write("350")

    max_brightness_tmpfile = device_path / "max_brightness"
    with open(max_brightness_tmpfile, "w") as f:
        f.write("2500")

    block = m_aionotify.BacklightBlock(
        format="{percent:.1f} {brightness} {max_brightness}",
        base_path=str(tmpdir),
        device_glob="test_*",
    )

    await block.run()
    result = block.result()
    assert result["full_text"] == "14.0 350 2500"

    await task.runner([block.start()], timeout=0.2)


@pytest.mark.asyncio
async def test_backlight_block_without_backlight(tmpdir):
    block = m_aionotify.BacklightBlock(
        format="{percent:.1f} {brightness} {max_brightness}",
        base_path=tmpdir,
        device_path="file_not_existing",
    )

    await task.runner([block.start()])

    assert block.frozen
    result = block.result()
    assert result["full_text"] == "No backlight"


@pytest.mark.asyncio
async def test_backlight_block_click_handler(tmpdir):
    mock_utils = Mock(utils)

    instance = m_aionotify.BacklightBlock(
        base_path=tmpdir,
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
