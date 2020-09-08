import subprocess
from unittest.mock import Mock, call

import pytest
from helpers import misc

from i3pyblocks import types

pulsectl = pytest.importorskip("pulsectl")
m_pulsectl = pytest.importorskip("i3pyblocks.blocks.pulsectl")

# Stub some PulseAudio sinks
SINK = misc.AttributeDict(description="description", index=1, name="sink", mute=0)
SINK_MUTE = misc.AttributeDict(description="description", index=1, name="sink", mute=1)
ANOTHER_SINK = misc.AttributeDict(
    description="another description", index=2, name="another_sink", mute=1
)


@pytest.fixture
def pulsectl_mocker():
    mock_pulsectl = Mock(pulsectl)
    mock_pulsectl.configure_mock(
        **{
            "Pulse.return_value.__enter__": Mock(),
            "Pulse.return_value.__exit__": Mock(),
        }
    )
    # Mock Pulse instance class
    mock_pulse = mock_pulsectl.Pulse.return_value
    # Mock pulse.server_list()
    mock_pulse.sink_list.return_value = [SINK, ANOTHER_SINK]
    # Mock pulse.server_info()
    mock_pulse.sink_info.return_value = SINK
    # Mock pulse.volume_get_all_chans()
    mock_pulse.volume_get_all_chans.return_value = 1.0

    return mock_pulsectl, mock_pulse


def mock_event(block_instance, facility):
    with pytest.raises(pulsectl.PulseLoopStop):
        event = Mock(pulsectl.PulseEventInfo)
        event.facility = facility
        block_instance._event_callback(event)


def test_pulse_audio_block(pulsectl_mocker):
    mock_pulsectl, mock_pulse = pulsectl_mocker
    instance = m_pulsectl.PulseAudioBlock(_pulsectl=mock_pulsectl)

    # If volume is 10%, returns Colors.WARN
    mock_pulse.volume_get_all_chans.return_value = 0.1

    instance.update_status()

    result = instance.result()

    assert result["full_text"] == "V: 10%"
    assert result["color"] == types.Color.WARN

    # If volume is 10%, returns Colors.NEUTRAL (None)
    mock_pulse.volume_get_all_chans.return_value = 0.5

    instance.update_status()

    result = instance.result()

    assert result["full_text"] == "V: 50%"

    # If volume is muted, change text and returns Color.URGENT
    mock_pulse.sink_info.return_value = SINK_MUTE

    # Simulate a normal event
    mock_event(instance, facility="sink")
    instance.handle_event()
    instance.update_status()

    result = instance.result()

    assert result["full_text"] == "V: MUTE"
    assert result["color"] == types.Color.URGENT


def test_pulse_audio_block_exception(pulsectl_mocker):
    mock_pulsectl, mock_pulse = pulsectl_mocker
    instance = m_pulsectl.PulseAudioBlock(_pulsectl=mock_pulsectl)

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
async def test_pulse_audio_block_click_handler(pulsectl_mocker):
    mock_pulsectl, mock_pulse = pulsectl_mocker
    mock_subprocess = Mock(subprocess)

    instance = m_pulsectl.PulseAudioBlock(
        command="command -c",
        _pulsectl=mock_pulsectl,
        _subprocess=mock_subprocess,
    )

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
