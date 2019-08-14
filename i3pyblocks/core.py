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
        name: Optional[str] = None,
        instance: Optional[str] = None,
        *,
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
        self.name: str
        if name:
            self.name = name
        else:
            self.name = self.__class__.__name__
        self.instance: Optional[str] = instance

        # Those are default values for properties if they are not overrided
        self._color: Optional[str] = color
        self._background: Optional[str] = background
        self._border: Optional[str] = border
        self._border_top: Optional[str] = border_top
        self._border_right: Optional[str] = border_right
        self._border_bottom: Optional[str] = border_bottom
        self._border_left: Optional[str] = border_left
        self._min_width: Optional[int] = min_width
        self._align: Optional[str] = align
        self._urgent: Optional[bool] = urgent
        self._separator: Optional[bool] = separator
        self._separator_block_width: Optional[int] = separator_block_width
        self._markup: Optional[str] = markup
        self._short_text: Optional[str] = None
        self._full_text: str = ""

        self._state: Dict[str, Optional[Union[str, int, bool]]]
        self.update()

    def _get_value_or_default(
        self, value: Optional[Union[str, int, bool]], key: str
    ) -> Optional[Union[str, int, bool]]:
        if value is not None:
            return value
        else:
            return getattr(self, key)

    def update(
        self,
        full_text: str = "",
        short_text: Optional[str] = None,
        color: Optional[str] = None,
        background: Optional[str] = None,
        border: Optional[str] = None,
        border_top: Optional[str] = None,
        border_right: Optional[str] = None,
        border_bottom: Optional[str] = None,
        border_left: Optional[str] = None,
        min_width: Optional[int] = None,
        align: Optional[str] = None,
        urgent: Optional[bool] = None,
        separator: Optional[bool] = None,
        separator_block_width: Optional[int] = None,
        markup: Optional[str] = None,
    ):
        self._state = {
            "name": self.name,
            "instance": self.instance,
            "full_text": full_text,
            "short_text": short_text,
            "color": self._get_value_or_default(color, "_color"),
            "background": self._get_value_or_default(background, "_background"),
            "border": self._get_value_or_default(border, "_border"),
            "border_top": self._get_value_or_default(border_top, "_border_top"),
            "border_right": self._get_value_or_default(border_right, "_border_right"),
            "border_left": self._get_value_or_default(border_left, "_border_left"),
            "border_bottom": self._get_value_or_default(
                border_bottom, "_border_bottom"
            ),
            "min_width": self._get_value_or_default(min_width, "_min_width"),
            "align": self._get_value_or_default(align, "_align"),
            "urgent": self._get_value_or_default(urgent, "_urgent"),
            "separator": self._get_value_or_default(separator, "_separator"),
            "separator_block_width": self._get_value_or_default(
                separator_block_width, "_separator_block_width"
            ),
            "markup": self._get_value_or_default(markup, "_markup"),
        }

    def signal_handler(self, signum: int, frame: Optional[object]) -> None:
        raise NotImplementedError("Must implement handler method")

    def result(self) -> Dict[str, Union[str, int, bool]]:
        return {k: v for k, v in self._state.items() if v is not None}

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
            self.update(f"Exception in {self.name}: {e}", urgent=True)


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
            output.append(json.dumps(module.result()))

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
