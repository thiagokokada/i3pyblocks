from unittest.mock import Mock

import pytest
from helpers import misc

Xdisplay = pytest.importorskip("Xlib.display")
m_xlib = pytest.importorskip("i3pyblocks.blocks.xlib")


@pytest.mark.asyncio
async def test_dpms_block():
    mock_Xdisplay = Mock(Xdisplay)
    mock_Display = mock_Xdisplay.Display.return_value
    mock_dpms_info = mock_Display.dpms_info

    instance = m_xlib.DPMSBlock(_Xdisplay=mock_Xdisplay)

    mock_dpms_info.return_value = misc.AttributeDict(state=1)
    await instance.run()
    assert instance.result()["full_text"] == "DPMS ON"

    await instance.click_handler()
    mock_Display.dpms_disable.assert_called_once()

    mock_Display.reset_mock()

    mock_dpms_info.return_value = misc.AttributeDict(state=0)
    await instance.run()
    assert instance.result()["full_text"] == "DPMS OFF"

    await instance.click_handler()
    mock_Display.dpms_enable.assert_called_once()
