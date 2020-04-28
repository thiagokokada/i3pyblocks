import asyncio
import json
import os
import signal

import pytest
from asynctest import CoroutineMock
from unittest.mock import patch

from i3pyblocks import core, modules


# TODO: Validate if we can actually read from stdin here
@pytest.mark.asyncio
async def test_get_aio_reader(capsys, mocker):
    mocker.patch("sys.stdin", return_value=b"Hello!")
    loop = asyncio.get_running_loop()

    with capsys.disabled():
        reader = await core.get_aio_reader(loop)
        assert isinstance(reader, asyncio.StreamReader)


@pytest.mark.asyncio
async def test_runner(capsys, mock_stdin):
    class ValidPollingModule(modules.PollingModule):
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

    runner = core.Runner()

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
    class FaultPollingModule(modules.PollingModule):
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

    runner = core.Runner()
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

    class ValidPollingModuleWithSignalHandler(modules.PollingModule):
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

    runner = core.Runner()
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


@pytest.mark.asyncio
async def test_runner_with_signal_handler_exception(capsys, mock_stdin, mocker):
    async def send_signal():
        await asyncio.sleep(0.1)
        os.kill(os.getpid(), signal.SIGUSR1)

    class InvalidPollingModuleWithSignalHandler(modules.PollingModule):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            pass

        async def signal_handler(self, sig):
            raise Exception("Boom!")

    logger_mock = mocker.patch("i3pyblocks.core.logger.exception")
    runner = core.Runner()
    instance = InvalidPollingModuleWithSignalHandler()
    runner.register_module(instance, signals=[signal.SIGUSR1])

    runner.register_task(send_signal())

    await runner.start(timeout=0.5)

    logger_mock.assert_called_once()


@pytest.mark.asyncio
async def test_runner_with_click_event():
    class ValidPollingModuleWithClickHandler(modules.PollingModule):
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

    runner = core.Runner()
    instance = ValidPollingModuleWithClickHandler()
    runner.register_module(instance)

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

    await runner.click_event(click_event)
    result = instance.result()

    assert result == {
        "name": "ValidPollingModuleWithClickHandler",
        "instance": str(instance.id),
        "full_text": "123-456-1-12-34-20-40-['Mod1']",
    }


@pytest.mark.asyncio
async def test_runner_with_click_event_exception(mocker):
    class InvalidPollingModuleWithClickHandler(modules.PollingModule):
        def __init__(self, sleep=0.1):
            super().__init__(
                sleep=sleep, separator=None, urgent=None, align=None, markup=None
            )

        async def run(self):
            pass

        async def click_handler(
            self, x, y, button, relative_x, relative_y, width, height, modifiers
        ):
            raise Exception("Boom!")

    logger_mock = mocker.patch("i3pyblocks.core.logger.exception")
    runner = core.Runner()
    instance = InvalidPollingModuleWithClickHandler()
    runner.register_module(instance)

    click_event = json.dumps(
        {"name": "InvalidPollingModuleWithClickHandler", "instance": str(instance.id)}
    ).encode()

    await runner.click_event(click_event)

    logger_mock.assert_called_once()


@pytest.mark.asyncio
async def test_runner_with_click_events(capsys):
    class ValidPollingModuleWithClickHandler(modules.PollingModule):
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

    runner = core.Runner()
    instance = ValidPollingModuleWithClickHandler()
    runner.register_module(instance)

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

    with patch(
        "i3pyblocks.core.get_aio_reader", new=CoroutineMock()
    ) as get_aio_reader_mock:
        reader_mock = get_aio_reader_mock.return_value
        reader_mock.readline = CoroutineMock()
        reader_mock.readline.return_value = b"[\n"
        reader_mock.readuntil = CoroutineMock()
        reader_mock.readuntil.side_effect = [click_event, b","]

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
