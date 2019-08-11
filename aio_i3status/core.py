import abc
import asyncio


class Module(metaclass=abc.ABCMeta):
    def __init__(self):
        self.result = None

    @abc.abstractmethod
    async def loop(self):
        raise NotImplemented("Must implement loop method")


class PollingModule(Module):
    def __init__(self, sleep=1):
        super().__init__()
        self.sleep = sleep

    @abc.abstractmethod
    def run(self):
        raise NotImplemented("Must implement run method")

    async def loop(self):
        try:
            while True:
                self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            self.result = e


class Runner:
    def __init__(self, sleep=1):
        self.sleep = sleep
        self.modules = []
        task = asyncio.create_task(self.write_results())
        self.tasks = [task]

    async def write_results(self):
        while True:
            for module in self.modules:
                if module.result:
                    print(module.result)
            await asyncio.sleep(self.sleep)

    def register_module(self, module):
        if not isinstance(module, Module):
            raise ValueError

        self.modules.append(module)
        task = asyncio.create_task(module.loop())
        self.tasks.append(task)

    async def start(self):
        await asyncio.wait(self.tasks)
