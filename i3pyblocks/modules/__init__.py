import abc
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Dict, List, Optional, Union

from i3pyblocks import core, utils


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
        self.instance = str(self.id)

        # Those are default values for properties if they are not overrided
        self.default_state = utils.non_nullable_dict(
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
        self.state = utils.non_nullable_dict(
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

    def result(self) -> Dict[str, Union[str, int, bool]]:
        return {**self.default_state, **self.state}

    def push_update(self) -> None:
        assert hasattr(
            self, "update_queue"
        ), "Cannot call push_update() method without calling start() method first"

        self.update_queue.put_nowait((self.id, self.result()))

    def update(self, *args, **kwargs) -> None:
        self.update_state(*args, **kwargs)
        self.push_update()

    def click_handler(
        self,
        x: int,
        y: int,
        button: int,
        relative_x: int,
        relative_y: int,
        width: int,
        height: int,
        modifiers: List[Optional[str]],
    ) -> None:
        raise NotImplementedError("Should implement click_handler method")

    def signal_handler(self, signum: int) -> None:
        raise NotImplementedError("Should implement signal_handler method")

    @abc.abstractmethod
    async def start(self, queue: asyncio.Queue) -> None:
        self.update_queue = queue


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

    async def start(self, queue: asyncio.Queue) -> None:
        self.update_queue = queue
        try:
            while True:
                self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.update(f"Exception in {self.name}: {e}", urgent=True)


class ThreadingModule(Module):
    def __init__(self, _max_workers: int = 1, **kwargs) -> None:
        super().__init__(**kwargs)
        self._executor = ThreadPoolExecutor(max_workers=_max_workers)

    @abc.abstractmethod
    def run(self) -> None:
        pass

    async def start(self, queue: asyncio.Queue) -> None:
        self.update_queue = queue
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._executor, self.run)
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.update(f"Exception in {self.name}: {e}", urgent=True)
