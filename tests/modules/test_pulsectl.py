from unittest.mock import call

import pulsectl

from i3pyblocks import types
from i3pyblocks.modules import pulsectl as m_pulsectl


class AttributeDict(dict):
    __getattr__ = dict.__getitem__  # type: ignore
    __setattr__ = dict.__setitem__  # type: ignore


def test_pulse_audio_module(mocker):
    MockPulse = mocker.patch.object(pulsectl, "Pulse")
    mock_instance = MockPulse.return_value
    mock_instance.server_info.return_value = AttributeDict(
        default_source_name="source", default_sink_name="sink"
    )
    sink = AttributeDict(description="description", index=1, name="sink", mute=0)
    sink_mute = AttributeDict(description="description", index=1, name="sink", mute=1)
    another_sink = AttributeDict(
        description="another description", index=2, name="another_sink", mute=1
    )
    mock_instance.sink_list.return_value = [sink, another_sink]
    mock_instance.sink_info.return_value = sink
    mock_instance.volume_get_all_chans.return_value = 1.0

    instance = m_pulsectl.PulseAudioModule()

    # If volume is 10%, returns Colors.WARN
    mock_instance.volume_get_all_chans.return_value = 0.1

    instance._update_status()

    result = instance.result()

    assert result["full_text"] == "V: 10%"
    assert result["color"] == types.Color.WARN

    # If volume is 10%, returns Colors.NEUTRAL (None)
    mock_instance.volume_get_all_chans.return_value = 0.5

    instance._update_status()

    result = instance.result()

    assert result["full_text"] == "V: 50%"

    instance._toggle_mute()
    mock_instance.mute.assert_called_with(sink, mute=True)

    # If volume is muted, change text and returns Color.URGENT
    mock_instance.sink_info.return_value = sink_mute

    instance._update_sink_info()
    instance._update_status()

    result = instance.result()

    assert result["full_text"] == "V: MUTE"
    assert result["color"] == types.Color.URGENT

    instance._toggle_mute()
    mock_instance.mute.assert_called_with(sink_mute, mute=False)


def test_pulse_audio_module_click_handler(mocker):
    MockPulse = mocker.patch.object(pulsectl, "Pulse")
    mock_instance = MockPulse.return_value

    mock_instance.server_info.return_value = AttributeDict(
        default_source_name="source", default_sink_name="sink"
    )
    sink = AttributeDict(description="description", index=1, name="sink", mute=0)
    mock_instance.sink_list.return_value = [sink]
    mock_instance.sink_info.return_value = sink
    mock_instance.volume_get_all_chans.return_value = 1.0

    instance = m_pulsectl.PulseAudioModule(command=("command", "-c"))

    popen_mock = mocker.patch("subprocess.Popen")
    instance.click_handler(types.Mouse.LEFT_BUTTON)
    popen_mock.assert_called_once_with(("command", "-c"))

    mute_mock = mock_instance.mute
    instance.click_handler(types.Mouse.RIGHT_BUTTON)
    mute_mock.assert_called_once_with(sink, mute=True)

    volume_change_mock = mock_instance.volume_change_all_chans
    instance.click_handler(types.Mouse.SCROLL_UP)
    instance.click_handler(types.Mouse.SCROLL_DOWN)
    volume_change_mock.assert_has_calls([call(sink, 0.05), call(sink, -0.05)])
