import pytest
from asynctest import patch
from helpers import misc

x11 = pytest.importorskip("i3pyblocks.blocks.x11")


@pytest.mark.asyncio
async def test_dpms_block():
    mock_config = {
        "Display.return_value.dpms_info.side_effect": [
            # One for run() call, another one for click_handler()
            misc.AttributeDict(state=1),
            misc.AttributeDict(state=1),
            # One for run() call, another one for click_handler()
            misc.AttributeDict(state=0),
            misc.AttributeDict(state=0),
        ]
    }
    with patch("i3pyblocks.blocks.x11.Xdisplay", **mock_config) as mock_Xdisplay:
        mock_Display = mock_Xdisplay.Display.return_value

        instance = x11.DPMSBlock()

        await instance.run()
        assert instance.result()["full_text"] == "DPMS ON"

        await instance.click_handler()
        mock_Display.dpms_disable.assert_called_once()

        mock_Display.reset_mock()

        await instance.run()
        assert instance.result()["full_text"] == "DPMS OFF"

        await instance.click_handler()
        mock_Display.dpms_enable.assert_called_once()
