import asyncio

import pytest

from i3pyblocks.modules import Align, Markup, Module, PollingModule, ThreadingModule
from i3pyblocks import modules


def test_invalid_module():
    class InvalidModule(Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module(mock_uuid4):
    class ValidModule(modules.Module):
        async def start(self):
            await super().start()
            self.update("Done!", color=None, urgent=False, markup=Markup.NONE)

        async def click_handler(self, *_, **__):
            pass

        async def signal_handler(self, *_, **__):
            pass

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
        align=Align.CENTER,
        urgent=True,
        separator=False,
        separator_block_width=9,
        markup=Markup.PANGO,
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


def test_invalid_polling_module():
    class InvalidPollingModule(PollingModule):
        pass

    with pytest.raises(TypeError):
        InvalidPollingModule()


@pytest.mark.asyncio
async def test_valid_polling_module(mock_uuid4):
    class ValidPollingModule(PollingModule):
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


@pytest.mark.asyncio
async def test_polling_module_with_error(mock_uuid4):
    class PollingModuleWithError(PollingModule):
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


@pytest.mark.asyncio
async def test_valid_thread_pool_module(mock_uuid4):
    class ValidThreadingModule(ThreadingModule):
        def __init__(self):
            self.count = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            self.count += 1
            self.update(str(self.count))

    module = ValidThreadingModule()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task])

    task.cancel()

    assert module.result() == {
        "full_text": "1",
        "instance": str(mock_uuid4),
        "name": "ValidThreadingModule",
    }


@pytest.mark.asyncio
async def test_thread_pool_module_with_error(mock_uuid4):
    class ThreadingModuleWithError(ThreadingModule):
        def __init__(self):
            self.count = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            raise Exception("Boom!")

    module = ThreadingModuleWithError()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task])

    task.cancel()

    assert module.result() == {
        "full_text": "Exception in ThreadingModuleWithError: Boom!",
        "instance": str(mock_uuid4),
        "name": "ThreadingModuleWithError",
        "urgent": True,
    }
