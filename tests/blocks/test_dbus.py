import pytest
from asynctest import CoroutineMock, patch

from i3pyblocks import types
from i3pyblocks.blocks import dbus


@pytest.mark.asyncio
async def test_dbus_block():
    class ValidDbusBlock(dbus.DbusBlock):
        async def start(self):
            pass

    mock_config = {
        "MessageBus.return_value.connect": CoroutineMock(),
        "MessageBus.return_value.connect.return_value.introspect": CoroutineMock(),
    }
    with patch("i3pyblocks.blocks.dbus.dbus_aio", **mock_config) as mock_dbus_aio:
        instance = ValidDbusBlock()
        await instance.setup()

        mock_bus = mock_dbus_aio.MessageBus.return_value.connect.return_value

        # Testing get_object_via_introspection
        await instance.get_object_via_introspection("some.object", "/some/path")
        mock_bus.introspect.assert_called_once_with("some.object", "/some/path")
        mock_bus.get_proxy_object.assert_called_once_with(
            "some.object", "/some/path", mock_bus.introspect.return_value
        )

        # Testing get_interface_via_introspection
        await instance.get_interface_via_introspection(
            "some.object", "/some/path", "another.object"
        )
        mock_obj = mock_bus.get_proxy_object.return_value
        mock_obj.get_interface.assert_called_once_with("another.object")


@pytest.mark.asyncio
async def test_kbdd_block():
    mock_config = {
        "MessageBus.return_value.connect": CoroutineMock(),
        "MessageBus.return_value.connect.return_value.introspect": CoroutineMock(),
    }
    with patch("i3pyblocks.blocks.dbus.dbus_aio", **mock_config) as mock_dbus_aio:
        instance = dbus.KbddBlock(format="{full_layout:.2s}")
        await instance.setup()

        mock_bus = mock_dbus_aio.MessageBus.return_value.connect.return_value
        mock_obj = mock_bus.get_proxy_object.return_value
        mock_interface = mock_obj.get_interface.return_value

        mock_interface.call_get_current_layout = CoroutineMock()
        mock_interface.call_get_layout_name = CoroutineMock()
        mock_interface.call_get_layout_name.return_value = (
            "English (US, intl., with dead keys)"
        )

        await instance.start()
        mock_interface.on_layout_name_changed.assert_called_once()
        assert instance.result()["full_text"] == "En"

        # Testing if click handler works
        mock_interface.call_get_layout_name.return_value = "Portuguese (Brazil)"

        mock_interface.call_next_layout = CoroutineMock()
        await instance.click_handler(button=types.MouseButton.LEFT_BUTTON)
        mock_interface.call_next_layout.assert_called_once()

        mock_interface.call_prev_layout = CoroutineMock()
        await instance.click_handler(button=types.MouseButton.RIGHT_BUTTON)
        mock_interface.call_prev_layout.assert_called_once()

        assert instance.result()["full_text"] == "Po"

        instance.update_callback("Something")
        assert instance.result()["full_text"] == "So"
