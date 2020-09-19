"""Blocks related to monitoring file changes, based on `aionotify`_.

This module contains FileWatcherBlock, an abstract, highly efficient Block to
show the contents of an arbitrary file. It uses ``aionotify``, that itself is
implement using Linux's `inotify`_, so this Block is only updated when the
event that we registered in this Block occurs in the target file.

For an example implementation, take BacklightBlock. It watches for changes in
``/sys/class/backlight/*/brightness`` file. So only when the brightness is
changed, this Block is updated.

.. _aionotify:
    https://github.com/rbarrois/aionotify
.. _inotify:
    https://en.wikipedia.org/wiki/Inotify
"""


import abc
import asyncio
import signal
from pathlib import Path
from typing import List, Mapping, Optional, Union

import aionotify

from i3pyblocks import blocks, logger, types
from i3pyblocks._internal import models, subprocess


class FileWatcherBlock(blocks.Block):
    r"""File watcher Block.

    A highly efficient Block to watch for events that happen in a file.

    By default, a click or a signal event will refresh the contents of this
    Block.

    You must not instantiate this class directly, instead you should
    subclass it and implement ``run()`` method first.

    :param path: The file path to watch for events.

    :param flags: The modification flags to be watched. A list of flags can be
        found `in aionotify repo`_. Multiple flags can be passed to, for
        example::

            from aionotify import Flags

            FileWatcherBlock(
                path="/some/path",
                flags=Flags.MODIFY | Flags.CREATE,
            )

    :param format_file_not_found: Format string to shown when the file in passed
        in ``path`` is not found.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.Block` class.

    .. _in aionotify repo:
        https://github.com/rbarrois/aionotify/blob/master/aionotify/enums.py
    """

    def __init__(
        self,
        path: Union[Path, str, None],
        flags: Optional[aionotify.Flags] = None,
        format_file_not_found: str = "File not found {path}",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.flags = flags
        self.path = Path(path) if path else None
        self.format_file_not_found = format_file_not_found

    async def click_handler(
        self,
        *,
        x: int,
        y: int,
        button: int,
        relative_x: int,
        relative_y: int,
        width: int,
        height: int,
        modifiers: List[Optional[str]],
    ) -> None:
        await self.run()

    async def signal_handler(self, *, sig: signal.Signals) -> None:
        await self.run()

    @abc.abstractmethod
    async def run(self) -> None:
        pass

    async def start(self) -> None:
        if not self.path or not self.path.exists():
            self.abort(full_text=self.format_file_not_found.format(path=self.path))
            return

        watcher = aionotify.Watcher()
        watcher.watch(str(self.path), flags=self.flags)

        try:
            loop = asyncio.get_event_loop()
            await watcher.setup(loop)
            while True:
                await self.run()
                self.event = await watcher.get_event()
        except Exception as e:
            logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e


class BacklightBlock(FileWatcherBlock):
    r"""Backlight Block.

    Based on `sysfs backlight interface`_.

    :param format: Format string to shown. Supports the following placeholders:

          - ``{brightness}``: Current brightness of display
          - ``{max_brightness}``: Max brightness supported by display
          - ``{percent}``: Percentage between current and max display
            brightness

    :param base_path: The path where available backlights will be searched.

    :param device_glob: `File glob`_ that will be used to search the device
        inside the ``base_path``. By default it tries to find anything, but if
        for some reason you want a specific device you can just use
        ``device_name`` here instead.

    :param command_on_click: Mapping with commands to be called when the user
        interacts with mouse inside this block. Can be useful to adjust the
        backlight using scroll, for example.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.FileWatcherBlock` class.

    .. _sysfs backlight interface:
        https://www.kernel.org/doc/Documentation/ABI/stable/sysfs-class-backlight
    .. _File glob:
        https://docs.python.org/3/library/glob.html
    """

    def __init__(
        self,
        format: str = "{percent:.0f}%",
        format_no_backlight: str = "No backlight",
        base_path: Union[Path, str] = "/sys/class/backlight/",
        device_glob: Optional[str] = "*",
        command_on_click: Mapping[int, Optional[models.CommandArgs]] = {
            types.MouseButton.LEFT_BUTTON: None,
            types.MouseButton.MIDDLE_BUTTON: None,
            types.MouseButton.RIGHT_BUTTON: None,
            types.MouseButton.SCROLL_UP: None,
            types.MouseButton.SCROLL_DOWN: None,
        },
        **kwargs,
    ) -> None:
        self.base_path = Path(base_path)

        if device_glob:
            self.device_path = next(self.base_path.glob(device_glob), None)
        else:
            self.device_path = self.base_path

        self.format = format
        self.format_no_backlight = format_no_backlight
        self.command_on_click = command_on_click

        if self.device_path:
            super().__init__(
                path=self.device_path / "brightness",
                flags=aionotify.Flags.MODIFY,
                **kwargs,
            )
        else:
            super().__init__(path=None, format_file_not_found=format_no_backlight)

    async def click_handler(self, button: int, **_kwargs) -> None:
        command = self.command_on_click.get(button)

        if not command:
            return

        await subprocess.arun(command)

    def _get_max_brightness(self) -> int:
        if self.device_path:
            with open(self.device_path / "max_brightness") as f:
                return int(f.readline().strip())
        else:
            return 1

    def _get_brightness(self) -> int:
        if self.device_path:
            # TODO: Maybe use actual_brightness here instead?
            with open(self.device_path / "brightness") as f:
                return int(f.readline().strip())
        else:
            return 0

    async def run(self) -> None:
        brightness = self._get_brightness()
        max_brightness = self._get_max_brightness()
        percent = (brightness / max_brightness) * 100

        self.update(
            self.ex_format(
                self.format,
                brightness=brightness,
                max_brightness=max_brightness,
                percent=percent,
            )
        )
