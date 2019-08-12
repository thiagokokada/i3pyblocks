#!/usr/bin/env python3

import asyncio

import psutil

from aio_i3status import core, test_module


def partitions(excludes=["/boot", "/nix/store"]):
    partitions = psutil.disk_partitions()
    return [p for p in partitions if p.mountpoint not in excludes]


async def main():
    runner = core.Runner()

    for partition in partitions():
        runner.register_module(
            test_module.DiskModule(path=partition.mountpoint, short_name=True)
        )
    runner.register_module(test_module.MemoryModule())
    runner.register_module(test_module.LoadModule())
    runner.register_module(test_module.TimeModule())
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
