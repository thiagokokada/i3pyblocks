import asyncio
import signal

import pytest

from i3pyblocks import modules


def test_invalid_module():
    class InvalidModule(modules.Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module(mock_uuid4):
    class ValidModule(modules.Module):
        async def start(self):
            await super().start()
            self.update("Done!", color=None, urgent=False, markup=modules.Markup.NONE)

    module = ValidModule(
        name="Name",
        color="#000000",
        background="#FFFFFF",
        border="#FF0000",
        border_top=1,
        border_right=1,
        border_bottom=1,
        border_left=1,
        min_width=10,
        align=modules.Align.CENTER,
        urgent=True,
        separator=False,
        separator_block_width=9,
        markup=modules.Markup.PANGO,
    )

    assert module.result() == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "",
        "instance": str(mock_uuid4),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": True,
        "markup": "pango",
    }

    await module.start()

    assert module.result() == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "Done!",
        "instance": str(mock_uuid4),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    id_, result = await module.update_queue.get()

    assert id_ == mock_uuid4
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
        "instance": str(mock_uuid4),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    with pytest.raises(NotImplementedError):
        await module.click_handler(
            x=1,
            y=1,
            button=1,
            relative_x=1,
            relative_y=1,
            width=1,
            height=1,
            modifiers=[],
        )

    with pytest.raises(NotImplementedError):
        await module.signal_handler(sig=signal.SIGHUP)


def test_invalid_polling_module():
    class InvalidPollingModule(modules.PollingModule):
        pass

    with pytest.raises(TypeError):
        InvalidPollingModule()


@pytest.mark.asyncio
async def test_valid_polling_module(mock_uuid4):
    class ValidPollingModule(modules.PollingModule):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            self.count += 1
            self.update(str(self.count))

    module = ValidPollingModule()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task], timeout=0.5)

    task.cancel()

    assert module.result() == {
        "full_text": "5",
        "instance": str(mock_uuid4),
        "name": "ValidPollingModule",
    }

    await module.click_handler(
        x=1, y=1, button=1, relative_x=1, relative_y=1, width=1, height=1, modifiers=[],
    )

    assert module.result() == {
        "full_text": "6",
        "instance": str(mock_uuid4),
        "name": "ValidPollingModule",
    }

    await module.signal_handler(sig=signal.SIGHUP)

    assert module.result() == {
        "full_text": "7",
        "instance": str(mock_uuid4),
        "name": "ValidPollingModule",
    }


@pytest.mark.asyncio
async def test_polling_module_with_error(mock_uuid4):
    class PollingModuleWithError(modules.PollingModule):
        def __init__(self, sleep=1):
            self.count = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        def run(self):
            raise Exception("Boom!")

    module = PollingModuleWithError()

    await module.start()

    assert module.result() == {
        "full_text": "Exception in PollingModuleWithError: Boom!",
        "instance": str(mock_uuid4),
        "name": "PollingModuleWithError",
        "urgent": True,
    }


def test_invalid_executor_module():
    class InvalidExecutorModule(modules.ExecutorModule):
        pass

    with pytest.raises(TypeError):
        InvalidExecutorModule()


@pytest.mark.asyncio
async def test_valid_executor_module(mock_uuid4):
    class ValidExecutorModule(modules.ExecutorModule):
        def __init__(self):
            self.count = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            self.count += 1
            self.update(str(self.count))

    module = ValidExecutorModule()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task])

    task.cancel()

    assert module.result() == {
        "full_text": "1",
        "instance": str(mock_uuid4),
        "name": "ValidExecutorModule",
    }


@pytest.mark.asyncio
async def test_executor_module_with_error(mock_uuid4):
    class ExecutorModuleWithError(modules.ExecutorModule):
        def __init__(self):
            self.count = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            raise Exception("Boom!")

    module = ExecutorModuleWithError()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task])

    task.cancel()

    assert module.result() == {
        "full_text": "Exception in ExecutorModuleWithError: Boom!",
        "instance": str(mock_uuid4),
        "name": "ExecutorModuleWithError",
        "urgent": True,
    }
