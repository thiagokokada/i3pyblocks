import asyncio
from asyncio import subprocess

from i3pyblocks import modules


class ShellModule(modules.PollingModule):
    def __init__(
        self, command: str, format: str = "{output}", sleep: int = 1, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.sleep = sleep
        self.format = format
        self.command = command

    async def click_handler(self, *_, **__) -> None:
        # TODO: Support running commands according to mouse clicks
        await self.run()

    async def signal_handler(self, *_, **__) -> None:
        # TODO: Support reacting to signal handlers?
        await self.run()

    async def run(self) -> None:
        process = await asyncio.create_subprocess_shell(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        output = stdout.decode().strip()
        output_err = stderr.decode().strip()

        self.update(self.format.format(output=output, output_err=output_err))
