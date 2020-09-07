import asyncio

from i3pyblocks import Runner
from i3pyblocks.blocks import basic, datetime

async def main():
    runner = Runner()
    runner.register_block(basic.TextBlock("Hello World!"))
    runner.register_block(datetime.DateTimeBlock())
    await runner.start()

asyncio.run(main())
