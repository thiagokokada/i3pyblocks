#!/usr/bin/env python3

import asyncio
import logging

import psutil as ps

from i3pyblocks import core, utils
from i3pyblocks.modules import psutil, pulsectl, time

logging.basicConfig(filename=f".i3pyblocks.log", level=logging.INFO)


def partitions(excludes=("/boot", "/nix/store")):
    partitions = ps.disk_partitions()
    return [p for p in partitions if p.mountpoint not in excludes]


async def main(loop):
    cpu_count = ps.cpu_count()
    runner = core.Runner(loop=loop)

    runner.register_module(
        psutil.NetworkSpeedModule(
            format_up=" {interface:.2s}:  {upload}  {download}",
            format_down="",
            interface_regex="en*|wl*",
        )
    )
    for partition in partitions():
        runner.register_module(
            psutil.DiskUsageModule(
                format=" {label}: {free:.1f}GiB",
                path=partition.mountpoint,
                short_label=True,
            )
        )
    runner.register_module(psutil.VirtualMemoryModule(format=" {available:.1f}GiB"))
    runner.register_module(
        psutil.SensorsTemperaturesModule(
            format="{icon} {current:.0f}°C",
            icons=[(0, ""), (25, ""), (50, ""), (75, "")],
        )
    )
    runner.register_module(psutil.CpuPercentModule(format=" {percent}%"))
    runner.register_module(
        psutil.LoadAvgModule(
            format=" {load1}",
            colors=[
                (0, None),
                (cpu_count // 2, utils.Color.WARN),
                (cpu_count, utils.Color.URGENT),
            ],
        )
    )
    runner.register_module(
        psutil.SensorsBatteryModule(
            format_plugged=" {percent:.0f}%",
            format_unplugged="{icon} {percent:.0f}% {remaining_time}",
            format_unknown="{icon} {percent:.0f}%",
            icons=[(0, ""), (10, ""), (25, ""), (50, ""), (75, "")],
        )
    )
    runner.register_module(
        pulsectl.PulseAudioModule(format=" {volume:.0f}%", format_mute=" mute")
    )
    runner.register_module(
        time.LocalTimeModule(format_time=" %T", format_date=" %a, %d/%m")
    )
    await runner.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
