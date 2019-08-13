import asyncio

import pytest

from i3pyblocks.core import *


def test_invalid_module():
    class InvalidModule(Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module():
    class ValidModule(Module):
        async def loop(self):
            self.urgent = False
            self.color = None
            self.full_text = "Done!"

    module = ValidModule(
        name="Name",
        instance="Instance",
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

    assert module.format() == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "color": "#000000",
        "full_text": "",
        "instance": "Instance",
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": True,
    }

    await module.loop()

    assert module.format() == {
        "align": "center",
        "background": "#FFFFFF",
        "border": "#FF0000",
        "border_bottom": 1,
        "border_left": 1,
        "border_right": 1,
        "border_top": 1,
        "full_text": "Done!",
        "instance": "Instance",
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
    }

    with pytest.raises(NotImplementedError):
        module.signal_handler(0, None)


def test_invalid_polling_module():
    class InvalidPollingModule(PollingModule):
        pass

    with pytest.raises(TypeError):
        InvalidPollingModule()


@pytest.mark.asyncio
async def test_valid_polling_module():
    class ValidPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None)

        def run(self):
            self.state += 1
            self.full_text = str(self.state)

    module = ValidPollingModule()

    task = asyncio.create_task(module.loop())

    await asyncio.wait([task], timeout=1)

    task.cancel()

    assert module.format() == {"name": "ValidPollingModule", "full_text": "10"}


@pytest.mark.asyncio
async def test_polling_module_with_error():
    class PollingModuleWithError(PollingModule):
        def __init__(self, sleep=1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None)

        def run(self):
            raise Exception("Boom!")

    module = PollingModuleWithError()

    await module.loop()

    assert module.format() == {
        "full_text": "Exception in PollingModuleWithError: Boom!",
        "name": "PollingModuleWithError",
        "urgent": True,
    }


@pytest.mark.asyncio
async def test_runner(capsys):
    class ValidPollingModule(PollingModule):
        def __init__(self, sleep=1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None)

        def run(self):
            self.state += 1
            self.full_text = str(self.state)

    runner = Runner()
    runner.register_module(ValidPollingModule())

    await runner.start(timeout=5)

    captured = capsys.readouterr()

    assert (
        captured.out
        == """\
{"version": 1}
[
[{"name": "ValidPollingModule", "full_text": ""}],
[{"name": "ValidPollingModule", "full_text": "1"}],
[{"name": "ValidPollingModule", "full_text": "2"}],
[{"name": "ValidPollingModule", "full_text": "3"}],
[{"name": "ValidPollingModule", "full_text": "4"}],
"""
    )
