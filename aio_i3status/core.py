import abc
import asyncio
import json
import sys


class Markup:
    NONE = "none"
    PANGO = "pango"


class Module(metaclass=abc.ABCMeta):
    def __init__(
        self,
        *,
        name=None,
        instance=None,
        color=None,
        background=None,
        border=None,
        border_top=None,
        border_right=None,
        border_bottom=None,
        border_left=None,
        min_width=None,
        align=None,
        urgent=False,
        separator=True,
        separator_block_width=None,
        markup=Markup.NONE,
    ):
        if name:
            self.name = name
        else:
            self.name = self.__class__.__name__
        self.instance = instance
        self.color = color
        self.background = background
        self.border = border
        self.border_top = border_top
        self.border_right = border_right
        self.border_bottom = border_bottom
        self.border_left = border_left
        self.min_width = min_width
        self.align = align
        self.urgent = urgent
        self.separator = separator
        self.separator_block_width = separator_block_width
        self.short_text = None
        self.full_text = ""

    def format(self):
        try:
            return {
                k: v
                for k, v in {
                    "name": self.name,
                    "instance": self.instance,
                    "color": self.color,
                    "background": self.background,
                    "border": self.border,
                    "border_top": self.border_top,
                    "border_right": self.border_right,
                    "border_left": self.border_left,
                    "min_width": self.min_width,
                    "align": self.align,
                    "urgent": self.urgent,
                    "separator": self.separator,
                    "separator_block_width": self.separator_block_width,
                    "full_text": self.full_text,
                    "short_text": self.short_text,
                }.items()
                if v is not None
            }
        except Exception as e:
            module_name = self.__class__.__name__
            return {
                "urgent": True,
                "name": module_name,
                "full_text": "Exception in {name}.format(): {exception}".format(
                    name=module_name, exception=e
                ),
            }

    @abc.abstractmethod
    async def loop(self):
        raise NotImplemented("Must implement loop method")


class PollingModule(Module):
    def __init__(self, sleep=1, **kwargs):
        super().__init__(**kwargs)
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
            self.urgent = True
            self.full_text = "Exception in {name}.run(): {exception}".format(
                name=self.name, exception=e
            )


class Runner:
    def __init__(self, sleep=1):
        self.sleep = sleep
        self.modules = []
        task = asyncio.create_task(self.write_results())
        self.tasks = [task]

    async def write_results(self):
        while True:
            output = []

            for module in self.modules:
                output.append(json.dumps(module.format()))

            sys.stdout.write("[" + ",".join(output) + "],\n")
            sys.stdout.flush()

            await asyncio.sleep(self.sleep)

    def register_module(self, module):
        if not isinstance(module, Module):
            raise ValueError("Must be a Module instance")

        self.modules.append(module)
        task = asyncio.create_task(module.loop())
        self.tasks.append(task)

    async def start(self):
        sys.stdout.write('{"version": 1}\n[\n')
        sys.stdout.flush()

        await asyncio.wait(self.tasks)
