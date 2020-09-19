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
from typing import Optional

from dbus_next import aio as dbus_aio
from dbus_next import errors

from i3pyblocks import blocks, logger, types


class DbusBlock(blocks.Block):
    """D-Bus Block.

    This Block extends the :class:`i3pyblocks.blocks.base.Block` by offering
    some helper methods to work with D-Bus, alongside with a proper :meth:`setup()`
    method.

    You must not instantiate this class directly, instead you should subclass
    it and implement :meth:`start()` method first.
    """

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
        sleep: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.sleep = sleep
        self.interface = None

    def update_callback(self, layout_name: str) -> None:
        self.update(self.ex_format(self.format, full_layout=layout_name))

    async def update_layout(self) -> None:
        if self.interface:
            current_layout: int = await self.interface.call_get_current_layout()
            layout_name: str = await self.interface.call_get_layout_name(current_layout)

            self.update(self.ex_format(self.format, full_layout=layout_name))

    async def click_handler(self, button: int, **_kwargs) -> None:
        if (
            button == types.MouseButton.LEFT_BUTTON
            or button == types.MouseButton.SCROLL_UP
        ):
            if self.interface:
                await self.interface.call_next_layout()
        elif (
            button == types.MouseButton.RIGHT_BUTTON
            or button == types.MouseButton.SCROLL_DOWN
        ):
            if self.interface:
                await self.interface.call_prev_layout()
        await self.update_layout()

    async def start(self) -> None:
        if self.frozen:
            return

        while not self.interface:
            try:
                self.interface = await self.get_interface_via_introspection(
                    self.bus_name,
                    self.object_path,
                    self.interface_name,
                )
            except errors.DBusError:
                logger.debug(f"D-Bus {self.bus_name} service not found, retrying...")
                await asyncio.sleep(self.sleep)

        try:
            await self.update_layout()
            self.interface.on_layout_name_changed(self.update_callback)
        except Exception as e:
            logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e
