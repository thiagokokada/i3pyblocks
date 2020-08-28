import datetime
import re
from typing import Optional, Tuple

import psutil
from psutil._common import bytes2human

from i3pyblocks import modules, utils, types


class CpuPercentModule(modules.PollingModule):
    def __init__(
        self,
        format: str = "C: {percent}%",
        colors: types.Dictable = (
            (0, types.Color.NEUTRAL),
            (75, types.Color.WARN),
            (90, types.Color.URGENT),
        ),
        sleep: int = 5,
        *,
        _psutil=psutil,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = dict(colors)
        self.psutil = _psutil

    async def run(self) -> None:
        percent = self.psutil.cpu_percent(interval=None)

        color = utils.calculate_threshold(self.colors, percent)

        self.update(self.format.format(percent=percent), color=color)


class DiskUsageModule(modules.PollingModule):
    def __init__(
        self,
        format: str = "{label}: {free:.1f}GiB",
        colors: types.Dictable = (
            (0, types.Color.NEUTRAL),
            (75, types.Color.WARN),
            (90, types.Color.URGENT),
        ),
        icons: types.Dictable = (
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ),
        divisor: int = types.IECUnit.GiB,
        sleep: int = 5,
        path: str = "/",
        short_label: bool = False,
        *,
        _psutil=psutil,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = dict(colors)
        self.icons = dict(icons)
        self.divisor = divisor
        self.path = path
        if short_label:
            self.label = self._get_short_label(self.path)
        else:
            self.label = self.path
        self.psutil = _psutil

    def _convert(self, dividend: float) -> float:
        return dividend / self.divisor

    def _get_short_label(self, path: str) -> str:
        return "/" + "/".join(x[0] for x in self.path.split("/") if x)

    async def run(self) -> None:
        disk = self.psutil.disk_usage(self.path)

        color = utils.calculate_threshold(self.colors, disk.percent)
        icon = utils.calculate_threshold(self.icons, disk.percent)

        self.update(
            self.format.format(
                label=self.label,
                total=self._convert(disk.total),
                used=self._convert(disk.used),
                free=self._convert(disk.free),
                percent=disk.percent,
                icon=icon,
            ),
            color=color,
        )


class LoadAvgModule(modules.PollingModule):
    def __init__(
        self,
        format: str = "L: {load1}",
        colors: types.Dictable = (
            (0, types.Color.NEUTRAL),
            (2, types.Color.WARN),
            (4, types.Color.URGENT),
        ),
        sleep: int = 5,
        *,
        _psutil=psutil,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = dict(colors)
        self.psutil = _psutil

    async def run(self) -> None:
        load1, load5, load15 = self.psutil.getloadavg()

        color = utils.calculate_threshold(self.colors, load1)

        self.update(
            self.format.format(load1=load1, load5=load5, load15=load15), color=color
        )


class NetworkSpeedModule(modules.PollingModule):
    def __init__(
        self,
        format_up: str = "{interface}:  U {upload} D {download}",
        format_down: str = "NO NETWORK",
        colors: types.Dictable = (
            (0, types.Color.NEUTRAL),
            (2 * types.IECUnit.MiB, types.Color.WARN),
            (5 * types.IECUnit.MiB, types.Color.URGENT),
        ),
        interface_regex: str = "en*|eth*|ppp*|sl*|wl*|ww*",
        sleep: int = 3,
        *,
        _psutil=psutil,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format_up = format_up
        self.format_down = format_down
        self.colors = dict(colors)
        self.interface_regex = re.compile(interface_regex)
        self.psutil = _psutil
        self.previous = self.psutil.net_io_counters(pernic=True)

    def _find_interface(self) -> Optional[str]:
        interfaces = self.psutil.net_if_stats()

        for interface, stats in interfaces.items():
            if stats.isup and self.interface_regex.match(interface):
                return interface

        return None

    def _calculate_speed(self, previous, now) -> Tuple[float, float]:
        upload = (now.bytes_sent - previous.bytes_sent) / self.sleep
        download = (now.bytes_recv - previous.bytes_recv) / self.sleep

        return upload, download

    async def run(self) -> None:
        interface = self._find_interface()

        if not interface:
            self.update(self.format_down, color=types.Color.URGENT)
            return

        now = self.psutil.net_io_counters(pernic=True)

        try:
            upload, download = self._calculate_speed(
                self.previous[interface], now[interface]
            )
        except KeyError:
            # When the interface does not exist in self.previous, we will get a
            # KeyError. In this case, just set upload and download to 0.
            upload, download = 0, 0

        color = utils.calculate_threshold(self.colors, max(upload, download))

        self.update(
            self.format_up.format(
                upload=bytes2human(upload),
                download=bytes2human(download),
                interface=interface,
            ),
            color=color,
        )

        self.previous = now


class SensorsBatteryModule(modules.PollingModule):
    def __init__(
        self,
        format_plugged: str = "B: PLUGGED {percent:.0f}%",
        format_unplugged: str = "B: {icon} {percent:.0f}% {remaining_time}",
        format_unknown: str = "B: {icon} {percent:.0f}%",
        colors: types.Dictable = (
            (0, types.Color.URGENT),
            (10, types.Color.WARN),
            (25, types.Color.NEUTRAL),
        ),
        icons: types.Dictable = (
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ),
        sleep=5,
        *,
        _psutil=psutil,
        **kwargs,
    ):
        super().__init__(sleep=sleep, **kwargs)
        self.format_plugged = format_plugged
        self.format_unplugged = format_unplugged
        self.format_unknown = format_unknown
        self.colors = dict(colors)
        self.icons = dict(icons)
        self.psutil = _psutil

    async def run(self):
        battery = self.psutil.sensors_battery()

        if not battery:
            return

        color = utils.calculate_threshold(self.colors, battery.percent)
        icon = utils.calculate_threshold(self.icons, battery.percent)

        if (
            battery.power_plugged
            or battery.secsleft == self.psutil.POWER_TIME_UNLIMITED
        ):
            self.format = self.format_plugged
        else:
            if battery.secsleft == psutil.POWER_TIME_UNKNOWN:
                self.format = self.format_unknown
            else:
                self.format = self.format_unplugged

        self.update(
            self.format.format(
                percent=battery.percent,
                remaining_time=(datetime.timedelta(seconds=battery.secsleft)),
                icon=icon,
            ),
            color=color,
        )


class SensorsTemperaturesModule(modules.PollingModule):
    def __init__(
        self,
        format: str = "T: {current:.0f}°C",
        colors: types.Dictable = (
            (0, types.Color.NEUTRAL),
            (60, types.Color.WARN),
            (85, types.Color.URGENT),
        ),
        icons: types.Dictable = (
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ),
        fahrenheit: bool = False,
        sensor: str = None,
        sleep: int = 5,
        *,
        _psutil=psutil,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = dict(colors)
        self.icons = dict(icons)
        self.fahrenheit = fahrenheit
        self.psutil = _psutil
        if sensor:
            self.sensor = sensor
        else:
            self.sensor = next(iter(self.psutil.sensors_temperatures()))

    async def run(self) -> None:
        temperatures = self.psutil.sensors_temperatures(self.fahrenheit)[self.sensor]
        temperature = temperatures[0]

        color = utils.calculate_threshold(self.colors, temperature.current)
        icon = utils.calculate_threshold(self.icons, temperature.current)

        self.update(
            self.format.format(
                label=temperature.label,
                current=temperature.current,
                high=temperature.high,
                critical=temperature.critical,
                icon=icon,
            ),
            color=color,
        )


class VirtualMemoryModule(modules.PollingModule):
    def __init__(
        self,
        format: str = "M: {available:.1f}GiB",
        colors: types.Dictable = (
            (0, types.Color.NEUTRAL),
            (75, types.Color.WARN),
            (90, types.Color.URGENT),
        ),
        icons: types.Dictable = (
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ),
        divisor: int = types.IECUnit.GiB,
        sleep: int = 3,
        *,
        _psutil=psutil,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = dict(colors)
        self.icons = dict(icons)
        self.divisor = divisor
        self.psutil = _psutil

    def _convert(self, dividend: float) -> float:
        return dividend / self.divisor

    async def run(self) -> None:
        memory = self.psutil.virtual_memory()

        color = utils.calculate_threshold(self.colors, memory.percent)
        icon = utils.calculate_threshold(self.icons, memory.percent)

        self.update(
            self.format.format(
                total=self._convert(memory.total),
                available=self._convert(memory.available),
                used=self._convert(memory.used),
                free=self._convert(memory.free),
                percent=memory.percent,
                icon=icon,
            ),
            color=color,
        )
