"""i3pyblocks block.

This module includes implementation for the Block class, used to represent a
i3bar block. It also includes some more advanced implementations of Block
class, like PollingBlock.
"""

import abc
import asyncio
import signal
import uuid
from concurrent.futures import Executor
from typing import Callable, List, Optional

from i3pyblocks import formatter, logger
from i3pyblocks._internal import misc, models


class Block(metaclass=abc.ABCMeta):
    """Base Block.

    A Block represents each part that composes an i3pyblocks output. It is
    responsible extracting, parsing and processing the information, and also
    formatting so it can be output in i3bar later.

    This is an abstract class defining the interface for what a Block is.
    It should not be used directly, instead it should be derivated and its
    abstract methods should be implemented.

    :param block_name: Allows you to set a custom internal representation for
        the class. This should only be useful if you need to differentiate
        between multiple instances of the same module in a consistent way
        (i.e.: you can't rely on something random like the :attr:`id`).
        If not passed this will use by default the string representation of
        the class name.

    :param default_state: Defines the default state of the Block, that is, the
        value that will be shown unless the state is updated by
        :meth:`update_state()` method. For example, let's say you want a block
        that has a permanent green background (unless overriden), so you can do
        something like::

            block_instance = Block(
                default_state={
                    "background": "#008000",
                },
            )

        And all calls to :meth:`result()` will have ``background == "#008000"``,
        unless overriden by :meth:`update_state()` with a different value.

    :ivar id: Unique identifier for Block based on UUIDv4.

    :cvar ex_format: Reference of :class:`~i3pyblocks.formatter.ExtendedFormatter`'s
        ``format()`` method available to all children. Supports some additional
        funcionality compared to the default ``str().format()`` method, for
        example::

            s = "HellO WorlD!"
            print(self.ex_format("{!u}", s))  # "HELLO WORLD!"
            print(self.ex_format("{!l}", s))  # "hello world!"
            print(self.ex_format("{!c}", s))  # "Hello world!"
            print(self.ex_format("{!t}", s))  # "Hello World!"

    .. seealso::

        For details about each of the keys available in ``default_state``
        parameter, see :meth:`update_state()` documentation.
    """

    ex_format: Callable[..., str] = formatter.ExtendedFormatter().format

    def __init__(
        self,
        *,
        block_name: Optional[str] = None,
        default_state: Optional[models.State] = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.block_name = block_name or self.__class__.__name__
        self.frozen = True
        self.update_queue: Optional[asyncio.Queue] = None

        # Those are default values for properties if they are not overriden
        self._default_state = misc.non_nullable_dict(
            name=self.block_name, instance=str(self.id), **(default_state or {})
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
        align: Optional[str] = None,
        urgent: Optional[bool] = None,
        separator: Optional[bool] = None,
        separator_block_width: Optional[int] = None,
        markup: Optional[str] = None,
    ) -> None:
        """Updates Block's state.

        The state is what will be shown by the Block in the next update,
        unless another update occurs before a Block's :meth:`push_update`
        method is called.

        Each of this method arguments is from `blocks in i3bar protocol`_,
        since they're mapped directly from it (so a ``full_text="foo"`` results
        in a ``{"full_text": "foo"}`` in the Block's output).

        :param full_text: The full_text will be displayed by i3bar on the status
            line. This is the only required parameter. If full_text is an empty
            string, the block will be skipped.

        :param short_text: It will be used in case the status line needs to be
            shortened because it uses more space than your screen provides.

        :param color: To make the current state of the information easy to spot,
            colors can be used. Colors are specified in hex (like in HTML),
            starting with a leading hash sign. For example, #ff0000 means red.

        :param background: Overrides the background color for this particular
            block.

        :param border: Overrides the border color for this particular block.

        :param border_top: Defines the width (in pixels) of the top border of
            this block. Defaults to 1.

        :param border_right: Defines the width (in pixels) of the right border
            of this block. Defaults to 1.

        :param border_bottom: Defines the width (in pixels) of the bottom border
            of this block. Defaults to 1.

        :param border_left: Defines the width (in pixels) of the left border of
            this block. Defaults to 1.

        :param min_width: The minimum width (in pixels) of the block. If the
            content of the full_text key take less space than the specified
            min_width, the block will be padded to the left and/or the right
            side, according to the align key.

        :param align: Align text on the center, right or left (default) of the
            block, when the minimum width of the latter, specified by the
            min_width key, is not reached.

        :param urgent: A boolean which specifies whether the current value is
            urgent.

        :param separator: A boolean which specifies whether a separator line
            should be drawn after this block. The default is true, meaning the
            separator line will be drawn.

        :param separator_block_width: The amount of pixels to leave blank after
            the block. In the middle of this gap, a separator line will be
            drawn unless separator is disabled.

        :param markup: A string that indicates how the text of the block should
            be parsed. Pango markup only works if you use a pango font.

        .. _blocks in i3bar protocol:
            https://i3wm.org/docs/i3bar-protocol.html#_blocks_in_detail
        """
        self._state = misc.non_nullable_dict(
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

    def result(self) -> models.State:
        """Returns the current state of Block as a dict.

        This will combine both the default state and the current state to
        generate the current state of the Block.

        :returns: A :class:`~i3pyblocks._internal.models.State` dict, ready
            to be converted to JSON.
        """
        return {**self._default_state, **self._state}  # type: ignore

    def push_update(self) -> None:
        """Push result to queue, so it can be retrieved by Runner."""
        if self.update_queue and not self.frozen:
            self.update_queue.put_nowait((self.id, self.result()))
        else:
            logger.debug(
                f"Not pushing update since block {self.block_name} with "
                f"id {self.id} is either not initialized or frozen"
            )

    def update(self, *args, **kwargs) -> None:
        """Updates a Block.

        This method will immediately updates a Block, so its new contents
        should be shown in the next redraw of i3bar. It is basically the
        equivalent of calling Method's :meth:`update_state()` followed by
        :meth:`push_update()`.

        The parameters of this method is passed as-is to Block's
        :meth:`update_state()`.
        """
        self.update_state(*args, **kwargs)
        self.push_update()

    def abort(self, *args, **kwargs) -> None:
        """Aborts a Block.

        This method will do one last update of the Block, and disable all
        further updates on it. Useful to show errors.

        Note that this does not necessary stops the Block from working
        (i.e.: its loop may still be running), it just stops the updates
        from showing in i3bar. Each Block is responsible to stop updating
        after this method is called, if this is desired.

        The parameters of this method is passed as-is to Block's
        :meth:`update_state()`.
        """
        self.update(*args, **kwargs)
        self.frozen = True

    async def setup(self, queue: Optional[asyncio.Queue] = None) -> None:
        """Setup a Block.

        This method is called just before :meth:`start()` to setup some things
        necessary to make the Block work.

        If you want to do some kinda of async initialization, override
        this function and put your code here. However, do not forget to call
        ``await super().setup(queue=queue)`` after your code to prepare your
        Block for updates.

        :param queue: `asyncio.Queue`_ instance that will be used to notify
            updates from this Block.

        .. _asyncio.Queue:
            https://docs.python.org/3/library/asyncio-queue.html#asyncio.Queue
        """
        if queue:
            self.update_queue = queue
        else:
            self.update_queue = asyncio.Queue()
        self.frozen = False

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
        """Callback called when a click event happens to this Block.

        Each of this method arguments is from `click events in i3bar protocol`
        since they're mapped directly (so a ``{"x": 1}`` results in a ``x=1``).

        :param x: X11 root window coordinates where the click occurred.

        :param y: X11 root window coordinates where the click occurred.

        :param button: X11 button ID (for example 1 to 3 for left/middle/right
            mouse button).

        :param relative_x: Coordinates where the click occurred, with respect
            to the top left corner of the block.

        :param relative_y: Coordinates where the click occurred, with respect
            to the top left corner of the block.

        :param width: Width (in px) of the block.

        :param height: Height (in px) of the block.

        :param modifier: A list of the modifiers active when the click occurred.
            The order in which modifiers are listed is not guaranteed.

        .. seealso::

            :class:`i3pyblocks.types.MouseButton` has the mapping of the available
            mouse button IDs.

            :class:`i3pyblocks.types.KeyModifier` has the mapping of the available
            modifiers.

        .. _click events in i3bar protocol:
          https://i3wm.org/docs/i3bar-protocol.html#_click_events
        """
        pass

    async def signal_handler(self, *, sig: signal.Signals) -> None:
        """Callback called when a signal event happens to this Block.

        :param sig: `Signal enum`_ with the signal that originated this event.
            This can be used to differentiate between different signals.

        .. _Signal enum:
            https://docs.python.org/3/library/signal.html#module-contents
        """
        pass

    @abc.abstractmethod
    async def start(self) -> None:
        """Starts a Block.

        This is an abstract method, so it should be overriden.

        This method is where you generally wants to put your main loop to
        update the state of the Block. This loop can either be triggered by
        events or can be an infinity loop. It can even be a single call
        to :meth:`update()`, but in this case your Block will only be updated
        once.
        """
        pass


class PollingBlock(Block):
    """Polling Block.

    This is the most common Block implementation. It is a Block that runs
    a loop where it executes :meth:`run()` method and sleeps for ``sleep``
    seconds, afterwards running :meth:`run()` again, keeping this cycle forever.

    By default, a click or a signal event will refresh the contents of this
    Block.

    You must not instantiate this class directly, instead you should
    subclass it and implement :meth:`run()` method first.

    :param sleep: Sleep in seconds between each call to :meth:`run()`.
    """

    def __init__(self, sleep: int = 1, **kwargs) -> None:
        self.sleep = sleep
        super().__init__(**kwargs)

    @abc.abstractmethod
    async def run(self) -> None:
        """Main loop in PollingBlock.

        This is the method that will be run at each X ``sleep`` seconds.

        Since this is an abstract method, it should be overriden before usage.
        """
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

    async def start(self) -> None:
        try:
            while not self.frozen:
                await self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e


class ExecutorBlock(Block):
    """Executor Block.

    This is a special Block implementation to be used when it is not possible
    to implement functionality using asyncio, for example, when a external
    library uses its own event loop.

    What this block does is to call :meth:`run()` method inside an `executor`_,
    that is run in a separate thread or process depending of the selected
    executor. Since it is running in a separate thread/process, it does not
    interfere with the main asyncio loop.

    You must not instantiate this class directly, instead you should
    subclass it and implement :meth:`run()` method first.

    :param executor: An optional `Executor instance`_. If not passed it will
        use the default one.

    .. _executor:
        https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor
    .. _Executor instance:
        https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor
    """

    def __init__(self, executor: Optional[Executor] = None, **kwargs) -> None:
        self.executor = executor
        super().__init__(**kwargs)

    @abc.abstractmethod
    def run(self) -> None:
        """Main loop in PollingBlock.

        This is the method that will be run inside an executor.

        Since this is an abstract method, it should be overriden before usage.
        """
        pass

    async def start(self) -> None:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self.run)
        except Exception as e:
            logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e
