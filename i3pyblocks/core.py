"""i3pyblocks core.

This module contains the essence of i3pyblocks. Most of its functionality is
implemented in Runner class, a class that manages Blocks and also handles
outputing the result, handling i3bar events and handling Unix signals.

Attributes:
  logger: Logger instance used by i3pyblocks.
"""


import asyncio
import json
import signal
import uuid
from typing import AnyStr, Awaitable, Dict, Iterable, List, Optional, Union

from i3pyblocks import blocks, logger
from i3pyblocks._internal import misc, models


class Runner:
    """Main class of i3pyblocks, managing and running Blocks.

    This is the class in i3pyblocks responsible to managing Blocks and
    running them, printing its results to stdout and also reading stdin for
    possible click events comming from `i3bar`_.

    .. _i3bar:
        https://i3wm.org/docs/i3bar-protocol.html
    """

    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.blocks: Dict[uuid.UUID, blocks.Block] = {}
        self.results: Dict[uuid.UUID, Optional[models.State]] = {}
        self.tasks: List[asyncio.Future] = []
        self.queue: asyncio.Queue = asyncio.Queue()

    def register_signal(
        self,
        block: blocks.Block,
        signums: Iterable[Union[int, signal.Signals]],
    ) -> None:
        """Registers a list of Unix signals for a Block.

        This will register a :meth:`~i3pyblocks.blocks.base.Block.signal_handler`
        method as a callback for when signums[] is called. Note that since
        signals are associated with the main thread of i3pyblocks, each signal can
        only be assigned to a specific Block.

        The received signal will be passed to
        :meth:`~i3pyblocks.blocks.base.Block.signal_handler` as a parameter, so
        when receiving multiple signals it is possible to identify each of them
        separately.

        This method capture the errors inside
        :meth:`~i3pyblocks.blocks.base.Block.signal_handler`, but it also logs
        it so you can inspect the issue later on.

        :param block: instance of :class:`~i3pyblocks.blocks.base.Block` that
            will receive the signal.

        :param signmums: Any iterable containing signal numbers. Each signal
            can be an int or a `Signal enum`_.

        .. _`Signal enum`:
            https://docs.python.org/3/library/signal.html#module-contents
        """

        async def signal_handler(sig: signal.Signals):
            try:
                logger.debug(
                    f"Block {block.block_name} with id {block.id} received "
                    f"a signal {sig.name}"
                )
                await block.signal_handler(sig=sig)
            except Exception as e:
                block.exception(
                    e,
                    format="Exception in {block_name} signal handler: {exception}",
                    reraise=False,
                )

        def callback_fn(sig: signal.Signals):
            return asyncio.ensure_future(signal_handler(sig))

        for signum in signums:
            sig = signal.Signals(signum)  # Make sure this is a Signals instance
            self.loop.add_signal_handler(sig, callback_fn, sig)
            logger.debug(f"Registered signal {sig.name} for {block.block_name}")

    def register_task(self, awaitable: Awaitable) -> None:
        """Register a task that will be run in Runner's loop.

        :param awaitable: Either a coroutine, task or future that will be added
            to the task list to be schedule inside main loop in i3pyblocks.
        """
        task = asyncio.ensure_future(awaitable)
        self.tasks.append(task)
        logger.debug(f"Registered async task {awaitable} in {self}")

    async def register_block(
        self,
        block: blocks.Block,
        signals: Iterable[Union[int, signal.Signals]] = (),
    ) -> None:
        """Registers a Block that will be run and managed by Runner.

        This will register a new Block in Runner and also make sure that
        everything is ready to run the Block correctly.

        Optionally it will also register any Unix signals that the Block wants
        to wait for events (see :meth:`register_signal()` method).

        :param block: instance of :class:`~i3pyblocks.blocks.base.Block` instance
            that will be registered inside Runner's main loop.

        :param signums: Any iterable containing signal numbers, can be either
            an int or a signal.Signals' enum. See :meth:`register_signal()`
            method for more information.
        """
        # Setup the block before starting it
        await block.setup(self.queue)

        self.blocks[block.id] = block
        # This only works correctly because from Python 3.7+ dict is ordered
        self.results[block.id] = None
        self.register_task(block.start())

        if signals:
            self.register_signal(block, signals)

    async def update_results(self) -> None:
        """Get updated results from registed Blocks."""
        id_, result = await self.queue.get()
        self.results[id_] = result
        self.queue.task_done()

        # To reduce the number of redraws, let's empty the queue here
        # and draw all available updates
        while self.queue.qsize() > 0:
            id_, result = self.queue.get_nowait()
            self.results[id_] = result

    async def write_results(self) -> None:
        """Writes results to stdout.

        This is a endless loop that will wait for an update in any Block,
        get this update and print all Blocks results using the format
        described in https://i3wm.org/docs/i3bar-protocol.html#_the_protocol.
        """
        while True:
            await self.update_results()
            output = list(self.results.values())
            print(json.dumps(output), end=",\n", flush=True)

    async def click_event(self, raw: AnyStr) -> None:
        """Parses a click event, passing it to a Block's ``click_handler()``.

        Receives a click event from stdin in JSON format, parses it, finds
        the correspondent :class:`~i3pyblocks.blocks.base.Block` and calls its
        :meth:`~i3pyblocks.blocks.base.Block.click_handler` method.

        :param raw: A JSON formatted string with the click event, as described
            in https://i3wm.org/docs/i3bar-protocol.html#_click_events.
        """
        try:
            click_event = json.loads(raw)
            instance = click_event["instance"]
            id_ = uuid.UUID(instance)
            block = self.blocks[id_]

            logger.debug(
                f"Block {block.block_name} with id {block.id} received"
                f" a click event: {click_event}"
            )

            await block.click_handler(
                x=click_event.get("x"),
                y=click_event.get("y"),
                button=click_event.get("button"),
                relative_x=click_event.get("relative_x"),
                relative_y=click_event.get("relative_y"),
                width=click_event.get("width"),
                height=click_event.get("height"),
                modifiers=click_event.get("modifiers"),
            )
        except Exception as e:
            block.exception(
                e,
                format="Exception in {block_name} click handler: {exception}",
                reraise=False,
            )

    # Based on: https://git.io/fjbHx
    async def click_events(self) -> None:
        """Reads stdin for new click events."""
        reader = await misc.get_aio_reader(self.loop)
        await reader.readline()

        while True:
            raw = await reader.readuntil(b"}")
            await self.click_event(raw)
            await reader.readuntil(b",")

    def stop(self) -> None:
        """Stops the Runner."""
        for task in self.tasks:
            task.cancel()

    async def start(self, timeout: Optional[int] = None) -> None:
        """Starts the Runner.

        This will first print the header as specified in
        https://i3wm.org/docs/i3bar-protocol.html#_the_protocol, declaring
        the capabilities of i3pyblocks to i3bar.

        Afterwards it will run forever printing to stdout the updates from
        the registered Blocks in the format expected by i3bar, and will also
        reads stdin for any click events coming from i3bar.

        :param timeout: Time in seconds to stop the Runner. This is mostly used
            by tests or debug purposes.
        """
        self.register_task(self.click_events())
        self.register_task(self.write_results())

        print(json.dumps({"version": 1, "click_events": True}), end="\n[\n", flush=True)

        await asyncio.wait(self.tasks, timeout=timeout)

        # This is a hack so we can end with a valid JSON, since there is
        # probably some trailing comma somewhere
        print("null\n]")

        self.stop()
