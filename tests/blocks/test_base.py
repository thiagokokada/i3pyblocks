import asyncio
import signal

import pytest

from i3pyblocks import blocks, types

from helpers import task

DEFAULT_STATE = dict(
    separator=None,
    urgent=None,
    align=None,
    markup=None,
)


def test_invalid_block():
    class InvalidBlock(blocks.Block):
        pass

    with pytest.raises(TypeError):
        InvalidBlock()


@pytest.mark.asyncio
async def test_valid_block():
    class ValidBlock(blocks.Block):
        async def start(self):
            await super().start()
            self.update(
                "Done!",
                color=None,
                urgent=False,
                markup=types.MarkupText.NONE,
            )

    block = ValidBlock(
        block_name="Name",
        default_state=dict(
            color="#000000",
            background="#FFFFFF",
            border="#FF0000",
            border_top=1,
            border_right=1,
            border_bottom=1,
            border_left=1,
            min_width=10,
            align=types.AlignText.CENTER,
            urgent=True,
            separator=False,
            separator_block_width=9,
            markup=types.MarkupText.PANGO,
        ),
    )

    block.setup(asyncio.Queue())

    assert block.result() == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "",
        "instance": str(block.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": True,
        "markup": "pango",
    }

    await block.start()

    assert block.result() == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "Done!",
        "instance": str(block.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    id_, result = await block.update_queue.get()

    assert id_ == block.id
    assert result == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "Done!",
        "instance": str(block.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    block.abort("Aborted!")

    _, result = await block.update_queue.get()

    assert result == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "Aborted!",
        "instance": str(block.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": True,
        "markup": "pango",
    }

    block.update("Shouldn't update since aborted")

    with pytest.raises(asyncio.QueueEmpty):
        await block.update_queue.get_nowait()


def test_invalid_polling_block():
    class InvalidPollingBlock(blocks.PollingBlock):
        pass

    with pytest.raises(TypeError):
        InvalidPollingBlock()


@pytest.mark.asyncio
async def test_valid_polling_block():
    class ValidPollingBlock(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        async def run(self):
            self.count += 1
            self.update(str(self.count))

    block = ValidPollingBlock()

    await task.runner([block.start()], timeout=0.5)

    assert block.result() == {
        "full_text": "5",
        "instance": str(block.id),
        "name": "ValidPollingBlock",
    }

    await block.click_handler(
        x=1,
        y=1,
        button=types.MouseButton.LEFT_BUTTON,
        relative_x=1,
        relative_y=1,
        width=1,
        height=1,
        modifiers=[],
    )

    assert block.result() == {
        "full_text": "6",
        "instance": str(block.id),
        "name": "ValidPollingBlock",
    }

    await block.signal_handler(sig=signal.SIGHUP)

    assert block.result() == {
        "full_text": "7",
        "instance": str(block.id),
        "name": "ValidPollingBlock",
    }


@pytest.mark.asyncio
async def test_polling_block_with_error():
    class PollingBlockWithError(blocks.PollingBlock):
        def __init__(self, sleep=1):
            self.count = 0
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        def run(self):
            raise Exception("Boom!")

    block = PollingBlockWithError()

    with pytest.raises(Exception):
        await block.start()

    assert block.result() == {
        "full_text": "Exception in PollingBlockWithError: Boom!",
        "instance": str(block.id),
        "name": "PollingBlockWithError",
        "urgent": True,
    }


def test_invalid_executor_block():
    class InvalidExecutorBlock(blocks.ExecutorBlock):
        pass

    with pytest.raises(TypeError):
        InvalidExecutorBlock()


@pytest.mark.asyncio
async def test_valid_executor_block():
    class ValidExecutorBlock(blocks.ExecutorBlock):
        def __init__(self):
            self.count = 0
            super().__init__(default_state=DEFAULT_STATE)

        def run(self):
            self.count += 1
            self.update(str(self.count))

    block = ValidExecutorBlock()

    await task.runner([block.start()])

    assert block.result() == {
        "full_text": "1",
        "instance": str(block.id),
        "name": "ValidExecutorBlock",
    }


@pytest.mark.asyncio
async def test_executor_block_with_error():
    class ExecutorBlockWithError(blocks.ExecutorBlock):
        def __init__(self):
            self.count = 0
            super().__init__(default_state=DEFAULT_STATE)

        def run(self):
            raise Exception("Boom!")

    block = ExecutorBlockWithError()

    await task.runner([block.start()])

    assert block.result() == {
        "full_text": "Exception in ExecutorBlockWithError: Boom!",
        "instance": str(block.id),
        "name": "ExecutorBlockWithError",
        "urgent": True,
    }
