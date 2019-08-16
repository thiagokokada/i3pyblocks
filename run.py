#!/usr/bin/env python3

import asyncio
import logging

import psutil

from i3pyblocks import core, modules

logging.basicConfig(filename=f".i3pyblocks.log", level=logging.INFO)


def partitions(excludes=["/boot", "/nix/store"]):
    partitions = psutil.disk_partitions()
    return [p for p in partitions if p.mountpoint not in excludes]


async def main(loop):
    runner = core.Runner(loop=loop)

    runner.register_module(modules.psutil.NetworkSpeedModule(separator=False))
    runner.register_module(modules.psutil.TemperatureModule(separator=False))
    for partition in partitions():
        runner.register_module(
            modules.psutil.DiskModule(
                path=partition.mountpoint, short_label=True, separator=False
            )
        )
    runner.register_module(modules.psutil.MemoryModule(separator=False))
    runner.register_module(modules.psutil.LoadModule(separator=False))
    runner.register_module(modules.psutil.BatteryModule(separator=False))
    runner.register_module(modules.LocalTimeModule(separator=False))
    await runner.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
