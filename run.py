#!/usr/bin/env python3

import asyncio
import logging
import signal
from pathlib import Path

import psutil as ps

from i3pyblocks import Runner, types
from i3pyblocks.modules import aionotify, i3ipc, datetime, psutil, pulsectl, subprocess

logging.basicConfig(filename=Path.home() / ".i3pyblocks.log", level=logging.DEBUG)


def partitions(excludes=("/boot", "/nix/store")):
    partitions = ps.disk_partitions()
    return [p for p in partitions if p.mountpoint not in excludes]


async def main():
    cpu_count = ps.cpu_count()
    runner = Runner()

    runner.register_module(i3ipc.WindowTitleModule(format=" {window_title:.41s}"))
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
            icons=((0, ""), (25, ""), (50, ""), (75, "")),
        )
    )
    runner.register_module(
        psutil.CpuPercentModule(format=" {percent}%"),
        signals=(signal.SIGUSR1, signal.SIGUSR2),
    )
    runner.register_module(
        psutil.LoadAvgModule(
            format=" {load1}",
            colors=(
                (0, None),
                (cpu_count // 2, types.Color.WARN),
                (cpu_count, types.Color.URGENT),
            ),
        )
    )
    runner.register_module(
        psutil.SensorsBatteryModule(
            format_plugged=" {percent:.0f}%",
            format_unplugged="{icon} {percent:.0f}% {remaining_time}",
            format_unknown="{icon} {percent:.0f}%",
            icons=((0, ""), (10, ""), (25, ""), (50, ""), (75, "")),
        )
    )
    runner.register_module(
        subprocess.ToggleModule(
            command_state="xset q | grep -Fo 'DPMS is Enabled'",
            command_on="xset s on +dpms",
            command_off="xset s off -dpms",
            format_on="  ",
            format_off="  ",
        )
    )
    runner.register_module(
        subprocess.ShellModule(
            command="xkblayout-state print %s",
            format=" {output}",
            command_on_click=(
                (types.Mouse.SCROLL_UP, "xkblayout-state set +1"),
                (types.Mouse.SCROLL_DOWN, "xkblayout-state set -1"),
            ),
        )
    )
    runner.register_module(
        aionotify.BacklightModule(
            format=" {percent:.0f}%",
            format_no_backlight="",
            command_on_click=(
                (types.Mouse.SCROLL_UP, "light -A 5%"),
                (types.Mouse.SCROLL_DOWN, "light -U 5"),
            ),
        )
    )
    runner.register_module(
        pulsectl.PulseAudioModule(format=" {volume:.0f}%", format_mute=" mute")
    )
    runner.register_module(
        datetime.DateTimeModule(format_time=" %T", format_date=" %a, %d/%m")
    )
    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
