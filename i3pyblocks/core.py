import abc
import asyncio
import json
import uuid
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Optional, Union

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
        *,
        color: Optional[str] = None,
        background: Optional[str] = None,
        border: Optional[str] = None,
        border_top: Optional[int] = None,
        border_right: Optional[int] = None,
        border_bottom: Optional[int] = None,
        border_left: Optional[int] = None,
        min_width: Optional[int] = None,
        align: Optional[str] = None,
        urgent: Optional[bool] = False,
        separator: Optional[bool] = True,
        separator_block_width: Optional[int] = None,
        markup: Optional[str] = Markup.NONE,
    ) -> None:
        self.id = uuid.uuid4()
        self.name = name or self.__class__.__name__
        self.instance = str(self.id)

        # Those are default values for properties if they are not overrided
        self._default_state = utils.non_nullable_dict(
            name=self.name,
            instance=self.instance,
            color=color,
            background=background,
            border=border,
            border_top=border_top,
            border_right=border_right,
            border_left=border_left,
            border_bottom=border_bottom,
            min_width=min_width,
            align=align,
            urgent=urgent,
            separator=separator,
            separator_block_width=separator_block_width,
            markup=markup,
        )

        self.update()

    def update(
        self,
        full_text: str = "",
        short_text: Optional[str] = None,
        color: Optional[str] = None,
        background: Optional[str] = None,
        border: Optional[str] = None,
        border_top: Optional[int] = None,
        border_right: Optional[int] = None,
        border_bottom: Optional[int] = None,
        border_left: Optional[int] = None,
        min_width: Optional[int] = None,
        align: Optional[str] = None,
        urgent: Optional[bool] = None,
        separator: Optional[bool] = None,
        separator_block_width: Optional[int] = None,
        markup: Optional[str] = None,
    ):
        self._state = utils.non_nullable_dict(
            full_text=full_text,
            short_text=short_text,
            color=color,
            background=background,
            border=border,
            border_top=border_top,
            border_right=border_right,
            border_left=border_left,
            border_bottom=border_bottom,
            min_width=min_width,
            align=align,
            urgent=urgent,
            separator=separator,
            separator_block_width=separator_block_width,
            markup=markup,
        )

    def result(self) -> Dict[str, Union[str, int, bool]]:
        return {**self._default_state, **self._state}

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
        raise NotImplementedError("Should implement click_handler method")

    def signal_handler(self, signum: int) -> None:
        raise NotImplementedError("Should implement signal_handler method")

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


class ThreadingModule(Module):
    def __init__(self, max_workers: int = 1, **kwargs) -> None:
        super().__init__(**kwargs)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    @abc.abstractmethod
    def run(self) -> None:
        pass

    async def loop(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._executor, self.run)
        except Exception as e:
            utils.Log.exception(f"Exception in {self.name}")
            self.update(f"Exception in {self.name}: {e}", urgent=True)


class Runner:
    notify_event = None

    def __init__(self, sleep: int = 1) -> None:
        self.sleep = sleep
        self._loop = asyncio.get_running_loop()
        self._modules: Dict[str, Module] = {}
        self._tasks: List[asyncio.Future] = []
        Runner.notify_event = asyncio.Event()

    def register_signal(self, module: Module, signums: Iterable[int]) -> None:
        def _handler(signum: int):
            try:
                module.signal_handler(signum=signum)
                self.write_result()
            except Exception:
                utils.Log.exception(f"Exception in {module.name} signal handler")

        for signum in signums:
            self._loop.add_signal_handler(signum, _handler, signum)

    def register_task(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.append(task)

    def register_module(self, module: Module, signals: Iterable[int] = ()) -> None:
        self._modules[module.instance] = module
        self.register_task(module.loop())

        if signals:
            self.register_signal(module, signals)

    def write_result(self) -> None:
        output = [json.dumps(module.result()) for module in self._modules.values()]
        print("[" + ",".join(output) + "],", flush=True)

    async def write_results(self) -> None:
        while True:
            self.write_result()
            await asyncio.sleep(self.sleep)

    async def write_results_from_notification(self) -> None:
        assert Runner.notify_event

        while True:
            await Runner.notify_event.wait()
            self.write_result()
            utils.Log.debug(f"Write results from notification")
            Runner.notify_event.clear()

    @classmethod
    def notify_update(cls, module: Module) -> None:
        if cls.notify_event:
            utils.Log.debug(
                f"Module {module.name} with id {module.id} asked for update"
            )
            cls.notify_event.set()

    def click_event(self, raw: Union[str, bytes, bytearray]) -> None:
        try:
            click_event = json.loads(raw)
            instance = click_event["instance"]
            module = self._modules[instance]

            module.click_handler(
                x=click_event.get("x"),
                y=click_event.get("y"),
                button=click_event.get("button"),
                relative_x=click_event.get("relative_x"),
                relative_y=click_event.get("relative_y"),
                width=click_event.get("width"),
                height=click_event.get("height"),
                modifiers=click_event.get("modifiers"),
            )
            self.write_result()
        except Exception:
            utils.Log.exception(f"Error in {module.name} click handler")

    # Based on: https://git.io/fjbHx
    async def click_events(self) -> None:
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)

        await self._loop.connect_read_pipe(lambda: protocol, sys.stdin)

        await reader.readline()

        while True:
            raw = await reader.readuntil(b"}")
            self.click_event(raw)
            await reader.readuntil(b",")

    async def start(self, timeout: Optional[int] = None) -> None:
        self.register_task(self.click_events())
        self.register_task(self.write_results())
        self.register_task(self.write_results_from_notification())

        print('{"version": 1, "click_events": true}\n[', flush=True)

        await asyncio.wait(self._tasks, timeout=timeout)
