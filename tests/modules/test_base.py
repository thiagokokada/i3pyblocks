import asyncio
import signal

import pytest

from i3pyblocks import modules, types

from helpers import task


def test_invalid_module():
    class InvalidModule(modules.Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module():
    class ValidModule(modules.Module):
        async def start(self):
            await super().start()
            self.update("Done!", color=None, urgent=False, markup=types.Markup.NONE)

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
        align=types.Align.CENTER,
        urgent=True,
        separator=False,
        separator_block_width=9,
        markup=types.Markup.PANGO,
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
        "instance": str(module.id),
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
        "instance": str(module.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    id_, result = await module.update_queue.get()

    assert id_ == module.id
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
        "instance": str(module.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    module.abort("Aborted!")

    _, result = await module.update_queue.get()

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
        "instance": str(module.id),
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": True,
        "markup": "pango",
    }

    module.update("Shouldn't update since aborted")

    with pytest.raises(asyncio.QueueEmpty):
        await module.update_queue.get_nowait()


def test_invalid_polling_module():
    class InvalidPollingModule(modules.PollingModule):
        pass

    with pytest.raises(TypeError):
        InvalidPollingModule()


@pytest.mark.asyncio
async def test_valid_polling_module():
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

    await task.runner([module.start()], timeout=0.5)

    assert module.result() == {
        "full_text": "5",
        "instance": str(module.id),
        "name": "ValidPollingModule",
    }

    await module.click_handler(
        x=1, y=1, button=1, relative_x=1, relative_y=1, width=1, height=1, modifiers=[],
    )

    assert module.result() == {
        "full_text": "6",
        "instance": str(module.id),
        "name": "ValidPollingModule",
    }

    await module.signal_handler(sig=signal.SIGHUP)

    assert module.result() == {
        "full_text": "7",
        "instance": str(module.id),
        "name": "ValidPollingModule",
    }


@pytest.mark.asyncio
async def test_polling_module_with_error():
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
        "instance": str(module.id),
        "name": "PollingModuleWithError",
        "urgent": True,
    }


def test_invalid_executor_module():
    class InvalidExecutorModule(modules.ExecutorModule):
        pass

    with pytest.raises(TypeError):
        InvalidExecutorModule()


@pytest.mark.asyncio
async def test_valid_executor_module():
    class ValidExecutorModule(modules.ExecutorModule):
        def __init__(self):
            self.count = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            self.count += 1
            self.update(str(self.count))

    module = ValidExecutorModule()

    await task.runner([module.start()])

    assert module.result() == {
        "full_text": "1",
        "instance": str(module.id),
        "name": "ValidExecutorModule",
    }


@pytest.mark.asyncio
async def test_executor_module_with_error():
    class ExecutorModuleWithError(modules.ExecutorModule):
        def __init__(self):
            self.count = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            raise Exception("Boom!")

    module = ExecutorModuleWithError()

    await task.runner([module.start()])

    assert module.result() == {
        "full_text": "Exception in ExecutorModuleWithError: Boom!",
        "instance": str(module.id),
        "name": "ExecutorModuleWithError",
        "urgent": True,
    }
