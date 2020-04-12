import pulsectl

from i3pyblocks.modules import pulsectl as m_pulsectl


# TODO: improve this test namespace
def test_pulse_audio_module(mocker):
    mocker.patch.object(pulsectl, "Pulse")

    instance = m_pulsectl.PulseAudioModule()

    instance.run()

    result = instance.result()

    assert result["full_text"] == ""
