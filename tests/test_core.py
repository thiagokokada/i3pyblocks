import asyncio
import json
import os
import signal

import pytest

from i3pyblocks.core import Runner
from i3pyblocks.modules import PollingModule


@pytest.mark.asyncio
async def test_runner(capsys, mock_stdin):
    class ValidPollingModule(PollingModule):
        def __init__(self, name, sleep=0.1):
            self.count = 0
            super().__init__(
                name=name,
                sleep=sleep,
                separator=None,
                urgent=None,
                align=None,
                markup=None,
            )

        async def run(self):
            self.count += 1
            self.update(str(self.count))

    runner = Runner()

    instance_1 = ValidPollingModule(name="instance_1")
    instance_2 = ValidPollingModule(name="instance_2")
    instance_3 = ValidPollingModule(name="instance_3")

    runner.register_module(instance_1)
    runner.register_module(instance_2)
    runner.register_module(instance_3)

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")
    header = json.loads(output_lines[0])

    assert header == {"version": 1, "click_events": True}

    results = json.loads("\n".join(output_lines[1:]))

    for i, result in enumerate(results[:5], start=1):
        assert result == [
            {"name": "instance_1", "instance": str(instance_1.id), "full_text": str(i)},
            {"name": "instance_2", "instance": str(instance_2.id), "full_text": str(i)},
            {"name": "instance_3", "instance": str(instance_3.id), "full_text": str(i)},
        ]

    assert results[5] is None


@pytest.mark.asyncio
async def test_runner_with_fault_module(capsys, mock_stdin):
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
    instance = FaultPollingModule()
    runner.register_module(instance)

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")

    results = json.loads("\n".join(output_lines[1:]))

    for i, result in enumerate(results[:4], start=1):
        assert result == [
            {
                "name": "FaultPollingModule",
                "instance": str(instance.id),
                "full_text": str(i),
            },
        ]

    assert results[4] == [
        {
            "name": "FaultPollingModule",
            "instance": str(instance.id),
            "full_text": "Exception in FaultPollingModule: Boom!",
            "urgent": True,
        }
    ]


@pytest.mark.asyncio
async def test_runner_with_signal_handler(capsys, mock_stdin):
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
    instance = ValidPollingModuleWithSignalHandler()
    runner.register_module(instance, signals=[signal.SIGUSR1, signal.SIGUSR2])

    runner.register_task(send_signal())
    runner.register_task(send_another_signal())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")

    results = json.loads("\n".join(output_lines[1:]))

    assert results[0] == [
        {
            "name": "ValidPollingModuleWithSignalHandler",
            "instance": str(instance.id),
            "full_text": "received_signal",
        }
    ]

    assert results[1] == [
        {
            "name": "ValidPollingModuleWithSignalHandler",
            "instance": str(instance.id),
            "full_text": "received_another_signal",
        }
    ]


# TODO: Test with mocked sys.stdin instead of calling functions directly
@pytest.mark.asyncio
async def test_runner_with_click_handler(capsys):
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
    instance = ValidPollingModuleWithClickHandler()
    runner.register_module(instance)

    async def send_click():
        click_event = json.dumps(
            {
                "name": "ValidPollingModuleWithClickHandler",
                "instance": str(instance.id),
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

    output_lines = captured.out.split("\n")

    results = json.loads("\n".join(output_lines[1:]))

    assert results[0] == [
        {
            "name": "ValidPollingModuleWithClickHandler",
            "instance": str(instance.id),
            "full_text": "123-456-1-12-34-20-40-['Mod1']",
        }
    ]
