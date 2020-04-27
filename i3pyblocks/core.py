import asyncio
import json
import logging
import signal
import sys
import uuid
from typing import AnyStr, Awaitable, Dict, Iterable, List, Optional, Union

from i3pyblocks import modules, types

logger = logging.getLogger("i3pyblocks")
logger.addHandler(logging.NullHandler())


class Runner:
    def __init__(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.modules: Dict[uuid.UUID, modules.Module] = {}
        self.results: Dict[uuid.UUID, Optional[types.Result]] = {}
        self.tasks: List[asyncio.Future] = []
        self.queue: asyncio.Queue = asyncio.Queue()

    def register_signal(
        self, module: modules.Module, signums: Iterable[Union[int, signal.Signals]]
    ) -> None:
        async def signal_handler(sig: signal.Signals):
            try:
                logger.debug(
                    f"Module {module.name} with id {module.id} received a signal {sig.name}"
                )
                await module.signal_handler(sig=sig)
            except Exception:
                logger.exception(f"Exception in {module.name} signal handler")

        def callback_fn(sig: signal.Signals):
            return asyncio.create_task(signal_handler(sig))

        for signum in signums:
            sig = signal.Signals(signum)  # Make sure this is a Signals instance
            self.loop.add_signal_handler(sig, callback_fn, sig)
            logger.debug(f"Registered signal {sig.name} for {module.name}")

    def register_task(self, awaitable: Awaitable) -> None:
        task = asyncio.create_task(awaitable)
        self.tasks.append(task)
        logger.debug(f"Registered async task {awaitable} in {self}")

    def register_module(
        self, module: modules.Module, signals: Iterable[Union[int, signal.Signals]] = ()
    ) -> None:
        self.modules[module.id] = module
        # This only works correctly because from Python 3.7+ dict is ordered
        self.results[module.id] = None
        self.register_task(module.start(self.queue))

        if signals:
            self.register_signal(module, signals)

    async def update_results(self) -> None:
        id_, result = await self.queue.get()
        self.results[id_] = result

        # To reduce the number of redraws, let's empty the queue here
        # and draw all updates at the same time
        while self.queue.qsize() > 0:
            id_, result = self.queue.get_nowait()
            self.results[id_] = result

    async def write_results(self) -> None:
        while True:
            await self.update_results()
            output = list(self.results.values())
            print(json.dumps(output), end=",\n", flush=True)

    async def click_event(self, raw: AnyStr) -> None:
        try:
            click_event = json.loads(raw)
            instance = click_event["instance"]
            id_ = uuid.UUID(instance)
            module = self.modules[id_]

            logger.debug(
                f"Module {module.name} with id {module.id} received"
                f" a click event: {click_event}"
            )

            await module.click_handler(
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

        await self.loop.connect_read_pipe(lambda: protocol, sys.stdin)

        await reader.readline()

        while True:
            raw = await reader.readuntil(b"}")
            await self.click_event(raw)
            await reader.readuntil(b",")

    def stop(self) -> None:
        for task in self.tasks:
            task.cancel()

    async def start(self, timeout: Optional[int] = None) -> None:
        self.register_task(self.click_events())
        self.register_task(self.write_results())

        print(json.dumps({"version": 1, "click_events": True}), end="\n[\n", flush=True)

        await asyncio.wait(self.tasks, timeout=timeout)

        self.stop()
