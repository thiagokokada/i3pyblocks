from unittest.mock import Mock, call, patch

import pytest
from helpers import misc

from i3pyblocks import types

try:
    pulsectl = pytest.importorskip("pulsectl")
    pulse = pytest.importorskip("i3pyblocks.blocks.pulse")
except OSError:
    from unittest import SkipTest

    raise SkipTest("PulseAudio is not installed, skipping tests...")

# Stub some PulseAudio sinks
SINK = misc.AttributeDict(description="description", index=1, name="sink", mute=0)
SINK_MUTE = misc.AttributeDict(description="description", index=1, name="sink", mute=1)
ANOTHER_SINK = misc.AttributeDict(
    description="another description", index=2, name="another_sink", mute=1
)
MOCK_CONFIG = {
    "Pulse.return_value.__enter__": Mock(),
    "Pulse.return_value.__exit__": Mock(),
    "Pulse.return_value.sink_list.return_value": [SINK, ANOTHER_SINK],
    "Pulse.return_value.sink_info.side_effect": [SINK, SINK_MUTE],
    "Pulse.return_value.volume_get_all_chans.side_effect": [0, 0.2, 0.8],
    # Unmock those exceptions
    "PulseLoopStop": pulsectl.PulseLoopStop,
    "PulseError": pulsectl.PulseError,
}


def mock_event(block_instance, facility):
    with pytest.raises(pulsectl.PulseLoopStop):
        event = Mock(pulsectl.PulseEventInfo)
        event.facility = facility
        block_instance._event_callback(event)


def test_pulse_audio_block():
    with patch("i3pyblocks.blocks.pulse.pulsectl", **MOCK_CONFIG):
        instance = pulse.PulseAudioBlock()

        # If volume is 0%, returns Colors.URGENT
        instance.update_status()
        result = instance.result()
        assert result["full_text"] == "V: 0%"
        assert result["color"] == types.Color.URGENT

        # If volume is 20%, returns Colors.WARN
        instance.update_status()
        result = instance.result()
        assert result["full_text"] == "V: 20%"
        assert result["color"] == types.Color.WARN

        # If volume is 80%, returns Colors.NEUTRAL (None)
        instance.update_status()
        result = instance.result()
        assert result["full_text"] == "V: 80%"
        assert not result.get("color")

        # Simulate a normal event
        mock_event(instance, facility="sink")
        instance.handle_event()
        instance.update_status()

        result = instance.result()

        assert result["full_text"] == "V: MUTE"
        assert result["color"] == types.Color.URGENT


def test_pulse_audio_block_exception():
    with patch("i3pyblocks.blocks.pulse.pulsectl", **MOCK_CONFIG) as mock_pulsectl:
        instance = pulse.PulseAudioBlock()

        mock_pulse = mock_pulsectl.Pulse.return_value

        # Simulate an event going wrong
        mock_event(instance, facility="server")
        mock_pulse.sink_info.side_effect = [pulsectl.PulseError(), SINK]
        instance.handle_event()

        mock_pulse.sink_info.assert_called()
        # Why 3 times?
        # - The first is during setup
        # - The second is during handle_event() (raising an Exception)
        # - The third is called by retry logic in _update_sink_info()
        assert mock_pulse.sink_info.call_count == 3


@pytest.mark.asyncio
async def test_pulse_audio_block_click_handler():
    with patch(
        "i3pyblocks.blocks.pulse.pulsectl", **MOCK_CONFIG
    ) as mock_pulsectl, patch("i3pyblocks.blocks.pulse.subprocess") as mock_subprocess:
        instance = pulse.PulseAudioBlock(
            command="command -c",
        )

        mock_pulse = mock_pulsectl.Pulse.return_value

        # LEFT_BUTTON should run command
        await instance.click_handler(types.MouseButton.LEFT_BUTTON)
        mock_subprocess.Popen.assert_called_once_with("command -c", shell=True)

        context_manager_mock = mock_pulse.__enter__
        mute_mock = context_manager_mock.return_value.mute

        # When not mute, pressing RIGHT_BUTTON will mute it
        instance.sink.mute = 0
        await instance.click_handler(types.MouseButton.RIGHT_BUTTON)
        mute_mock.assert_called_once_with(SINK, mute=True)

        mute_mock.reset_mock()

        # When not mute, pressing RIGHT_BUTTON will unmute it
        instance.sink.mute = 1
        await instance.click_handler(types.MouseButton.RIGHT_BUTTON)
        mute_mock.assert_called_once_with(SINK, mute=False)

        # Scroll Up/Down should trigger volume increase/decrease
        await instance.click_handler(types.MouseButton.SCROLL_UP)
        await instance.click_handler(types.MouseButton.SCROLL_DOWN)
        context_manager_mock.assert_has_calls(
            [
                call(),
                call().volume_change_all_chans(SINK, 0.05),
                call(),
                call().volume_change_all_chans(SINK, -0.05),
            ]
        )
