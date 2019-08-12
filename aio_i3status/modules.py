import time

import psutil
from psutil._common import bytes2human

from aio_i3status.core import PollingModule


class Color:
    GOOD = "#00FF00"
    WARN = "#FFFF00"
    URGENT = "#FF0000"


class DiskModule(PollingModule):
    def __init__(self, path="/", short_name=False):
        super().__init__(instance=path)
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
    def __init__(self):
        self.previous = psutil.net_io_counters()
        super().__init__()

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
    def __init__(self, sensor=None):
        if sensor:
            self.sensor = sensor
        else:
            self.sensor = next(iter(psutil.sensors_temperatures().keys()))
        super().__init__()

    def run(self):
        temperatures = psutil.sensors_temperatures()[self.sensor]
        temperature = temperatures[0]

        self.full_text = f" {temperature.current}°C"
