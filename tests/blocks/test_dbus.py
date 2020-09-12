import pytest
from asynctest import CoroutineMock, patch

from i3pyblocks import types
from i3pyblocks.blocks import dbus


@pytest.mark.asyncio
async def test_kbdd_block():
    mock_config = {
        "MessageBus.return_value.connect": CoroutineMock(),
        "MessageBus.return_value.connect.return_value.introspect": CoroutineMock(),
    }
    with patch("i3pyblocks.blocks.dbus.dbus_aio", **mock_config):
        instance = dbus.KbddBlock(format="{full_layout:.2s}")
        await instance.setup()

        # Get the mocked properties attribute from instance
        mock_properties = instance.properties

        mock_properties.call_get_current_layout = CoroutineMock()
        mock_properties.call_get_layout_name = CoroutineMock()
        mock_properties.call_get_layout_name.return_value = (
            "English (US, intl., with dead keys)"
        )

        await instance.start()
        mock_properties.on_layout_name_changed.assert_called_once()
        assert instance.result()["full_text"] == "En"

        # Testing if click handler works
        mock_properties.call_get_layout_name.return_value = "Portuguese (Brazil)"

        mock_properties.call_next_layout = CoroutineMock()
        await instance.click_handler(button=types.MouseButton.LEFT_BUTTON)
        mock_properties.call_next_layout.assert_called_once()

        mock_properties.call_prev_layout = CoroutineMock()
        await instance.click_handler(button=types.MouseButton.RIGHT_BUTTON)
        mock_properties.call_prev_layout.assert_called_once()

        assert instance.result()["full_text"] == "Po"

        instance.update_callback("Something")
        assert instance.result()["full_text"] == "So"
