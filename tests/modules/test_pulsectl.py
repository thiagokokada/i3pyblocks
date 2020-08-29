import subprocess
from unittest.mock import call, Mock

import pytest
import pulsectl

from i3pyblocks import types
from i3pyblocks.modules import pulsectl as m_pulsectl

from helpers import misc

# Stub some PulseAudio sinks
SINK = misc.AttributeDict(description="description", index=1, name="sink", mute=0)
SINK_MUTE = misc.AttributeDict(description="description", index=1, name="sink", mute=1)
ANOTHER_SINK = misc.AttributeDict(
    description="another description", index=2, name="another_sink", mute=1
)


@pytest.fixture
def pulsectl_mocker():
    mock_pulsectl = Mock(pulsectl)
    # Mock Pulse instance class
    mock_pulse = mock_pulsectl.Pulse.return_value
    # Mock pulse.server_list()
    mock_pulse.sink_list.return_value = [SINK, ANOTHER_SINK]
    # Mock pulse.server_info()
    mock_pulse.sink_info.return_value = SINK
    # Mock pulse.volume_get_all_chans()
    mock_pulse.volume_get_all_chans.return_value = 1.0

    return mock_pulsectl, mock_pulse


def mock_event(module_instance, facility):
    with pytest.raises(pulsectl.PulseLoopStop):
        event = Mock(pulsectl.PulseEventInfo)
        event.facility = facility
        module_instance._event_callback(event)


def test_pulse_audio_module(pulsectl_mocker):
    mock_pulsectl, mock_pulse = pulsectl_mocker
    instance = m_pulsectl.PulseAudioModule(_pulsectl=mock_pulsectl)

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

    instance.toggle_mute()
    mock_pulse.mute.assert_called_with(SINK, mute=True)

    # If volume is muted, change text and returns Color.URGENT
    mock_pulse.sink_info.return_value = SINK_MUTE

    # Simulate a normal event
    mock_event(instance, facility="sink")
    instance.handle_event()
    instance.update_status()

    result = instance.result()

    assert result["full_text"] == "V: MUTE"
    assert result["color"] == types.Color.URGENT

    instance.toggle_mute()
    mock_pulse.mute.assert_called_with(SINK_MUTE, mute=False)


def test_pulse_audio_module_exception(pulsectl_mocker):
    mock_pulsectl, mock_pulse = pulsectl_mocker
    instance = m_pulsectl.PulseAudioModule(_pulsectl=mock_pulsectl)

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
async def test_pulse_audio_module_click_handler(pulsectl_mocker):
    mock_pulsectl, mock_pulse = pulsectl_mocker
    mock_subprocess = Mock(subprocess)

    instance = m_pulsectl.PulseAudioModule(
        command=("command", "-c"), _pulsectl=mock_pulsectl, _subprocess=mock_subprocess
    )

    await instance.click_handler(types.Mouse.LEFT_BUTTON)
    mock_subprocess.Popen.assert_called_once_with(("command", "-c"))

    mute_mock = mock_pulse.mute
    await instance.click_handler(types.Mouse.RIGHT_BUTTON)
    mute_mock.assert_called_once_with(SINK, mute=True)

    volume_change_mock = mock_pulse.volume_change_all_chans
    await instance.click_handler(types.Mouse.SCROLL_UP)
    await instance.click_handler(types.Mouse.SCROLL_DOWN)
    volume_change_mock.assert_has_calls([call(SINK, 0.05), call(SINK, -0.05)])
