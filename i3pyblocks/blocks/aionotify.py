import abc
import asyncio
from pathlib import Path
from typing import Optional, Union

import aionotify

from i3pyblocks import core, blocks, types, utils


class FileWatcherBlock(blocks.Block):
    def __init__(
        self,
        path: Union[Path, str, None],
        flags: Optional[aionotify.Flags] = None,
        format_file_not_found: str = "File not found {path}",
        *,
        _aionotify=aionotify,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.flags = flags
        self.path = Path(path) if path else None
        self.format_file_not_found = format_file_not_found
        self.aionotify = _aionotify

    @abc.abstractmethod
    async def run(self) -> None:
        pass

    async def start(self) -> None:
        if not self.path or not self.path.exists():
            self.abort(full_text=self.format_file_not_found.format(path=self.path))
            return

        watcher = self.aionotify.Watcher()
        watcher.watch(str(self.path), flags=self.flags)

        try:
            loop = asyncio.get_running_loop()
            await watcher.setup(loop)
            while True:
                await self.run()
                self.event = await watcher.get_event()
        except Exception as e:
            core.logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e


class BacklightBlock(FileWatcherBlock):
    def __init__(
        self,
        format: str = "{percent:.0f}%",
        format_no_backlight: str = "No backlight found",
        base_path: Union[Path, str] = "/sys/class/backlight/",
        device_glob: Optional[str] = "*",
        command_on_click: types.Dictable = (
            (types.MouseButton.LEFT_BUTTON, None),
            (types.MouseButton.MIDDLE_BUTTON, None),
            (types.MouseButton.RIGHT_BUTTON, None),
            (types.MouseButton.SCROLL_UP, None),
            (types.MouseButton.SCROLL_DOWN, None),
        ),
        *,
        _aionotify=aionotify,
        _utils=utils,
        **kwargs,
    ) -> None:
        self.base_path = Path(base_path)

        if device_glob:
            self.device_path = next(self.base_path.glob(device_glob), None)
        else:
            self.device_path = self.base_path

        self.format = format
        self.format_no_backlight = format_no_backlight
        self.command_on_click = dict(command_on_click)

        if self.device_path:
            super().__init__(
                path=self.device_path / "brightness",
                flags=_aionotify.Flags.MODIFY,
                _aionotify=_aionotify,
                **kwargs,
            )
        else:
            super().__init__(path=None, format_file_not_found=format_no_backlight)

        self.utils = _utils

    async def click_handler(self, button: int, *_, **__) -> None:
        command = self.command_on_click.get(button)

        if not command:
            return

        await self.utils.shell_run(command)

    def _get_max_brightness(self) -> int:
        if self.base_path:
            with open(self.device_path / "max_brightness") as f:
                return int(f.readline().strip())
        else:
            return 1

    def _get_brightness(self) -> int:
        if self.path:
            with open(self.device_path / "brightness") as f:
                return int(f.readline().strip())
        else:
            return 0

    async def run(self) -> None:
        brightness = self._get_brightness()
        max_brightness = self._get_max_brightness()
        percent = (brightness / max_brightness) * 100

        self.update(
            self.format.format(
                brightness=brightness,
                max_brightness=max_brightness,
                percent=percent,
            )
        )
