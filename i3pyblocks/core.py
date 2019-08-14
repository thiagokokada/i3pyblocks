import abc
import asyncio
import json
import signal
import sys
from typing import Dict, Optional, List, Union


class Align:
    CENTER = "center"
    RIGHT = "right"
    LEFT = "left"


class Markup:
    NONE = "none"
    PANGO = "pango"


class Module(metaclass=abc.ABCMeta):
    def __init__(
        self,
        *,
        name: Optional[str] = None,
        instance: Optional[str] = None,
        color: Optional[str] = None,
        background: Optional[str] = None,
        border: Optional[str] = None,
        border_top: Optional[str] = None,
        border_right: Optional[str] = None,
        border_bottom: Optional[str] = None,
        border_left: Optional[str] = None,
        min_width: Optional[int] = None,
        align: Optional[str] = None,
        urgent: Optional[bool] = False,
        separator: Optional[bool] = True,
        separator_block_width: Optional[int] = None,
        markup: Optional[str] = Markup.NONE,
    ) -> None:
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

    def signal_handler(self, signum: int, frame: Optional[object]) -> None:
        raise NotImplementedError("Must implement handler method")

    def format(self) -> Dict[str, Union[str, int, bool]]:
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
                "border_bottom": self.border_bottom,
                "min_width": self.min_width,
                "align": self.align,
                "urgent": self.urgent,
                "separator": self.separator,
                "separator_block_width": self.separator_block_width,
                # full_text must be present, even if it is an empty string
                "full_text": str(self.full_text),
                "short_text": self.short_text,
            }.items()
            if v is not None
        }

    @abc.abstractmethod
    async def loop(self) -> None:
        pass


class PollingModule(Module):
    def __init__(self, sleep: int = 1, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sleep = sleep

    @abc.abstractmethod
    def run(self) -> None:
        pass

    def signal_handler(self, _signum, _frame) -> None:
        self.run()

    async def loop(self) -> None:
        try:
            while True:
                self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            self.urgent = True
            self.full_text = "Exception in {name}: {exception}".format(
                name=self.name, exception=e
            )


class Runner:
    def __init__(self, sleep: int = 1) -> None:
        self.sleep = sleep
        self.modules: List[Module] = []
        task = asyncio.ensure_future(self.write_results())
        self.tasks = [task]

    def _clean_up(self) -> None:
        for task in self.tasks:
            task.cancel()

    def _register_task(self, task: asyncio.Future) -> None:
        self.tasks.append(task)

    def register_signal(self, module: Module, signums: List[int] = []) -> None:
        def _handler(signum, frame):
            module.signal_handler(signum, frame)
            self.write_result()

        for signum in signums:
            signal.signal(signum, _handler)

    def register_module(self, module: Module, signals: List[int] = []) -> None:
        if not isinstance(module, Module):
            raise ValueError("Must be a Module instance")

        if signals:
            self.register_signal(module, signals)

        self.modules.append(module)
        task = asyncio.ensure_future(module.loop())
        self._register_task(task)

    def write_result(self) -> None:
        output: List[str] = []

        for module in self.modules:
            output.append(json.dumps(module.format()))

        sys.stdout.write("[" + ",".join(output) + "],\n")
        sys.stdout.flush()

    async def write_results(self) -> None:
        while True:
            self.write_result()
            await asyncio.sleep(self.sleep)

    async def start(self, timeout: Optional[int] = None) -> None:
        sys.stdout.write('{"version": 1}\n[\n')
        sys.stdout.flush()

        await asyncio.wait(self.tasks, timeout=timeout)

        self._clean_up()
