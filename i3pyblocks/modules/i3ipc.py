import asyncio

from i3ipc import Event
from i3ipc.aio import Connection

from i3pyblocks import core, modules


class WindowTitleModule(modules.Module):
    def __init__(self, format: str = "{window_title:.81s}", **kwargs):
        super().__init__(**kwargs)
        self.format = format

    async def clear_title(self, *_):
        self.update()

    async def update_title(self, connection: Connection, *_):
        tree = await connection.get_tree()
        window = tree.find_focused()

        self.update(self.format.format(window_title=window.name))

    async def start(self, queue: asyncio.Queue = None) -> None:
        await super().start(queue)

        # https://git.io/Jft7j
        connection = Connection(auto_reconnect=True)
        await connection.connect()

        connection.on(Event.WORKSPACE_FOCUS, self.clear_title)
        connection.on(Event.WINDOW_CLOSE, self.clear_title)
        connection.on(Event.WINDOW_TITLE, self.update_title)
        connection.on(Event.WINDOW_FOCUS, self.update_title)

        try:
            await self.update_title(connection)
            await connection.main()
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.update(f"Exception in {self.name}: {e}", urgent=True)
