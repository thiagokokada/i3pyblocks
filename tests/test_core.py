import asyncio
import os
import signal
import time

import pytest

from i3pyblocks.core import Runner
from i3pyblocks.modules import PollingModule, ThreadingModule


@pytest.mark.asyncio
async def test_runner(capsys, mock_stdin, mock_uuid4):
    class ValidPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.state = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

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
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

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
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

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
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

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


@pytest.mark.asyncio
async def test_runner_with_notify_update(capsys, mock_stdin, mock_uuid4):
    class ValidThreadingModule(ThreadingModule):
        def __init__(self):
            self.state = 0
            super().__init__(separator=None, urgent=None, align=None, markup=None)

        def run(self):
            for _ in range(5):
                self.state += 1
                self.update(str(self.state))
                Runner.notify_update(self)
                time.sleep(0.1)

    runner = Runner(sleep=100)
    runner.register_module(ValidThreadingModule())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    # TODO: Understand why this is happening.
    assert (
        captured.out
        == """\
{"version": 1, "click_events": true}
[
[{"name": "ValidThreadingModule", "instance": "uuid4", "full_text": "1"}],
[{"name": "ValidThreadingModule", "instance": "uuid4", "full_text": "1"}],
[{"name": "ValidThreadingModule", "instance": "uuid4", "full_text": "5"}],
"""
    )
