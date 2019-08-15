import datetime

import psutil
from psutil._common import bytes2human

from i3pyblocks.core import PollingModule


class BatteryModule(PollingModule):
    def __init__(self, sleep=5, **kwargs):
        super().__init__(sleep=sleep, **kwargs)

    def format_battery(self, percent):
        if percent > 75:
            return "", None
        elif percent > 50:
            return "", None
        elif percent > 25:
            return "", None
        elif percent > 10:
            return "", Color.WARN
        else:
            return "", Color.URGENT

    def run(self):
        battery = psutil.sensors_battery()

        if not battery:
            return

        percent = battery.percent
        remaining_time = battery.secsleft
        remaining_time_formatted = datetime.timedelta(seconds=battery.secsleft)
        plugged = battery.power_plugged
        icon, color = self.format_battery(percent)

        if plugged:
            self.update(f" {percent:.0f}%")
        elif remaining_time != psutil.POWER_TIME_UNKNOWN:
            self.update(
                f"{icon} {percent:.0f}% {remaining_time_formatted}", color=color
            )
        else:
            self.update(f"{icon} {percent:.0f}%", color=color)


class DiskModule(PollingModule):
    def __init__(self, sleep=5, path="/", short_label=False, **kwargs):
        super().__init__(sleep=sleep, instance=path, **kwargs)
        self.path = path
        if short_label:
            self.label = "/" + "/".join(x[0] for x in self.path.split("/") if x)
        else:
            self.label = self.path

    def run(self):
        free = psutil.disk_usage("/").free
        free_in_gib = free / 1024 ** 3

        self.update(f" {self.label}: {free_in_gib:.1f}GiB")


class LoadModule(PollingModule):
    def __init__(self, sleep=5, **kwargs):
        super().__init__(sleep=sleep, **kwargs)

    def run(self):
        load1, load5, load15 = psutil.getloadavg()
        cpu_count = psutil.cpu_count()

        if load1 > cpu_count:
            color = Color.URGENT
        elif load1 > cpu_count // 2:
            color = Color.WARN
        else:
            color = None

        self.update(f" {load1}", color=color)


class MemoryModule(PollingModule):
    def __init__(self, sleep=3, **kwargs):
        super().__init__(sleep=sleep, **kwargs)

    def run(self):
        memory = psutil.virtual_memory()

        if memory.available < 0.1 * memory.total:
            color = Color.URGENT
        elif memory.available < 0.3 * memory.total:
            color = Color.WARN
        else:
            color = None

        memory_in_gib = memory.available / 1024 ** 3
        self.update(f" {memory_in_gib:.1f}GiB", color=color)


class NetworkModule(PollingModule):
    def __init__(self, sleep=3, **kwargs):
        super().__init__(sleep=sleep, **kwargs)
        self.previous = psutil.net_io_counters()

    def run(self):
        now = psutil.net_io_counters()

        upload = (now.bytes_sent - self.previous.bytes_sent) / self.sleep
        download = (now.bytes_recv - self.previous.bytes_recv) / self.sleep

        if download > 5 * 1024 ** 2 or upload > 5 * 1024 ** 2:
            color = Color.URGENT
        elif download > 1024 ** 2 or upload > 1024 ** 2:
            color = Color.WARN
        else:
            color = None

        self.update(f" {bytes2human(upload)}  {bytes2human(download)}", color=color)

        self.previous = now


class TemperatureModule(PollingModule):
    def __init__(self, sleep=5, sensor=None, **kwargs):
        super().__init__(sleep=sleep, **kwargs)
        if sensor:
            self.sensor = sensor
        else:
            self.sensor = next(iter(psutil.sensors_temperatures().keys()))

    def run(self):
        temperatures = psutil.sensors_temperatures()[self.sensor]
        temperature = temperatures[0].current

        if temperature > 75:
            color = Color.URGENT
        elif temperature > 50:
            color = Color.WARN
        else:
            color = None

        self.update(f" {temperature:.0f}°C", color=color)
