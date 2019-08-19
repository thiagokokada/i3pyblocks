import datetime
from typing import List, Optional, Tuple

import psutil
from psutil._common import bytes2human

from i3pyblocks import core, utils


class CpuPercentModule(core.PollingModule):
    def __init__(
        self,
        format: str = "C: {percent}%",
        colors: utils.Items = [
            (0, utils.Color.NEUTRAL),
            (75, utils.Color.WARN),
            (90, utils.Color.URGENT),
        ],
        sleep: int = 5,
        **kwargs,
    ) -> None:
        self.format = format
        self.colors = colors
        super().__init__(sleep=sleep, **kwargs)

    def run(self) -> None:
        percent = psutil.cpu_percent(interval=None)

        color = utils.calculate_threshold(self.colors, percent)

        self.update(self.format.format(percent=percent), color=color)


class DiskUsageModule(core.PollingModule):
    def __init__(
        self,
        format: str = "{label}: {free:.1f}GiB",
        colors: utils.Items = [
            (0, utils.Color.NEUTRAL),
            (75, utils.Color.WARN),
            (90, utils.Color.URGENT),
        ],
        icons: utils.Items = [
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ],
        divisor: int = utils.IECUnits.GiB,
        sleep: int = 5,
        path: str = "/",
        short_label: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, instance=path, **kwargs)
        self.format = format
        self.colors = colors
        self.icons = icons
        self.divisor = divisor
        self.path = path
        if short_label:
            self.label = self._get_short_label(self.path)
        else:
            self.label = self.path

    def _convert(self, dividend: float) -> float:
        return dividend / self.divisor

    def _get_short_label(self, path: str) -> str:
        return "/" + "/".join(x[0] for x in self.path.split("/") if x)

    def run(self) -> None:
        disk = psutil.disk_usage(self.path)

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


class LoadAvgModule(core.PollingModule):
    def __init__(
        self,
        format: str = "L: {load1}",
        colors: utils.Items = [
            (0, utils.Color.NEUTRAL),
            (2, utils.Color.WARN),
            (4, utils.Color.URGENT),
        ],
        sleep: int = 5,
        **kwargs,
    ) -> None:
        self.format = format
        self.colors = colors
        super().__init__(sleep=sleep, **kwargs)

    def run(self) -> None:
        load1, load5, load15 = psutil.getloadavg()

        color = utils.calculate_threshold(self.colors, load1)

        self.update(
            self.format.format(load1=load1, load5=load5, load15=load15), color=color
        )


class NetworkSpeedModule(core.PollingModule):
    def __init__(
        self,
        format_up: str = "{iface}:  U {upload} D {download}",
        format_down: str = "NO NETWORK",
        colors: utils.Items = [
            (0, utils.Color.NEUTRAL),
            (2 * utils.IECUnits.MiB, utils.Color.WARN),
            (5 * utils.IECUnits.MiB, utils.Color.URGENT),
        ],
        ignored_interfaces: List[str] = ["lo"],
        sleep: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format_up = format_up
        self.format_down = format_down
        self.colors = colors
        self.ignored_interfaces = ignored_interfaces
        self.previous = psutil.net_io_counters(pernic=True)

    def _detect_active_iface(self) -> Optional[str]:
        if_stats = psutil.net_if_stats()

        for iface, stats in if_stats.items():
            if iface in self.ignored_interfaces:
                continue
            if (
                # This heuristic tries to avoid virtual interfaces like bridges
                stats.isup
                and stats.speed
                and stats.duplex is not psutil.NIC_DUPLEX_UNKNOWN
            ):
                return iface

        return None

    def _calculate_speed(self, previous, now) -> Tuple[float, float]:
        upload = (now.bytes_sent - previous.bytes_sent) / self.sleep
        download = (now.bytes_recv - previous.bytes_recv) / self.sleep

        return upload, download

    def run(self) -> None:
        iface = self._detect_active_iface()

        if not iface:
            self.update(self.format_down, color=utils.Color.URGENT)
            return

        now = psutil.net_io_counters(pernic=True)

        try:
            upload, download = self._calculate_speed(self.previous[iface], now[iface])
        except KeyError:
            # When the interface does not exist in self.previous, we will get a
            # KeyError. In this case, just set upload and download to 0.
            upload, download = 0, 0

        color = utils.calculate_threshold(self.colors, max(upload, download))

        self.update(
            self.format_up.format(
                upload=bytes2human(upload), download=bytes2human(download), iface=iface
            ),
            color=color,
        )

        self.previous = now


class SensorsBatteryModule(core.PollingModule):
    def __init__(
        self,
        format_plugged: str = "B: PLUGGED {percent:.0f}%",
        format_unplugged: str = "B: {icon} {percent:.0f}% {remaining_time}",
        format_unknown: str = "B: {icon} {percent:.0f}%",
        colors: utils.Items = [
            (0, utils.Color.URGENT),
            (10, utils.Color.WARN),
            (25, utils.Color.NEUTRAL),
        ],
        icons: utils.Items = [
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ],
        sleep=5,
        **kwargs,
    ):
        super().__init__(sleep=sleep, **kwargs)
        self.format_plugged = format_plugged
        self.format_unplugged = format_unplugged
        self.format_unknown = format_unknown
        self.colors = colors
        self.icons = icons

    def run(self):
        battery = psutil.sensors_battery()

        if not battery:
            return

        color = utils.calculate_threshold(self.colors, battery.percent)
        icon = utils.calculate_threshold(self.icons, battery.percent)

        if battery.power_plugged or battery.secsleft == psutil.POWER_TIME_UNLIMITED:
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


class SensorsTemperaturesModule(core.PollingModule):
    def __init__(
        self,
        format: str = "T: {current:.0f}°C",
        colors: utils.Items = [
            (0, utils.Color.NEUTRAL),
            (60, utils.Color.WARN),
            (85, utils.Color.URGENT),
        ],
        icons: utils.Items = [
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ],
        fahrenheit: bool = False,
        sensor: str = None,
        sleep: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = colors
        self.icons = icons
        self.fahrenheit = fahrenheit
        if sensor:
            self.sensor = sensor
        else:
            self.sensor = next(iter(psutil.sensors_temperatures()))

    def run(self) -> None:
        temperatures = psutil.sensors_temperatures(self.fahrenheit)[self.sensor]
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


class VirtualMemoryModule(core.PollingModule):
    def __init__(
        self,
        format: str = "M: {available:.1f}GiB",
        colors: utils.Items = [
            (0, utils.Color.NEUTRAL),
            (75, utils.Color.WARN),
            (90, utils.Color.URGENT),
        ],
        icons: utils.Items = [
            (0.0, "▁"),
            (12.5, "▂"),
            (25.0, "▃"),
            (37.5, "▄"),
            (50.0, "▅"),
            (62.5, "▆"),
            (75.0, "▇"),
            (87.5, "█"),
        ],
        divisor: int = utils.IECUnits.GiB,
        sleep=3,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = colors
        self.icons = icons
        self.divisor = divisor

    def _convert(self, dividend: float) -> float:
        return dividend / self.divisor

    def run(self) -> None:
        memory = psutil.virtual_memory()

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
