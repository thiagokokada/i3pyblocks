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

from i3pyblocks import blocks, core, types


class KbddBlock(blocks.Block):
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

    def __init__(self, format: str = "{full_layout}", **kwargs) -> None:
        super().__init__(**kwargs)
        self.format = format

    async def update_layout(self) -> None:
        current_layout: int = await self.interface.call_get_current_layout()
        layout_name: str = await self.interface.call_get_layout_name(current_layout)

        self.update(self.ex_format(self.format, full_layout=layout_name))

    async def click_handler(self, button: int, **_kwargs) -> None:
        if (
            button == types.MouseButton.LEFT_BUTTON
            or button == types.MouseButton.SCROLL_UP
        ):
            await self.interface.call_next_layout()
        elif (
            button == types.MouseButton.RIGHT_BUTTON
            or button == types.MouseButton.SCROLL_DOWN
        ):
            await self.interface.call_prev_layout()
        await self.update_layout()

    def update_callback(self, layout_name: str) -> None:
        self.update(self.ex_format(self.format, full_layout=layout_name))

    async def setup(self, queue: Optional[asyncio.Queue] = None) -> None:
        try:
            self.bus = await dbus_aio.MessageBus().connect()
            self.introspection = await self.bus.introspect(
                self.bus_name,
                self.object_path,
            )
            self.kbdd_object = self.bus.get_proxy_object(
                self.bus_name,
                self.object_path,
                self.introspection,
            )
            self.interface = self.kbdd_object.get_interface(self.interface_name)
        except errors.DBusError:
            core.logger.exception(
                f"Error during {self.block_name} setup. This block is disabled!"
            )
            return

        await super().setup(queue)

    async def start(self) -> None:
        try:
            await self.update_layout()
            self.interface.on_layout_name_changed(self.update_callback)
        except Exception as e:
            core.logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e


class MediaPlayerBlock(blocks.Block):
    bus_name = "org.mpris.MediaPlayer2.{player}"
    object_path = "/org/mpris/MediaPlayer2"
    interface_name = "org.freedesktop.DBus.Properties"

    def __init__(
        self,
        player: str = "spotify",
        format: str = "{artist} - {title}",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.player = player
        self.format = format

    def update_callback(
        self,
        interface_name,
        changed_properties,
        invalidated_properties,
    ):
        metadata = changed_properties["Metadata"].value
        self.update(
            self.format.format(
                artist=" ".join(metadata["xesam:artist"].value),
                title=metadata["xesam:title"].value,
            )
        )

    async def setup(self, queue: Optional[asyncio.Queue] = None) -> None:
        try:
            self.bus = await dbus_aio.MessageBus().connect()
            self.introspection = await self.bus.introspect(
                self.bus_name.format(player=self.player),
                self.object_path,
            )
            self.mpris_object = self.bus.get_proxy_object(
                self.bus_name.format(player=self.player),
                self.object_path,
                self.introspection,
            )
            self.interface = self.mpris_object.get_interface(self.interface_name)
        except errors.DBusError:
            core.logger.exception(
                f"Error during {self.block_name} setup. This block is disabled!"
            )
            return

        await super().setup(queue)

    async def start(self):
        try:
            self.interface.on_properties_changed(self.update_callback)
        except Exception as e:
            core.logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e
