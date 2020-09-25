"""Blocks related to `D-Bus`_, based on `dbus-next`_.

To inspect and debug a D-Bus protocol, `DFeet`_ can help.

.. _D-Bus:
    https://en.wikipedia.org/wiki/D-Bus
.. _dbus-next:
    https://github.com/altdesktop/python-dbus-next
.. _DFeet:
    https://wiki.gnome.org/Apps/DFeet
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from dbus_next import Variant
from dbus_next import aio as dbus_aio
from dbus_next import errors

from i3pyblocks import blocks, logger, types


class DbusBlock(blocks.Block):
    r"""D-Bus Block.

    This Block extends the :class:`i3pyblocks.blocks.base.Block` by offering
    some helper methods to work with D-Bus.

    You must not instantiate this class directly, instead you should subclass
    it and implement :meth:`start()` method first.

    :param bus_name: The D-Bus bus name to introspect, i.e.:
        ``org.mpris.MediaPlayer2.spotify``.

    :param object_name: The D-Bus object to introspect, i.e.:
        ``/org/mpris/MediaPlayer2``.

    :param interface_name: The D-Bus interface to introspect, i.e.:
        ``org.mpris.MediaPlayer2``.

    :param dbus_conn_sleep: Used only before the initial connection, as a sleep
        between the calls in loop before the connection is successful. After
        the connection between the interface is made, this value is not used
        anymore.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.Block` class.
    """

    def __init__(
        self,
        bus_name: str,
        object_path: str,
        interface_name: str,
        dbus_conn_sleep: int = 1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bus_name = bus_name
        self.object_path = object_path
        self.interface_name = interface_name
        self.dbus_conn_sleep = dbus_conn_sleep
        self.interface = None

    async def setup(self, queue: Optional[asyncio.Queue] = None) -> None:
        try:
            self.bus = await dbus_aio.MessageBus().connect()
        except errors.DBusError:
            logger.exception(
                f"Cannot connect to D-Bus. Block {self.block_name} is disabled!"
            )
            return
        await super().setup(queue)

    async def get_object_via_introspection(
        self, bus_name: str, object_path: str
    ) -> dbus_aio.ProxyObject:
        introspection = await self.bus.introspect(bus_name, object_path)
        return self.bus.get_proxy_object(bus_name, object_path, introspection)

    async def get_interface_via_introspection(
        self,
        bus_name: str,
        object_path: str,
        interface_name: str,
    ) -> dbus_aio.ProxyInterface:
        obj = await self.get_object_via_introspection(bus_name, object_path)
        return obj.get_interface(interface_name)

    async def wait_interface(self) -> None:
        while not self.interface:
            try:
                self.interface = await self.get_interface_via_introspection(
                    self.bus_name,
                    self.object_path,
                    self.interface_name,
                )
            except errors.DBusError:
                logger.debug(f"D-Bus {self.bus_name} service not found, retrying...")
                await asyncio.sleep(self.dbus_conn_sleep)

    def _safe_interface_method_call(self, method: str, *args, **kwargs) -> Any:
        if self.interface:
            return getattr(self.interface, method)(*args, **kwargs)

    async def safe_method_call(self, method: str, *args) -> Any:
        r"""Safely call a D-Bus method from interface.

        :param property: Name of a D-Bus method, just in ``snake_case`` form
            instead of ``camelCase``.

        :param \*args: Positional arguments to be passed to the method.
        """
        return await self._safe_interface_method_call(f"call_{method}", *args)

    async def safe_property_set(self, property: str, value: Any) -> None:
        """Safely set a D-Bus property from interface.

        :param property: Name of a D-Bus property, just in ``snake_case`` form
            instead of ``camelCase``.

        :param value: Value to set the property.
        """
        await self._safe_interface_method_call(f"set_{property}", value)

    async def safe_property_get(self, property: str) -> Any:
        """Safely get a D-Bus property from interface.

        :param property: Name of a D-Bus property, just in ``snake_case`` form
            instead of ``camelCase``.
        """
        return await self._safe_interface_method_call(f"get_{property}")

    def safe_signal_call(self, signal: str, callback: Callable[..., None]) -> None:
        """Safely listen a D-Bus signal from interface.

        :param signal: Name of a D-Bus signal, just in ``snake_case`` form
            instead of ``camelCase``.

        :param callback: Callback function to be run when the signal is
            received.
        """
        self._safe_interface_method_call(f"on_{signal}", callback)


class KbddBlock(DbusBlock):
    """Block that shows X11 keyboard layout based on `kbdd`_ daemon.

    **Provisional block subject to changes/removal.**

    Needs ``kbdd`` daemon installed and running. In i3wm, add this to your
    ``$HOME/.config/i3/config`` file::

        # keyboard layout daemon
        exec --no-startup-id kbdd

    :param format: Format string to shown. Supports the following placeholders:

        - ``{full_layout}``: Full layout name. Quite verbose, i.e.:
          'English (US, intl., with dead keys)'

    .. _kbdd:
        https://github.com/qnikst/kbdd
    """

    bus_name = "ru.gentoo.KbddService"
    object_path = "/ru/gentoo/KbddService"
    interface_name = "ru.gentoo.kbdd"

    def __init__(
        self,
        format: str = "{full_layout}",
        **kwargs,
    ) -> None:
        super().__init__(
            bus_name=self.bus_name,
            object_path=self.object_path,
            interface_name=self.interface_name,
            **kwargs,
        )
        self.format = format

    async def click_handler(self, button: int, **_kwargs) -> None:
        if (
            button == types.MouseButton.LEFT_BUTTON
            or button == types.MouseButton.SCROLL_UP
        ):
            await self.safe_method_call("next_layout")
        elif (
            button == types.MouseButton.RIGHT_BUTTON
            or button == types.MouseButton.SCROLL_DOWN
        ):
            await self.safe_method_call("prev_layout")

        await self.update_layout()

    async def update_layout(self) -> None:
        current_layout: Optional[int] = await self.safe_method_call(
            "get_current_layout"
        )
        layout_name: Optional[str] = await self.safe_method_call(
            "get_layout_name", current_layout
        )

        self.update(self.ex_format(self.format, full_layout=layout_name))

    def update_callback(self, layout_name: str) -> None:
        self.update(self.ex_format(self.format, full_layout=layout_name))

    async def start(self) -> None:
        try:
            await self.wait_interface()
            await self.update_layout()
            self.safe_signal_call("layout_name_changed", self.update_callback)
        except Exception as e:
            self.exception(e)


class MediaPlayerBlock(DbusBlock):
    """Block that shows media player that support `MPRIS2`_ specification.

    :param format: Format string to shown. Supports the following placeholders:

        - ``{artist}``: Artist name. If more than one, it will be joined using
          ', ' as separator
        - ``{title}``: Title name.
        - ``{track_number}``: Track number.

    .. _MPRIS2:
        https://specifications.freedesktop.org/mpris-spec/latest/
    """

    bus_name = "org.mpris.MediaPlayer2.{player}"
    object_path = "/org/mpris/MediaPlayer2"
    interface_name = "org.freedesktop.DBus.Properties"

    def __init__(
        self,
        player: str = "spotify",
        format: str = "{artist} - {track_number}. {title}",
        **kwargs,
    ) -> None:
        super().__init__(
            bus_name=self.bus_name.format(player=player),
            object_path=self.object_path,
            interface_name=self.interface_name,
            **kwargs,
        )
        self.format = format

    def update_callback(
        self,
        interface_name: str,
        changed_properties: Dict[str, Variant],
        invalidated_properties: List[Variant],
    ) -> None:
        metadata = changed_properties["Metadata"].value
        self.update(
            self.ex_format(
                self.format,
                artist=", ".join(metadata["xesam:artist"].value),
                title=metadata["xesam:title"].value,
                track_number=metadata["xesam:trackNumber"].value,
            )
        )

    async def start(self) -> None:
        try:
            await self.wait_interface()
            self.safe_signal_call("properties_changed", self.update_callback)
        except Exception as e:
            self.exception(e)
