"""Blocks based on `i3ipc`_.

This module contains WindowTitleBlock, that uses ``i3ipc`` to show the current
window title in i3pyblocks.

Since it uses a publish/subscribe mechanism, it should be highly efficient,
only updating when it is actually needed.

.. _i3ipc:
    https://github.com/altdesktop/i3ipc-python
"""

import i3ipc
import i3ipc.aio

from i3pyblocks import blocks, core


class WindowTitleBlock(blocks.Block):
    r"""Block that shows the current window title.

    :param format: Format string to shown. Supports ``{window_title}``
        placeholder.

    :param \*\*kwargs: Extra arguments to be passed to ``Block`` class.
    """

    def __init__(
        self,
        format: str = "{window_title:.81s}",
        *,
        _i3ipc=i3ipc,
        _i3ipc_aio=i3ipc.aio,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.format = format
        self.i3ipc = _i3ipc
        self.i3ipc_aio = _i3ipc_aio

    async def clear_title(self, *_):
        self.update()

    async def update_title(self, connection, *_):
        tree = await connection.get_tree()
        window = tree.find_focused()

        self.update(self.format.format(window_title=window.name or ""))

    async def start(self) -> None:
        # https://git.io/Jft7j
        connection = self.i3ipc_aio.Connection(auto_reconnect=True)

        await connection.connect()

        connection.on(self.i3ipc.Event.WORKSPACE_FOCUS, self.clear_title)
        connection.on(self.i3ipc.Event.WINDOW_CLOSE, self.clear_title)
        connection.on(self.i3ipc.Event.WINDOW_TITLE, self.update_title)
        connection.on(self.i3ipc.Event.WINDOW_FOCUS, self.update_title)

        try:
            await self.update_title(connection)
            await connection.main()
        except Exception as e:
            core.logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e
