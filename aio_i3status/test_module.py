from datetime import datetime

from aio_i3status.core import PollingModule


class TestModule(PollingModule):
    def __init__(self, sleep=0.5):
        super().__init__(sleep)
        self.result = 0

    def run(self):
        if self.result >= 10:
            raise Exception("Error!")
        self.result += 1


class AnotherTestModule(PollingModule):
    def run(self):
        self.result = datetime.now().time()
