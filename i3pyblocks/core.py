import abc
import asyncio
import json
import sys
from typing import Dict, Optional, List, Union

from i3pyblocks import utils


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
        instance: Optional[str] = "default",
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
        self.name = name or self.__class__.__name__
        self.instance = instance

        # Those are default values for properties if they are not overrided
        self._color = color
        self._background = background
        self._border = border
        self._border_top = border_top
        self._border_right = border_right
        self._border_bottom = border_bottom
        self._border_left = border_left
        self._min_width = min_width
        self._align = align
        self._urgent = urgent
        self._separator = separator
        self._separator_block_width = separator_block_width
        self._markup = markup
        self._short_text = None
        self._full_text = ""

        self._state: Dict[str, Optional[Union[str, int, bool]]]
        self.update()

    def _get_value_or_default(
        self, value: Optional[Union[str, int, bool]], key: str
    ) -> Optional[Union[str, int, bool]]:
        if value is not None:
            return value
        else:
            return getattr(self, key)

    @staticmethod
    def get_key(name: str, instance: Optional[str]):
        return f"{name}__{instance or 'none'}"

    def key(self) -> str:
        return self.get_key(self.name, self.instance)

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

    def result(self) -> Dict[str, Union[str, int, bool]]:
        return {k: v for k, v in self._state.items() if v is not None}

    @abc.abstractmethod
    def click_handler(
        self,
        x: int,
        y: int,
        button: int,
        relative_x: int,
        relative_y: int,
        width: int,
        height: int,
        modifiers: List[str],
    ) -> None:
        pass

    @abc.abstractmethod
    def signal_handler(self, signum: int) -> None:
        pass

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

    def click_handler(self, *_, **__) -> None:
        self.run()

    def signal_handler(self, *_, **__) -> None:
        self.run()

    async def loop(self) -> None:
        try:
            while True:
                self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            utils.Log.exception(f"Exception in {self.name}")
            self.update(f"Exception in {self.name}: {e}", urgent=True)


class Runner:
    def __init__(self, sleep: int = 1, loop=None) -> None:
        self.sleep = sleep
        self.modules: Dict[str, Module] = {}
        self.tasks: List[asyncio.Future] = []

        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

    def _get_module_from_key(self, name: str, instance: str = None) -> Module:
        return self.modules[Module.get_key(name, instance)]

    def _register_coroutine(self, coro) -> None:
        task = asyncio.ensure_future(coro)
        self.tasks.append(task)

    def register_signal(self, module: Module, signums: List[int] = []) -> None:
        def _handler(signum: int):
            try:
                module.signal_handler(signum)
                self.write_result()
            except Exception:
                utils.Log.exception(f"Exception in {module.name} signal handler")

        for signum in signums:
            self.loop.add_signal_handler(signum, _handler, signum)

    def register_module(self, module: Module, signals: List[int] = []) -> None:
        module_key = module.key()

        if module_key not in self.modules.keys():
            self.modules[module_key] = module
        else:
            raise ValueError(
                f"Module '{module.name}' with instance '{module.instance}' already exists"
            )

        self._register_coroutine(module.loop())

        if signals:
            self.register_signal(module, signals)

    def write_result(self) -> None:
        output = [json.dumps(module.result()) for module in self.modules.values()]

        sys.stdout.write("[" + ",".join(output) + "],\n")
        sys.stdout.flush()

    async def write_results(self) -> None:
        while True:
            self.write_result()
            await asyncio.sleep(self.sleep)

    def click_event(self, raw: Union[str, bytes, bytearray]) -> None:
        try:
            click_event = json.loads(raw)
            module = self._get_module_from_key(
                click_event.get("name"), click_event.get("instance")
            )
            module.click_handler(
                click_event.get("x"),
                click_event.get("y"),
                click_event.get("button"),
                click_event.get("relative_x"),
                click_event.get("relative_y"),
                click_event.get("width"),
                click_event.get("height"),
                click_event.get("modifiers"),
            )
            self.write_result()
        except Exception:
            utils.Log.exception(f"Error in {module.name} click handler")

    # Based on: https://git.io/fjbHx
    async def click_events(self) -> None:
        reader = asyncio.StreamReader(loop=self.loop)
        protocol = asyncio.StreamReaderProtocol(reader, loop=self.loop)

        await self.loop.connect_read_pipe(lambda: protocol, sys.stdin)

        await reader.readline()

        while True:
            raw = await reader.readuntil(b"}")
            self.click_event(raw)
            await reader.readuntil(b",")

    def _setup(self) -> None:
        self._register_coroutine(self.click_events())
        self._register_coroutine(self.write_results())

    def _clean_up(self) -> None:
        for task in self.tasks:
            task.cancel()

    async def start(self, timeout: Optional[int] = None) -> None:
        self._setup()

        sys.stdout.write('{"version": 1, "click_events": true}\n[\n')
        sys.stdout.flush()

        await asyncio.wait(self.tasks, timeout=timeout, loop=self.loop)

        self._clean_up()
