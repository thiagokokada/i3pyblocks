import asyncio
import os
import signal
import sys

import pytest

from i3pyblocks.core import Align, Markup, Module, PollingModule, Runner


def test_module():
    assert Module.get_key("abc", "def") == "abc__def"


def test_invalid_module():
    class InvalidModule(Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module():
    class ValidModule(Module):
        async def loop(self):
            self.update("Done!", color=None, urgent=False, markup=Markup.NONE)

        def click_handler(self, *_, **__):
            pass

        def signal_handler(self, *_, **__):
            pass

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
        "instance": "Instance",
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": True,
        "markup": "pango",
    }

    await module.loop()

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
        "instance": "Instance",
        "min_width": 10,
        "name": "Name",
        "separator": False,
        "separator_block_width": 9,
        "urgent": False,
        "markup": "none",
    }

    assert module.key() == "Name__Instance"


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
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            self.state += 1
            self.update(str(self.state))

    module = ValidPollingModule()

    task = asyncio.ensure_future(module.loop())

    await asyncio.wait([task], timeout=0.5)

    task.cancel()

    assert module.result() == {
        "full_text": "5",
        "instance": "default",
        "name": "ValidPollingModule",
    }


@pytest.mark.asyncio
async def test_polling_module_with_error():
    class PollingModuleWithError(PollingModule):
        def __init__(self, sleep=1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            raise Exception("Boom!")

    module = PollingModuleWithError()

    await module.loop()

    assert module.result() == {
        "full_text": "Exception in PollingModuleWithError: Boom!",
        "instance": "default",
        "name": "PollingModuleWithError",
        "urgent": True,
    }


@pytest.mark.asyncio
async def test_runner(capsys, mocker):
    mocker.patch.object(sys, "stdin")

    class ValidPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            self.state += 1
            self.update(str(self.state))

    runner = Runner(sleep=0.1)
    runner.register_module(ValidPollingModule())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert (
        captured.out
        == """\
{"version": 1, "click_events": true}
[
[{"name": "ValidPollingModule", "instance": "default", "full_text": "1"}],
[{"name": "ValidPollingModule", "instance": "default", "full_text": "2"}],
[{"name": "ValidPollingModule", "instance": "default", "full_text": "3"}],
[{"name": "ValidPollingModule", "instance": "default", "full_text": "4"}],
[{"name": "ValidPollingModule", "instance": "default", "full_text": "5"}],
"""
    )


def test_runner_with_two_equal_modules():
    class ValidPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            self.state += 1
            self.update(str(self.state))

    runner = Runner(sleep=0.1)
    runner.register_module(ValidPollingModule())
    with pytest.raises(ValueError):
        runner.register_module(ValidPollingModule())


@pytest.mark.asyncio
async def test_runner_with_signal_handler(capsys, mocker):
    mocker.patch.object(sys, "stdin")

    async def send_signal():
        await asyncio.sleep(0.1)
        os.kill(os.getpid(), signal.SIGUSR1)

    async def send_another_signal():
        await asyncio.sleep(0.2)
        os.kill(os.getpid(), signal.SIGUSR2)

    class ValidPollingModuleWithSignalHandler(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            pass

        def signal_handler(self, signum, frame):
            if signum == signal.SIGUSR1:
                self.update("received_signal")
            elif signum == signal.SIGUSR2:
                self.update("received_another_signal")
            else:
                raise Exception("This shouldn't happen")

    runner = Runner(sleep=0.1)
    runner.register_module(
        ValidPollingModuleWithSignalHandler(), signals=[signal.SIGUSR1, signal.SIGUSR2]
    )

    runner._register_coroutine(send_signal())

    runner._register_coroutine(send_another_signal())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert "received_signal" in captured.out
    assert "received_another_signal" in captured.out


# TODO: Test with mocked sys.stdin instead of calling functions directly
def test_runner_with_click_handler():
    click_event = b'{"name":"ValidPollingModuleWithClickHandler","instance":"default","button":1,"modifiers":["Mod1"],"x":123,"y":456,"relative_x":12,"relative_y":34,"width":20,"height":40}'

    class ValidPollingModuleWithClickHandler(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            pass

        def click_handler(
            self, x, y, button, relative_x, relative_y, width, height, modifiers
        ):
            self.update(
                f"{x}-{y}-{button}-{relative_x}-{relative_y}-{width}-{height}-{modifiers}"
            )

    runner = Runner(sleep=0.1)
    module = ValidPollingModuleWithClickHandler()
    runner.register_module(module)
    runner.click_event(click_event)

    result = module.result()

    assert "123-456-1-12-34-20-40-['Mod1']" == result["full_text"]
