import time
import signal

import i3pyblocks.modules.psutil
from i3pyblocks.core import PollingModule


class Color:
    GOOD = "#00FF00"
    WARN = "#FFFF00"
    URGENT = "#FF0000"


class LocalTimeModule(PollingModule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.run_fn = self.time

    def time(self):
        current_time = time.localtime()
        formatted_time = time.strftime("%T", current_time)
        self.update(f" {formatted_time}")

    def date(self):
        current_time = time.localtime()
        formatted_date = time.strftime("%d %a %Y", current_time)
        self.update(f" {formatted_date}")

    def signal_handler(self, signum, frame):
        if signum == signal.SIGUSR1:
            self.run_fn = self.time
        elif signum == signal.SIGUSR2:
            self.run_fn = self.date

        super().signal_handler(signum, frame)

    def click_handler(self, **kwargs):
        if self.run_fn == self.time:
            self.run_fn = self.date
        else:
            self.run_fn = self.time

        super().click_handler(**kwargs)

    def run(self):
        self.run_fn()
