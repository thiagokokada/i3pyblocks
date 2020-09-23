import pytest
from asynctest import CoroutineMock, patch
from dbus_next import Variant

from i3pyblocks import types
from i3pyblocks.blocks import dbus


# TODO: Improve tests
@pytest.mark.asyncio
async def test_dbus_block():
    class ValidDbusBlock(dbus.DbusBlock):
        async def run(self):
            self.update("Hello!")

        def update_callback(self):
            self.update("Bye")

    with patch(
        "i3pyblocks.blocks.dbus.dbus_aio", autospec=True, spec_set=True
    ) as mock_dbus_aio:
        mock_dbus_aio.configure_mock(
            **{
                "MessageBus.return_value.connect": CoroutineMock(),
                "MessageBus.return_value.connect.return_value.introspect": CoroutineMock(),
            }
        )
        instance = ValidDbusBlock(
            bus_name="some.object",
            object_path="/some/path",
            interface_name="some.interface",
            loop_method="some_method",
        )
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

        await instance.start()
        assert instance.result()["full_text"] == "Hello!"


@pytest.mark.asyncio
async def test_kbdd_block():
    with patch(
        "i3pyblocks.blocks.dbus.dbus_aio", autospec=True, spec_set=True
    ) as mock_dbus_aio:
        mock_dbus_aio.configure_mock(
            **{
                "MessageBus.return_value.connect": CoroutineMock(),
                "MessageBus.return_value.connect.return_value.introspect": CoroutineMock(),
            }
        )
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


@pytest.mark.asyncio
async def test_media_player_block():
    with patch(
        "i3pyblocks.blocks.dbus.dbus_aio", autospec=True, spec_set=True
    ) as mock_dbus_aio:
        mock_dbus_aio.configure_mock(
            **{
                "MessageBus.return_value.connect": CoroutineMock(),
                "MessageBus.return_value.connect.return_value.introspect": CoroutineMock(),
            }
        )
        instance = dbus.MediaPlayerBlock()
        await instance.setup()

        changed_properties = {
            "Metadata": Variant(
                "a{sv}",
                {
                    "mpris:trackid": Variant(
                        "s", "spotify:track:5hbg2YisSRgoGG85pl0g1F"
                    ),
                    "mpris:length": Variant("t", 227040000),
                    "mpris:artUrl": Variant(
                        "s",
                        "https://open.spotify.com/image/"
                        "ab67616d00001e02d583a42a4c3fc63b61f1eda9",
                    ),
                    "xesam:album": Variant("s", "センチメートル"),
                    "xesam:albumArtist": Variant("as", ["the peggies"]),
                    "xesam:artist": Variant("as", ["the peggies"]),
                    "xesam:autoRating": Variant("d", 0.67),
                    "xesam:discNumber": Variant("i", 1),
                    "xesam:title": Variant("s", "センチメートル"),
                    "xesam:trackNumber": Variant("i", 1),
                    "xesam:url": Variant(
                        "s", "https://open.spotify.com/track/5hbg2YisSRgoGG85pl0g1F"
                    ),
                },
            ),
            "PlaybackStatus": Variant("s", "Playing"),
        }

        instance.update_callback(
            "org.mpris.MediaPlayer2.Player",
            changed_properties,
            [],
        )
        assert instance.result()["full_text"] == "the peggies - 1. センチメートル"
