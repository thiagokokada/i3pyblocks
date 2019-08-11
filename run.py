#!/usr/bin/env python3

import asyncio

from aio_i3status import core, test_module


async def main():
    runner = core.Runner()
    runner.register_module(test_module.TestModule())
    runner.register_module(test_module.AnotherTestModule())
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
