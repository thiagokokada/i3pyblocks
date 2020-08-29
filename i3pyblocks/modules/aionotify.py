import abc
import asyncio
import glob
import os
from typing import Optional

import aionotify

from i3pyblocks import core, modules, types, utils


class FileWatcherModule(modules.Module):
    def __init__(
        self,
        path: str,
        flags: Optional[aionotify.Flags] = None,
        format_file_not_found: str = "File not found {path}",
        *,
        _aionotify=aionotify,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.flags = flags
        self.path = path
        self.format_file_not_found = format_file_not_found
        self.aionotify = _aionotify

    @abc.abstractmethod
    async def run(self) -> None:
        pass

    async def start(self, queue: asyncio.Queue = None) -> None:
        await super().start(queue)

        if not os.path.exists(self.path):
            self.abort(full_text=self.format_file_not_found.format(path=self.path))
            return

        watcher = self.aionotify.Watcher()
        watcher.watch(self.path, flags=self.flags)

        try:
            loop = asyncio.get_running_loop()
            await watcher.setup(loop)
            while True:
                await self.run()
                self.event = await watcher.get_event()
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.abort(f"Exception in {self.name}: {e}", urgent=True)


class BacklightModule(FileWatcherModule):
    def __init__(
        self,
        format: str = "{percent:.0f}%",
        format_no_backlight: str = "No backlight found",
        path: str = "/sys/class/backlight/*",
        command_on_click: types.Dictable = (
            (types.Mouse.LEFT_BUTTON, None),
            (types.Mouse.MIDDLE_BUTTON, None),
            (types.Mouse.RIGHT_BUTTON, None),
            (types.Mouse.SCROLL_UP, None),
            (types.Mouse.SCROLL_DOWN, None),
        ),
        *,
        _aionotify=aionotify,
        _utils=utils,
        **kwargs,
    ) -> None:
        self.base_path = next(glob.iglob(path), None)
        self.format = format
        self.format_no_backlight = format_no_backlight
        self.command_on_click = dict(command_on_click)

        if self.base_path:
            super().__init__(
                path=os.path.join(self.base_path, "brightness"),
                flags=_aionotify.Flags.MODIFY,
                _aionotify=_aionotify,
                **kwargs,
            )
        else:
            super().__init__(path="", format_file_not_found=format_no_backlight)

        self.utils = _utils

    async def click_handler(self, button: int, *_, **__) -> None:
        command = self.command_on_click.get(button)

        if not command:
            return

        await self.utils.shell_run(command)

    def _get_max_brightness(self) -> int:
        if self.base_path:
            with open(os.path.join(self.base_path, "max_brightness")) as f:
                return int(f.readline().strip())
        else:
            return 1

    def _get_brightness(self) -> int:
        if self.path:
            with open(self.path) as f:
                return int(f.readline().strip())
        else:
            return 0

    async def run(self) -> None:
        brightness = self._get_brightness()
        max_brightness = self._get_max_brightness()
        percent = (brightness / max_brightness) * 100

        self.update(
            self.format.format(
                brightness=brightness, max_brightness=max_brightness, percent=percent,
            )
        )
