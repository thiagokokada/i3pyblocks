"""Blocks based on `asyncio.subprocess`_

This is a collection of Blocks based on ``asyncio.subprocess``, allowing you
to run an external program, parse its output and show it in i3pyblocks.

All Blocks in this module are based on ``PollingBlock``, since it is more
difficult to have proper event based updates when coordinating subprocess.
There is some alternatives that to try in the future, for example using inotify
or dbus based approaches.

.. _asyncio.subprocess:
    https://docs.python.org/3/library/asyncio-subprocess.html
"""
from asyncio import subprocess

from i3pyblocks import blocks, types
from i3pyblocks._internal import utils


class ShellBlock(blocks.PollingBlock):
    r"""Block that shows the result of a command running in shell.

    :param command: Command to be run. This will be parsed by shell, so it can
        also be multiple arbitrary commands separated by newlines, or multiple
        commands connected by pipes.

    :param format: Format string to shown. Supports both ``{output}`` (stdout)
        and ``{output_err}`` (stderr) placeholders.

    :param command_on_click: Dictable with commands to be called when the user
        interacts with mouse inside this block. After running this Block will
        be updated. Can be useful to change the keyboard layout for example.

    :param \*\*kwargs:
        Extra arguments to be passed to ``PollingBlock`` class.
    """

    def __init__(
        self,
        command: str,
        format: str = "{output}",
        command_on_click: types.Dictable = (
            (types.MouseButton.LEFT_BUTTON, None),
            (types.MouseButton.MIDDLE_BUTTON, None),
            (types.MouseButton.RIGHT_BUTTON, None),
            (types.MouseButton.SCROLL_UP, None),
            (types.MouseButton.SCROLL_DOWN, None),
        ),
        color_by_returncode: types.Dictable = (),
        sleep: int = 1,
        *,
        _utils=utils,
        **kwargs
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.command = command
        self.command_on_click = dict(command_on_click)
        self.color_by_returncode = dict(color_by_returncode)
        self.utils = _utils

    async def click_handler(self, button: int, **_kwargs) -> None:
        command = self.command_on_click.get(button)

        if not command:
            return

        await self.utils.shell_run(command)
        await self.run()

    async def run(self) -> None:
        stdout, stderr, process = await utils.shell_run(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        color = self.color_by_returncode.get(process.returncode)

        output = stdout.decode().strip()
        output_err = stderr.decode().strip()

        self.update(
            self.format.format(output=output, output_err=output_err), color=color
        )


class ToggleBlock(blocks.PollingBlock):
    r"""Block that shows a toggle on or off accordingly to command's output.

    This block output is determined by ``command_state``. When the command
    outputs something in stdout, this is interpreted as ON, while when the
    command outputs nothing in stdout, this is interpreted as OFF.

    :param command_state: Command to be run to determine state. This will be
        parsed by shell, so it can also be multiple arbitrary commands
        separated by newlines, or multiple commands connected by pipes.

    :param command_on: Command to be called when the current state is OFF, so
        it can be turned to ON.

    :param command_off: Command to be called when the current state is ON, so
        it can be turned to OFF.

    :param format_on: Format string to be shown when state is ON.

    :param format_off: Format string to be shown when state is OFF.

    :param sleep: Sleep in seconds between each call to ``run()``.

    :param \*\*kwargs: Extra arguments to be passed to ``PollingBlock`` class.
    """

    def __init__(
        self,
        command_state: str,
        command_on: str,
        command_off: str,
        format_on: str = "ON",
        format_off: str = "OFF",
        sleep: int = 1,
        *,
        _utils=utils,
        **kwargs
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.command_state = command_state
        self.command_on = command_on
        self.command_off = command_off
        self.format_on = format_on
        self.format_off = format_off
        self.utils = _utils

    async def get_state(self) -> bool:
        stdout, _, _ = await utils.shell_run(self.command_state, stdout=subprocess.PIPE)

        output = stdout.decode().strip()

        return bool(output)

    async def click_handler(self, **_kwargs) -> None:
        state = await self.get_state()

        if not state:
            command = self.command_on
        else:
            command = self.command_off

        await self.utils.shell_run(command)
        await self.run()

    async def run(self) -> None:
        state = await self.get_state()

        self.update(self.format_on if state else self.format_off)
