import time

import psutil

from aio_i3status.core import Color, PollingModule


class TimeModule(PollingModule):
    def run(self):
        current_time = time.localtime()
        formatted_time = time.strftime("%a %T", current_time)
        self.full_text = f" {formatted_time}"


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
