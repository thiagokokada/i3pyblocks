#!/usr/bin/env python3

import asyncio

import psutil

from aio_i3status import core, modules


def partitions(excludes=["/boot", "/nix/store"]):
    partitions = psutil.disk_partitions()
    return [p for p in partitions if p.mountpoint not in excludes]


async def main():
    runner = core.Runner()

    runner.register_module(modules.NetworkModule())
    runner.register_module(modules.TemperatureModule())
    for partition in partitions():
        runner.register_module(
            modules.DiskModule(path=partition.mountpoint, short_name=True)
        )
    runner.register_module(modules.MemoryModule())
    runner.register_module(modules.LoadModule())
    runner.register_module(modules.BatteryModule())
    runner.register_module(modules.LocalTimeModule())
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
