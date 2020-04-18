import asyncio
import json
import logging
import sys
import uuid
from typing import Any, Dict, Iterable, List, Optional, Union

from i3pyblocks import modules

logger = logging.getLogger("i3pyblocks")
logger.addHandler(logging.NullHandler())


class Runner:
    def __init__(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._modules: Dict[uuid.UUID, Dict[str, Any]] = {}
        self._tasks: List[asyncio.Future] = []
        self._queue: asyncio.Queue = asyncio.Queue()

    def register_signal(self, module: modules.Module, signums: Iterable[int]) -> None:
        def signal_handler(signum: int):
            try:
                logger.debug(
                    f"Module {module.name} with id {module.id} received a signal {signum}"
                )
                module.signal_handler(signum=signum)
            except Exception:
                logger.exception(f"Exception in {module.name} signal handler")

        for signum in signums:
            self._loop.add_signal_handler(signum, signal_handler, signum)
            logger.debug(f"Registered signal {signum} for {module.name}")

    def register_task(self, coro) -> None:
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        logger.debug(f"Registered async task {coro} in {self}")

    def register_module(
        self, module: modules.Module, signals: Iterable[int] = ()
    ) -> None:
        self._modules[module.id] = {"module": module, "result": {}}
        self.register_task(module.start(self._queue))

        if signals:
            self.register_signal(module, signals)

    async def get_result(self) -> None:
        id_, result = await self._queue.get()
        self._modules[id_]["result"] = result

    async def write_results(self) -> None:
        while True:
            await self.get_result()
            output = [json.dumps(m["result"]) for m in self._modules.values()]
            print("[" + ",".join(output) + "],", flush=True)

    def click_event(self, raw: Union[str, bytes, bytearray]) -> None:
        try:
            click_event = json.loads(raw)
            instance = click_event["instance"]
            id_ = uuid.UUID(instance)
            module = self._modules[id_]["module"]

            logger.debug(
                f"Module {module.name} with id {module.id} received"
                " a click event: {click_event}"
            )

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
        except Exception:
            logger.exception(f"Error in {module.name} click handler")

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

        print('{"version": 1, "click_events": true}\n[', flush=True)

        await asyncio.wait(self._tasks, timeout=timeout)
