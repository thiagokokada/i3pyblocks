import asyncio
import json
import sys
from typing import Dict, Iterable, List, Optional, Union

from i3pyblocks import utils, modules


class Runner:
    notify_event = None

    def __init__(self, sleep: int = 1) -> None:
        self.sleep = sleep
        self._loop = asyncio.get_running_loop()
        self._modules: Dict[str, modules.Module] = {}
        self._tasks: List[asyncio.Future] = []
        Runner.notify_event = asyncio.Event()

    def register_signal(self, module: modules.Module, signums: Iterable[int]) -> None:
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

    def register_module(
        self, module: modules.Module, signals: Iterable[int] = ()
    ) -> None:
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
    def notify_update(cls, module: modules.Module) -> None:
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
