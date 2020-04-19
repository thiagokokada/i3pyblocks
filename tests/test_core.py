import asyncio
import json
import os
import signal

import pytest

from i3pyblocks.core import Runner
from i3pyblocks.modules import PollingModule


@pytest.mark.asyncio
async def test_runner(capsys, mock_stdin, mock_uuid4):
    class ValidPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            self.count += 1
            self.update(str(self.count))

    runner = Runner()
    runner.register_module(ValidPollingModule())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert (
        captured.out
        == f"""\
{{"version": 1, "click_events": true}}
[
[{{"name": "ValidPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "1"}}],
[{{"name": "ValidPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "2"}}],
[{{"name": "ValidPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "3"}}],
[{{"name": "ValidPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "4"}}],
[{{"name": "ValidPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "5"}}],
"""
    )


@pytest.mark.asyncio
async def test_runner_with_fault_module(capsys, mock_stdin, mock_uuid4):
    class FaultPollingModule(PollingModule):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            self.count += 1
            if self.count > 4:
                raise Exception("Boom!")
            self.update(str(self.count))

    runner = Runner()
    runner.register_module(FaultPollingModule())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert (
        captured.out
        == f"""\
{{"version": 1, "click_events": true}}
[
[{{"name": "FaultPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "1"}}],
[{{"name": "FaultPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "2"}}],
[{{"name": "FaultPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "3"}}],
[{{"name": "FaultPollingModule", "instance": "{str(mock_uuid4)}", "full_text": "4"}}],
[{{"name": "FaultPollingModule", "instance": "{str(mock_uuid4)}", \
"full_text": "Exception in FaultPollingModule: Boom!", "urgent": true}}],
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
            self.count = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            pass

        async def signal_handler(self, sig):
            if sig == signal.SIGUSR1:
                self.update("received_signal")
            elif sig == signal.SIGUSR2:
                self.update("received_another_signal")
            else:
                raise Exception("This shouldn't happen")

    runner = Runner()
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
    class ValidPollingModuleWithClickHandler(PollingModule):
        def __init__(self, sleep=0.1):
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            pass

        async def click_handler(
            self, x, y, button, relative_x, relative_y, width, height, modifiers
        ):
            self.update(
                f"{x}-{y}-{button}-{relative_x}-{relative_y}-{width}-{height}-{modifiers}"
            )

    runner = Runner()
    module = ValidPollingModuleWithClickHandler()
    runner.register_module(module)

    async def send_click():
        click_event = json.dumps(
            {
                "name": "ValidPollingModuleWithClickHandler",
                "instance": str(mock_uuid4),
                "button": 1,
                "modifiers": ["Mod1"],
                "x": 123,
                "y": 456,
                "relative_x": 12,
                "relative_y": 34,
                "width": 20,
                "height": 40,
                "extra": "should be ignored",
            }
        ).encode()

        await asyncio.sleep(0.1)
        await runner.click_event(click_event)

    runner.register_task(send_click())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    assert "123-456-1-12-34-20-40-['Mod1']" in captured.out
