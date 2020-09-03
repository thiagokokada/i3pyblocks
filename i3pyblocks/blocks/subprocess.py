from asyncio import subprocess

from i3pyblocks import blocks, types, utils


class ShellBlock(blocks.PollingBlock):
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
        _utils=utils,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
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
    def __init__(
        self,
        command_state: str,
        command_on: str,
        command_off: str,
        format_on: str = "ON",
        format_off: str = "OFF",
        *,
        _utils=utils,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
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
