import time

from aio_i3status.core import PollingModule


class CountModule(PollingModule):
    def __init__(self):
        super().__init__()
        self.result = 0

    def run(self):
        self.result += 1


class TimeModule(PollingModule):
    def run(self):
        current_time = time.localtime()
        self.result = time.strftime("%Y-%m-%d %T", current_time)
