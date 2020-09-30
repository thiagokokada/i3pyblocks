from unittest.mock import Mock, patch

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
DEFAULT_MOCK_CONFIG = {
    "Pulse.return_value.__enter__": Mock(),
    "Pulse.return_value.__exit__": Mock(),
    "Pulse.return_value.__enter__.return_value.sink_list.return_value": [
        SINK,
        ANOTHER_SINK,
    ],
    "Pulse.return_value.__enter__.return_value.sink_info.return_value": SINK,
    "Pulse.return_value.__enter__.return_value.volume_get_all_chans.return_value": 0.8,
    # Unmock those exceptions
    "PulseLoopStop": pulsectl.PulseLoopStop,
    "PulseError": pulsectl.PulseError,
}


def mock_event(block_instance, facility):
    event = Mock(pulsectl.PulseEventInfo)
    event.facility = facility
    block_instance._event_callback(event)


def test_pulse_audio_block():
    with patch(
        "i3pyblocks.blocks.pulse.pulsectl", autospec=True, spec_set=True
    ) as mock_pulse:
        mock_pulse.configure_mock(
            **{
                **DEFAULT_MOCK_CONFIG,
                "Pulse.return_value.__enter__.return_value.sink_info.side_effect": [
                    SINK,
                    SINK,
                    SINK,
                    SINK_MUTE,
                ],
                "Pulse.return_value.__enter__.return_value.volume_get_all_chans.side_effect": [
                    0.0,
                    0.2,
                    0.8,
                ],
            }
        )
        instance = pulse.PulseAudioBlock()

        # If volume is 0%, returns Colors.URGENT
        instance.run_sync()
        result = instance.result()
        assert result.get("full_text") == "V: 0%"
        assert result.get("color") == types.Color.URGENT

        # If volume is 20%, returns Colors.WARN
        mock_event(instance, facility="server")
        result = instance.result()
        assert result.get("full_text") == "V: 20%"
        assert result.get("color") == types.Color.WARN

        # If volume is 80%, returns Colors.NEUTRAL (None)
        mock_event(instance, facility="sink")
        result = instance.result()
        assert result.get("full_text") == "V: 80%"
        assert result.get("color") == types.Color.NEUTRAL

        # If mute, returns Color.URGENT
        mock_event(instance, facility="server")
        result = instance.result()

        assert result.get("full_text") == "V: MUTE"
        assert result.get("color") == types.Color.URGENT


def test_pulse_audio_block_click_handler_sync():
    with patch(
        "i3pyblocks.blocks.pulse.pulsectl", autospec=True, spec_set=True
    ) as mock_pulsectl, patch(
        "i3pyblocks.blocks.pulse.subprocess", autospec=True, spec_set=True
    ) as mock_subprocess:
        mock_pulsectl.configure_mock(
            **{
                **DEFAULT_MOCK_CONFIG,
                "Pulse.return_value.__enter__.return_value.sink_info.side_effect": [
                    SINK,
                    SINK,
                    SINK,
                    SINK,
                    SINK,
                    SINK,
                    SINK,
                    SINK,
                    SINK_MUTE,
                ],
            }
        )
        instance = pulse.PulseAudioBlock(
            command=("command", "-c"),
        )
        mock_event(instance, facility="server")

        mock_pulse = mock_pulsectl.Pulse.return_value

        # LEFT_BUTTON should run command
        instance.click_handler_sync(types.MouseButton.LEFT_BUTTON)
        mock_subprocess.popener.assert_called_once_with(("command", "-c"))

        context_manager_mock = mock_pulse.__enter__
        mute_mock = context_manager_mock.return_value.mute

        # Scroll Up/Down should trigger volume increase/decrease
        volume_change_all_chans_mock = (
            context_manager_mock.return_value.volume_change_all_chans
        )
        instance.click_handler_sync(types.MouseButton.SCROLL_UP)
        volume_change_all_chans_mock.assert_called_once_with(SINK, 0.05)

        volume_change_all_chans_mock.reset_mock()

        instance.click_handler_sync(types.MouseButton.SCROLL_DOWN)
        volume_change_all_chans_mock.assert_called_once_with(SINK, -0.05)

        # When not mute, pressing RIGHT_BUTTON will mute it
        instance.click_handler_sync(types.MouseButton.RIGHT_BUTTON)
        mute_mock.assert_called_once_with(SINK, mute=True)

        mute_mock.reset_mock()

        instance.click_handler_sync(types.MouseButton.RIGHT_BUTTON)
        mute_mock.assert_called_once_with(SINK_MUTE, mute=False)
