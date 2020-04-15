import pulsectl

import pytest

from i3pyblocks.modules import pulsectl as m_pulsectl


# TODO: improve this test namespace
def test_pulse_audio_module(mocker):
    mocker.patch.object(pulsectl, "Pulse")

    with pytest.raises(AssertionError):
        m_pulsectl.PulseAudioModule()
