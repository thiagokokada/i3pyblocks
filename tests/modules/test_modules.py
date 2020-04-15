import asyncio

import pytest

from i3pyblocks.modules import Align, Markup, Module, PollingModule, ThreadingModule


def test_invalid_module():
    class InvalidModule(Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module(mock_uuid4):
    class ValidModule(Module):
        async def start(self):
            self.update("Done!", color=None, urgent=False, markup=Markup.NONE)

        def click_handler(self, *_, **__):
            pass

        def signal_handler(self, *_, **__):
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
        "instance": "uuid4",
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
        "instance": "uuid4",
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
            self.state = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        def run(self):
            self.state += 1
            self.update(str(self.state))

    module = ValidPollingModule()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task], timeout=0.5)

    task.cancel()

    assert module.result() == {
        "full_text": "5",
        "instance": "uuid4",
        "name": "ValidPollingModule",
    }


@pytest.mark.asyncio
async def test_polling_module_with_error(mock_uuid4):
    class PollingModuleWithError(PollingModule):
        def __init__(self, sleep=1):
            self.state = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        def run(self):
            raise Exception("Boom!")

    module = PollingModuleWithError()

    await module.start()

    assert module.result() == {
        "full_text": "Exception in PollingModuleWithError: Boom!",
        "instance": "uuid4",
        "name": "PollingModuleWithError",
        "urgent": True,
    }


@pytest.mark.asyncio
async def test_valid_thread_pool_module(mock_uuid4):
    class ValidThreadingModule(ThreadingModule):
        def __init__(self):
            self.state = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            self.state += 1
            self.update(str(self.state))

    module = ValidThreadingModule()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task])

    assert module.result() == {
        "full_text": "1",
        "instance": "uuid4",
        "name": "ValidThreadingModule",
    }


@pytest.mark.asyncio
async def test_thread_pool_module_with_error(mock_uuid4):
    class ThreadingModuleWithError(ThreadingModule):
        def __init__(self):
            self.state = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            raise Exception("Boom!")

    module = ThreadingModuleWithError()

    task = asyncio.create_task(module.start())

    await asyncio.wait([task])

    assert module.result() == {
        "full_text": "Exception in ThreadingModuleWithError: Boom!",
        "instance": "uuid4",
        "name": "ThreadingModuleWithError",
        "urgent": True,
    }
