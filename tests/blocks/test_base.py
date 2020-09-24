import asyncio
import signal
import time

import pytest
from helpers import task

from i3pyblocks import blocks, types

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
                self.ex_format("{!u}", "Done!"),
                color=None,
                urgent=False,
                markup=types.MarkupText.NONE,
            )

    default_state = dict(
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
    )

    block = ValidBlock(block_name="Name", default_state=default_state)

    await block.setup(asyncio.Queue())

    assert block.result() == {
        **default_state,
        "instance": str(block.id),
        "full_text": "",
        "name": "Name",
    }

    await block.start()

    assert block.result() == {
        **default_state,
        "instance": str(block.id),
        "full_text": "DONE!",
        "name": "Name",
        "markup": "none",
        "urgent": False,
    }

    id_, result = await block.update_queue.get()

    assert id_ == block.id
    assert result == {
        **default_state,
        "instance": str(block.id),
        "full_text": "DONE!",
        "name": "Name",
        "markup": "none",
        "urgent": False,
    }

    # Testing abort()
    block.abort("Aborted!")

    _, result = await block.update_queue.get()
    assert result == {
        **default_state,
        "instance": str(block.id),
        "full_text": "Aborted!",
        "name": "Name",
        "urgent": True,
    }

    block.update("Shouldn't update since aborted")

    with pytest.raises(asyncio.QueueEmpty):
        await block.update_queue.get_nowait()

    # Testing reset_state()
    block.reset_state()

    assert block.result() == {
        **default_state,
        "instance": str(block.id),
        "name": "Name",
    }

    # Testing exception()
    block.frozen = False

    with pytest.raises(Exception):
        block.exception(
            Exception("Kaboom!"),
            format="{block_name}: {exception}",
            reraise=True,
        )

    result = block.result()

    assert result["full_text"] == "Name: Kaboom!"
    assert result["urgent"] is True
    assert block.frozen


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
    await block.setup()

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
async def test_polling_block_abort():
    class PollingBlockAbort(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            super().__init__(sleep=sleep)

        def run(self):
            pass

    block = PollingBlockAbort()
    await block.setup()
    block.abort("Aborted")

    start_time = time.time()
    await task.runner([block.start()], timeout=10)
    running_time = time.time() - start_time

    assert block.result()["full_text"] == "Aborted"
    # This test shouldn't take too long, or something is wrong
    assert running_time < 0.1


@pytest.mark.asyncio
async def test_polling_block_with_error():
    class PollingBlockWithError(blocks.PollingBlock):
        def __init__(self, sleep=1):
            self.count = 0
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        def run(self):
            raise Exception("Boom!")

    block = PollingBlockWithError()
    await block.setup()

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
