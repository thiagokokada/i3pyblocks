import abc
import asyncio
import glob
import os

import aionotify

from i3pyblocks import core, modules, types, utils


class FileWatcherModule(modules.Module):
    def __init__(
        self, path: str, flags: aionotify.Flags, *, _aionotify=aionotify, **kwargs
    ):
        super().__init__(**kwargs)
        self.flags = flags
        self.path = path
        self.aionotify = _aionotify

    @abc.abstractmethod
    async def run(self) -> None:
        pass

    async def start(self, queue: asyncio.Queue = None) -> None:
        await super().start(queue)

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
            self.update(f"Exception in {self.name}: {e}", urgent=True)


class BacklightModule(FileWatcherModule):
    def __init__(
        self,
        format: str = "{percent:.0f}%",
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
        self.base_path = next(glob.iglob(path))
        self.brightness_path = os.path.join(self.base_path, "brightness")
        self.max_brightness_path = os.path.join(self.base_path, "max_brightness")
        super().__init__(
            path=self.brightness_path,
            flags=_aionotify.Flags.MODIFY,
            _aionotify=_aionotify,
            **kwargs,
        )
        self.format = format
        self.command_on_click = dict(command_on_click)
        self.utils = _utils

    async def click_handler(self, button: int, *_, **__) -> None:
        command = self.command_on_click.get(button)

        if not command:
            return

        await self.utils.shell_run(command)

    def _get_max_brightness(self) -> int:
        with open(self.max_brightness_path) as f:
            return int(f.readline().strip())

    def _get_brightness(self) -> int:
        with open(self.brightness_path) as f:
            return int(f.readline().strip())

    async def run(self) -> None:
        brightness = self._get_brightness()
        max_brightness = self._get_max_brightness()
        percent = (brightness / max_brightness) * 100

        self.update(
            self.format.format(
                brightness=brightness, max_brightness=max_brightness, percent=percent,
            )
        )
