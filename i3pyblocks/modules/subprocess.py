import asyncio
from asyncio import subprocess

from i3pyblocks import modules, types


class ShellModule(modules.PollingModule):
    def __init__(
        self,
        command: str,
        format: str = "{output}",
        command_on_click: types.Items = (
            (types.Mouse.LEFT_BUTTON, None),
            (types.Mouse.MIDDLE_BUTTON, None),
            (types.Mouse.RIGHT_BUTTON, None),
            (types.Mouse.SCROLL_UP, None),
            (types.Mouse.SCROLL_DOWN, None),
        ),
        color_by_returncode: types.Items = (),
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
