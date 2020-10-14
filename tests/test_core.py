import asyncio
import json
import os
import signal

import pytest
from mock import patch

from i3pyblocks import blocks, core, types
from i3pyblocks.blocks import basic

DEFAULT_STATE = dict(
    separator=None,
    urgent=None,
    align=None,
    markup=None,
)


@pytest.mark.asyncio
async def test_runner(capsys, mock_stdin):
    class ValidPollingBlock(blocks.PollingBlock):
        def __init__(self, block_name, sleep=0.1):
            self.count = 0
            super().__init__(
                block_name=block_name,
                sleep=sleep,
                default_state=DEFAULT_STATE,
            )

        async def run(self):
            self.count += 1
            self.update(str(self.count))

    runner = core.Runner()

    instance_1 = ValidPollingBlock(block_name="instance_1")
    instance_2 = basic.TextBlock("Hello!", block_name="instance_2")
    instance_3 = basic.TextBlock("Another hello!", block_name="instance_3")

    await runner.register_block(instance_1)
    await runner.register_block(instance_2)
    await runner.register_block(instance_3)

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")
    header = json.loads(output_lines[0])

    assert header == {"version": 1, "click_events": True}

    results = json.loads("\n".join(output_lines[1:]))

    for i, result in enumerate(results[:5], start=1):
        assert result == [
            {
                "name": "instance_1",
                "instance": str(instance_1.id),
                "full_text": str(i),
            },
            {
                "name": "instance_2",
                "instance": str(instance_2.id),
                "full_text": "Hello!",
            },
            {
                "name": "instance_3",
                "instance": str(instance_3.id),
                "full_text": "Another hello!",
            },
        ]

    assert results[5] is None


@pytest.mark.asyncio
async def test_runner_with_fault_block(capsys, mock_stdin):
    class FaultPollingBlock(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        async def run(self):
            self.count += 1
            if self.count > 4:
                raise Exception("Boom!")
            self.update(str(self.count))

    runner = core.Runner()
    instance = FaultPollingBlock()
    await runner.register_block(instance)

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")

    results = json.loads("\n".join(output_lines[1:]))

    for i, result in enumerate(results[:4], start=1):
        assert result == [
            {
                "name": "FaultPollingBlock",
                "instance": str(instance.id),
                "full_text": str(i),
            },
        ]

    assert results[4] == [
        {
            "name": "FaultPollingBlock",
            "instance": str(instance.id),
            "full_text": "Exception in FaultPollingBlock: Boom!",
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

    class ValidPollingBlockWithSignalHandler(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

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
    instance = ValidPollingBlockWithSignalHandler()
    await runner.register_block(instance, signals=[signal.SIGUSR1, signal.SIGUSR2])

    runner.register_task(send_signal())
    runner.register_task(send_another_signal())

    await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")

    results = json.loads("\n".join(output_lines[1:]))

    assert results[0] == [
        {
            "name": "ValidPollingBlockWithSignalHandler",
            "instance": str(instance.id),
            "full_text": "received_signal",
        }
    ]

    assert results[1] == [
        {
            "name": "ValidPollingBlockWithSignalHandler",
            "instance": str(instance.id),
            "full_text": "received_another_signal",
        }
    ]


@pytest.mark.asyncio
async def test_runner_with_signal_handler_exception(capsys, mock_stdin):
    async def send_signal():
        await asyncio.sleep(0.1)
        os.kill(os.getpid(), signal.SIGUSR1)

    class InvalidPollingBlockWithSignalHandler(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            self.count = 0
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        async def run(self):
            pass

        async def signal_handler(self, sig):
            raise Exception("Boom!")

    runner = core.Runner()
    instance = InvalidPollingBlockWithSignalHandler()
    await runner.register_block(instance, signals=[signal.SIGUSR1])

    runner.register_task(send_signal())

    await runner.start(timeout=0.5)

    result = instance.result()

    assert (
        result["full_text"]
        == "Exception in InvalidPollingBlockWithSignalHandler signal handler: Boom!"
    )

    assert result["urgent"] is True


@pytest.mark.asyncio
async def test_runner_with_click_event():
    class ValidPollingBlockWithClickHandler(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        async def run(self):
            pass

        async def click_handler(
            self, x, y, button, relative_x, relative_y, width, height, modifiers
        ):
            self.update(
                f"{x}-{y}-{button}-{relative_x}-{relative_y}-{width}-{height}-{modifiers}"
            )

    runner = core.Runner()
    instance = ValidPollingBlockWithClickHandler()
    await runner.register_block(instance)

    click_event = json.dumps(
        {
            "name": "ValidPollingBlockWithClickHandler",
            "instance": str(instance.id),
            "button": types.MouseButton.LEFT_BUTTON,
            "modifiers": [types.KeyModifier.ALT, types.KeyModifier.SUPER],
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
        "name": "ValidPollingBlockWithClickHandler",
        "instance": str(instance.id),
        "full_text": "123-456-1-12-34-20-40-['Mod1', 'Mod4']",
    }


@pytest.mark.asyncio
async def test_runner_with_click_event_exception():
    class InvalidPollingBlockWithClickHandler(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        async def run(self):
            pass

        async def click_handler(
            self, x, y, button, relative_x, relative_y, width, height, modifiers
        ):
            raise Exception("Boom!")

    runner = core.Runner()
    instance = InvalidPollingBlockWithClickHandler()
    await runner.register_block(instance)

    click_event = json.dumps(
        {"name": "InvalidPollingBlockWithClickHandler", "instance": str(instance.id)}
    ).encode()

    await runner.click_event(click_event)

    result = instance.result()

    assert (
        result["full_text"]
        == "Exception in InvalidPollingBlockWithClickHandler click handler: Boom!"
    )

    assert result["urgent"] is True


@pytest.mark.asyncio
async def test_runner_with_click_events(capsys):
    class ValidPollingBlockWithClickHandler(blocks.PollingBlock):
        def __init__(self, sleep=0.1):
            super().__init__(sleep=sleep, default_state=DEFAULT_STATE)

        async def run(self):
            pass

        async def click_handler(
            self, x, y, button, relative_x, relative_y, width, height, modifiers
        ):
            self.update(
                f"{x}-{y}-{button}-{relative_x}-{relative_y}-{width}-{height}-{modifiers}"
            )

    runner = core.Runner()
    instance = ValidPollingBlockWithClickHandler()
    await runner.register_block(instance)

    click_event = json.dumps(
        {
            "name": "ValidPollingBlockWithClickHandler",
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

    mock_input = [b"[\n", click_event, b","]

    with patch("i3pyblocks._internal.misc.get_aio_reader") as get_aio_reader_mock:
        reader_mock = get_aio_reader_mock.return_value
        reader_mock.readline.return_value = mock_input[0]
        reader_mock.readuntil.side_effect = mock_input[1:]

        await runner.start(timeout=0.5)

    captured = capsys.readouterr()

    output_lines = captured.out.split("\n")

    results = json.loads("\n".join(output_lines[1:]))

    assert results[0] == [
        {
            "name": "ValidPollingBlockWithClickHandler",
            "instance": str(instance.id),
            "full_text": "123-456-1-12-34-20-40-['Mod1']",
        }
    ]
