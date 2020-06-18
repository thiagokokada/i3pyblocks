import abc
import asyncio
import signal
import uuid
from concurrent.futures import Executor
from enum import Enum
from typing import List, Optional

from i3pyblocks import core, utils, types


class Align(Enum):
    CENTER = "center"
    RIGHT = "right"
    LEFT = "left"


class Markup(Enum):
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
        align: Optional[Align] = Align.LEFT,
        urgent: Optional[bool] = False,
        separator: Optional[bool] = True,
        separator_block_width: Optional[int] = None,
        markup: Optional[Markup] = Markup.NONE,
    ) -> None:
        self.id = uuid.uuid4()
        self.name = name or self.__class__.__name__
        self.freeze = True

        # Those are default values for properties if they are not overrided
        self._default_state = utils.non_nullable_dict(
            name=self.name,
            instance=str(self.id),
            color=color,
            background=background,
            border=border,
            border_top=border_top,
            border_right=border_right,
            border_left=border_left,
            border_bottom=border_bottom,
            min_width=min_width,
            align=align.value if align else None,
            urgent=urgent,
            separator=separator,
            separator_block_width=separator_block_width,
            markup=markup.value if markup else None,
        )

        self.update_state()

    def update_state(
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
        align: Optional[Align] = None,
        urgent: Optional[bool] = None,
        separator: Optional[bool] = None,
        separator_block_width: Optional[int] = None,
        markup: Optional[Markup] = None,
    ) -> None:
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
            align=align.value if align else None,
            urgent=urgent,
            separator=separator,
            separator_block_width=separator_block_width,
            markup=markup.value if markup else None,
        )

    def result(self) -> types.Result:
        return {**self._default_state, **self._state}

    def push_update(self) -> None:
        if not self.freeze:
            self.update_queue.put_nowait((self.id, self.result()))
        else:
            core.logger.warn(
                f"Not pushing update since module {self.name} with "
                f"id {self.id} is frozen"
            )

    def update(self, *args, **kwargs) -> None:
        self.update_state(*args, **kwargs)
        self.push_update()

    def abort(self, *args, **kwargs) -> None:
        self.update(*args, **kwargs)
        self.freeze = True

    async def click_handler(
        self,
        *,
        x: int,
        y: int,
        button: int,
        relative_x: int,
        relative_y: int,
        width: int,
        height: int,
        modifiers: List[Optional[str]],
    ) -> None:
        pass

    async def signal_handler(self, *, sig: signal.Signals) -> None:
        pass

    @abc.abstractmethod
    async def start(self, queue: asyncio.Queue = None) -> None:
        if not queue:
            queue = asyncio.Queue()
        self.update_queue = queue
        self.freeze = False


class PollingModule(Module):
    def __init__(self, sleep: int = 1, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sleep = sleep

    @abc.abstractmethod
    async def run(self) -> None:
        pass

    async def click_handler(
        self,
        *,
        x: int,
        y: int,
        button: int,
        relative_x: int,
        relative_y: int,
        width: int,
        height: int,
        modifiers: List[Optional[str]],
    ) -> None:
        await self.run()

    async def signal_handler(self, *, sig: signal.Signals) -> None:
        await self.run()

    async def start(self, queue: asyncio.Queue = None) -> None:
        await super().start(queue)
        try:
            while True:
                await self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.abort(f"Exception in {self.name}: {e}", urgent=True)


class ExecutorModule(Module):
    def __init__(self, executor: Optional[Executor] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.executor = executor

    def __exit__(self, *_) -> None:
        if self.executor:
            self.executor.shutdown(wait=True)

    @abc.abstractmethod
    def run(self) -> None:
        pass

    async def start(self, queue: asyncio.Queue = None) -> None:
        await super().start(queue)
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self.run)
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.abort(f"Exception in {self.name}: {e}", urgent=True)
