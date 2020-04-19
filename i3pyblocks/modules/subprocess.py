import asyncio
from asyncio import subprocess

from i3pyblocks import modules, types


class ShellModule(modules.PollingModule):
    def __init__(
        self,
        command: str,
        format: str = "{output}",
        command_on_click: types.Dictable = (
            (types.Mouse.LEFT_BUTTON, None),
            (types.Mouse.MIDDLE_BUTTON, None),
            (types.Mouse.RIGHT_BUTTON, None),
            (types.Mouse.SCROLL_UP, None),
            (types.Mouse.SCROLL_DOWN, None),
        ),
        color_by_returncode: types.Dictable = (),
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.format = format
        self.command = command
        self.command_on_click = dict(command_on_click)
        self.color_by_returncode = dict(color_by_returncode)

    async def click_handler(self, button: int, *_, **__) -> None:
        command = self.command_on_click.get(button)

        if not command:
            return

        process = await asyncio.create_subprocess_shell(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.wait()

        await self.run()

    async def run(self) -> None:
        process = await asyncio.create_subprocess_shell(
            self.command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        color = self.color_by_returncode.get(process.returncode)

        output = stdout.decode().strip()
        output_err = stderr.decode().strip()

        self.update(
            self.format.format(output=output, output_err=output_err), color=color
        )


class ToggleModule(modules.PollingModule):
    def __init__(
        self,
        command_state: str,
        command_on: str,
        command_off: str,
        format_on: str = "ON",
        format_off: str = "OFF",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.command_state = command_state
        self.command_on = command_on
        self.command_off = command_off
        self.format_on = format_on
        self.format_off = format_off

    async def get_state(self) -> bool:
        process = await asyncio.create_subprocess_shell(
            self.command_state,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, _ = await process.communicate()

        output = stdout.decode().strip()

        return bool(output)

    async def click_handler(self, *_, **__) -> None:
        state = await self.get_state()

        if not state:
            command = self.command_on
        else:
            command = self.command_off

        process = await asyncio.create_subprocess_shell(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.wait()

        await self.run()

    async def run(self) -> None:
        state = await self.get_state()

        self.update(self.format_on if state else self.format_off)
