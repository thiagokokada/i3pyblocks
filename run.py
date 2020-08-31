#!/usr/bin/env python3

import asyncio
import logging
import signal
from pathlib import Path

import psutil as ps

from i3pyblocks import Runner, types
from i3pyblocks.blocks import aionotify, i3ipc, datetime, psutil, pulsectl, subprocess

logging.basicConfig(filename=Path.home() / ".i3pyblocks.log", level=logging.DEBUG)


def partitions(excludes=("/boot", "/nix/store")):
    partitions = ps.disk_partitions()
    return [p for p in partitions if p.mountpoint not in excludes]


async def main():
    cpu_count = ps.cpu_count()
    runner = Runner()

    runner.register_block(i3ipc.WindowTitleBlock(format=" {window_title:.41s}"))
    runner.register_block(
        psutil.NetworkSpeedBlock(
            format_up=" {interface:.2s}:  {upload}  {download}",
            format_down="",
            interface_regex="en*|wl*",
        )
    )
    for partition in partitions():
        runner.register_block(
            psutil.DiskUsageBlock(
                format=" {label}: {free:.1f}GiB",
                path=partition.mountpoint,
                short_label=True,
            )
        )
    runner.register_block(psutil.VirtualMemoryBlock(format=" {available:.1f}GiB"))
    runner.register_block(
        psutil.SensorsTemperaturesBlock(
            format="{icon} {current:.0f}°C",
            icons=((0, ""), (25, ""), (50, ""), (75, "")),
        )
    )
    runner.register_block(
        psutil.CpuPercentBlock(format=" {percent}%"),
        signals=(signal.SIGUSR1, signal.SIGUSR2),
    )
    runner.register_block(
        psutil.LoadAvgBlock(
            format=" {load1}",
            colors=(
                (0, None),
                (cpu_count // 2, types.Color.WARN),
                (cpu_count, types.Color.URGENT),
            ),
        )
    )
    runner.register_block(
        psutil.SensorsBatteryBlock(
            format_plugged=" {percent:.0f}%",
            format_unplugged="{icon} {percent:.0f}% {remaining_time}",
            format_unknown="{icon} {percent:.0f}%",
            icons=((0, ""), (10, ""), (25, ""), (50, ""), (75, "")),
        )
    )
    runner.register_block(
        subprocess.ToggleBlock(
            command_state="xset q | grep -Fo 'DPMS is Enabled'",
            command_on="xset s on +dpms",
            command_off="xset s off -dpms",
            format_on="  ",
            format_off="  ",
        )
    )
    runner.register_block(
        subprocess.ShellBlock(
            command="xkblayout-state print %s",
            format=" {output}",
            command_on_click=(
                (types.MouseButton.SCROLL_UP, "xkblayout-state set +1"),
                (types.MouseButton.SCROLL_DOWN, "xkblayout-state set -1"),
            ),
        )
    )
    runner.register_block(
        aionotify.BacklightBlock(
            format=" {percent:.0f}%",
            format_no_backlight="",
            command_on_click=(
                (types.MouseButton.SCROLL_UP, "light -A 5%"),
                (types.MouseButton.SCROLL_DOWN, "light -U 5"),
            ),
        )
    )
    runner.register_block(
        pulsectl.PulseAudioBlock(format=" {volume:.0f}%", format_mute=" mute")
    )
    runner.register_block(
        datetime.DateTimeBlock(format_time=" %T", format_date=" %a, %d/%m")
    )
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
