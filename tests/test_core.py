import asyncio
import os
import signal

import pytest

from i3pyblocks.core import (
    Align,
    Markup,
    Module,
    PollingModule,
    ThreadPoolModule,
    Runner,
)


def test_invalid_module():
    class InvalidModule(Module):
        pass

    with pytest.raises(TypeError):
        InvalidModule()


@pytest.mark.asyncio
async def test_valid_module(mock_uuid4):
    class ValidModule(Module):
        async def loop(self):
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
        "instance": "uuid4",
        "name": "ValidPollingModule",
    }


@pytest.mark.asyncio
async def test_polling_module_with_error(mock_uuid4):
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
        "instance": "uuid4",
        "name": "PollingModuleWithError",
        "urgent": True,
    }


@pytest.mark.asyncio
async def test_valid_thread_pool_module(mock_uuid4):
    class ValidThreadPoolModule(ThreadPoolModule):
        def __init__(self, max_workers=1):
            self.state = 0
            super().__init__(
                max_workers=max_workers, separator=None, urgent=None, markup=None
            )

        def run(self):
            self.state += 1
            self.update(str(self.state))

    module = ValidThreadPoolModule()

    task = asyncio.ensure_future(module.loop())

    await asyncio.wait([task])

    assert module.result() == {
        "full_text": "1",
        "instance": "uuid4",
        "name": "ValidThreadPoolModule",
    }


@pytest.mark.asyncio
async def test_thread_pool_module_with_error(mock_uuid4):
    class ThreadPoolModuleWithError(ThreadPoolModule):
        def __init__(self, max_workers=1):
            self.state = 0
            super().__init__(
                max_workers=max_workers, separator=None, urgent=None, markup=None
            )

        def run(self):
            raise Exception("Boom!")

    module = ThreadPoolModuleWithError()

    task = asyncio.ensure_future(module.loop())

    await asyncio.wait([task])

    assert module.result() == {
        "full_text": "Exception in ThreadPoolModuleWithError: Boom!",
        "instance": "uuid4",
        "name": "ThreadPoolModuleWithError",
        "urgent": True,
    }


@pytest.mark.asyncio
async def test_runner(capsys, mock_stdin, mock_uuid4):
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
[{"name": "ValidPollingModule", "instance": "uuid4", "full_text": "1"}],
[{"name": "ValidPollingModule", "instance": "uuid4", "full_text": "2"}],
[{"name": "ValidPollingModule", "instance": "uuid4", "full_text": "3"}],
[{"name": "ValidPollingModule", "instance": "uuid4", "full_text": "4"}],
[{"name": "ValidPollingModule", "instance": "uuid4", "full_text": "5"}],
"""
    )


@pytest.mark.asyncio
async def test_runner_with_fault_module(capsys, mock_stdin, mock_uuid4):
    class FaultPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(sleep=sleep, separator=None, urgent=None, markup=None)

        def run(self):
            self.state += 1
            if self.state > 4:
                raise Exception("Boom!")
            self.update(str(self.state))

    runner = Runner(sleep=0.1)
    runner.register_module(FaultPollingModule())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert (
        captured.out
        == """\
{"version": 1, "click_events": true}
[
[{"name": "FaultPollingModule", "instance": "uuid4", "full_text": "1"}],
[{"name": "FaultPollingModule", "instance": "uuid4", "full_text": "2"}],
[{"name": "FaultPollingModule", "instance": "uuid4", "full_text": "3"}],
[{"name": "FaultPollingModule", "instance": "uuid4", "full_text": "4"}],
[{"name": "FaultPollingModule", "instance": "uuid4", \
"full_text": "Exception in FaultPollingModule: Boom!", "urgent": true}],
"""
    )


@pytest.mark.asyncio
async def test_runner_with_signal_handler(capsys, mock_stdin, mock_uuid4):
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

        def signal_handler(self, signum):
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

    runner.register_task(send_signal())
    runner.register_task(send_another_signal())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert "received_signal" in captured.out
    assert "received_another_signal" in captured.out


# TODO: Test with mocked sys.stdin instead of calling functions directly
@pytest.mark.asyncio
async def test_runner_with_click_handler(capsys, mock_uuid4):
    click_event = (
        b'{"name":"ValidPollingModuleWithClickHandler",'
        + b'"instance":"uuid4",'
        + b'"button":1,'
        + b'"modifiers":["Mod1"],'
        + b'"x":123,'
        + b'"y":456,'
        + b'"relative_x":12,'
        + b'"relative_y":34,'
        + b'"width":20,'
        + b'"height":40}'
    )

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

    captured = capsys.readouterr()

    assert "123-456-1-12-34-20-40-['Mod1']" in captured.out
