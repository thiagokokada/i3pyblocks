import datetime
import time
import signal

import psutil
from psutil._common import bytes2human

from i3pyblocks.core import PollingModule


class Color:
    GOOD = "#00FF00"
    WARN = "#FFFF00"
    URGENT = "#FF0000"


class BatteryModule(PollingModule):
    def __init__(self, sleep=5):
        super().__init__(sleep=sleep)

    def format_battery(self, percent):
        if percent > 75:
            self.color = None
            return ""
        elif percent > 50:
            self.color = None
            return ""
        elif percent > 25:
            self.color = None
            return ""
        elif percent > 10:
            self.color = Color.WARN
            return ""
        else:
            self.color = Color.URGENT
            return ""

    def run(self):
        battery = psutil.sensors_battery()

        if not battery:
            self.full_text = ""
            return

        percent = battery.percent
        remaining_time = battery.secsleft
        remaining_time_formatted = datetime.timedelta(seconds=battery.secsleft)
        plugged = battery.power_plugged

        if plugged:
            self.color = None
            self.full_text = f" {percent:.0f}%"
        elif remaining_time != psutil.POWER_TIME_UNKNOWN:
            self.full_text = f"{self.format_battery(percent)} {percent:.0f}% {remaining_time_formatted}"
        else:
            self.full_text = f"{self.format_battery(percent)} {percent:.0f}%"


class DiskModule(PollingModule):
    def __init__(self, sleep=5, path="/", short_name=False):
        super().__init__(sleep=sleep, instance=path)
        self.path = path
        self.short_name = short_name

    def run(self):
        free = psutil.disk_usage("/").free
        free_in_gib = free / 1024 ** 3

        if self.short_name:
            name = "/" + "/".join(x[0] for x in self.path.split("/") if x)
        else:
            name = self.path

        self.full_text = f" {name}: {free_in_gib:.1f}GiB"


class LoadModule(PollingModule):
    def __init__(self, sleep=5):
        super().__init__(sleep=sleep)

    def run(self):
        load1, load5, load15 = psutil.getloadavg()
        cpu_count = psutil.cpu_count()

        if load1 > cpu_count:
            self.color = Color.URGENT
        elif load1 > cpu_count // 2:
            self.color = Color.WARN
        else:
            self.color = None

        self.full_text = f" {load1}"


class LocalTimeModule(PollingModule):
    def signal_handler(self, signum, _):
        if signum == signal.SIGUSR1:
            self.color = Color.URGENT
        else:
            self.color = None

    def run(self):
        current_time = time.localtime()
        formatted_time = time.strftime("%a %T", current_time)
        self.full_text = f" {formatted_time}"


class MemoryModule(PollingModule):
    def run(self):
        memory = psutil.virtual_memory()

        if memory.available < 0.1 * memory.total:
            self.color = Color.URGENT
        elif memory.available < 0.3 * memory.total:
            self.color = Color.WARN
        else:
            self.color = None

        memory_in_gib = memory.available / 1024 ** 3
        self.full_text = f" {memory_in_gib:.1f}GiB"


class NetworkModule(PollingModule):
    def __init__(self, sleep=3):
        self.previous = psutil.net_io_counters()
        super().__init__(sleep=sleep)

    def run(self):
        now = psutil.net_io_counters()

        upload = (now.bytes_sent - self.previous.bytes_sent) / self.sleep
        download = (now.bytes_recv - self.previous.bytes_recv) / self.sleep

        self.previous = now

        if download > 5 * 1024 ** 2 or upload > 5 * 1024 ** 2:
            self.color = Color.URGENT
        elif download > 1024 ** 2 or upload > 1024 ** 2:
            self.color = Color.WARN
        else:
            self.color = None

        self.full_text = f" {bytes2human(upload)}  {bytes2human(download)}"


class TemperatureModule(PollingModule):
    def __init__(self, sleep=5, sensor=None):
        if sensor:
            self.sensor = sensor
        else:
            self.sensor = next(iter(psutil.sensors_temperatures().keys()))
        super().__init__(sleep=sleep)

    def run(self):
        temperatures = psutil.sensors_temperatures()[self.sensor]
        temperature = temperatures[0]

        self.full_text = f" {temperature.current}°C"
