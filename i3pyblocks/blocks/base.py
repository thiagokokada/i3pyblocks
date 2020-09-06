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
from typing import List, Optional

from i3pyblocks import core, types
from i3pyblocks._internal import utils


class Block(metaclass=abc.ABCMeta):
    """Base Block.

    A Block represents each part that composes an i3pyblocks output. It is
    responsible extracting, parsing and processing the information, and also
    formatting so it can be output in i3bar later.

    This is an abstract class defining the interface for what a Block is.
    It should not be used directly, instead it should be derivated and its
    abstract methods should be implemented.

    Keyword Args:
      block_name:
        Allows you to set a custom internal representation for the class.
        This should only be useful if you need to differentiate between
        multiple instances of the same module in a consistent way (i.e.:
        you can't rely on something random like the `Module.id`).
        If not passed this will use by default the string representation
        of the class name.
      default_state:
        Defines the default state of the Block, that is, the value that will
        be shown unless the state is updated by Block's `update_state()` method.
        For example, let's say you want a block that has a permanent green
        background (unless overriden), so you can do something like::

            block_instance = Block(default_state={"background": "#008000"})

        And all calls to `result()` will have ``background == "#008000"``,
        unless overriden by ``update_status()`` with a different value.

    See Also:
      For details about each of the keys available in ``default_state``, see
      ``update_state()`` documentation.
    """

    def __init__(
        self,
        *,
        block_name: Optional[str] = None,
        default_state: types.Dictable[str, Optional[types.Value]] = (
            ("color", None),
            ("background", None),
            ("border", None),
            ("border_top", None),
            ("border_right", None),
            ("border_bottom", None),
            ("border_left", None),
            ("min_width", None),
            ("align", types.AlignText.LEFT),
            ("urgent", False),
            ("separator", True),
            ("separator_block_width", None),
            ("markup", types.MarkupText.NONE),
        ),
    ) -> None:
        self.id = uuid.uuid4()
        self.block_name = block_name or self.__class__.__name__
        self.frozen = True
        self.update_queue: Optional[asyncio.Queue] = None

        # Those are default values for properties if they are not overriden
        self._default_state = utils.non_nullable_dict(
            name=self.block_name, instance=str(self.id), **dict(default_state)
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
        unless another update occurs before a Block's ``push_update()`` method
        is called.

        Each of this method arguments is from `i3bar's protocol specification`_,
        since they're mapped directly from it (so a ``full_text="foo"`` results
        in a ``{"full_text": "foo"}`` in the Block's output).

        Args:
          full_text:
            The full_text will be displayed by i3bar on the status line. This
            is the only required parameter. If full_text is an empty string, the
            block will be skipped.
          short_text:
            It will be used in case the status line needs to be shortened because
            it uses more space than your screen provides.
          color:
            To make the current state of the information easy to spot, colors can
            be used. Colors are specified in hex (like in HTML), starting with a
            leading hash sign. For example, #ff0000 means red.
          background:
            Overrides the background color for this particular block.
          border:
            Overrides the border color for this particular block.
          border_top:
            Defines the width (in pixels) of the top border of this block.
            Defaults to 1.
          border_right:
            Defines the width (in pixels) of the right border of this block.
            Defaults to 1.
          border_bottom:
            Defines the width (in pixels) of the bottom border of this block.
            Defaults to 1.
          border_left:
            Defines the width (in pixels) of the left border of this block.
            Defaults to 1.
          min_width:
            The minimum width (in pixels) of the block. If the content of the
            full_text key take less space than the specified min_width, the
            block will be padded to the left and/or the right side, according
            to the align key.
          align:
            Align text on the center, right or left (default) of the block,
            when the minimum width of the latter, specified by the min_width
            key, is not reached.
          urgent:
            A boolean which specifies whether the current value is urgent.
          separator:
            A boolean which specifies whether a separator line should be
            drawn after this block. The default is true, meaning the separator
            line will be drawn.
          separator_block_width:
            The amount of pixels to leave blank after the block. In the middle
            of this gap, a separator line will be drawn unless separator is
            disabled.
          markup:
            A string that indicates how the text of the block should be parsed.
            Pango markup only works if you use a pango font.

        .. _i3bar's protocol specification:
          https://i3wm.org/docs/i3bar-protocol.html#_blocks_in_detail
        """
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

    def result(self) -> types.Result:
        """Returns the current state of Block as a Result map.

        This will combine both the default state and the current state to
        generate the current state of the Block.

        Returns:
          A ``i3pyblocks.types.Result`` map, ready to be converted to JSON.
          For example::

            {
               "full_text": "Some funny text",
               "background": "#FF0000",
            }
        """
        return {**self._default_state, **self._state}

    def push_update(self) -> None:
        """Push result to queue, so it can be retrieved by Runner."""
        if self.update_queue and not self.frozen:
            self.update_queue.put_nowait((self.id, self.result()))
        else:
            core.logger.warning(
                f"Not pushing update since block {self.block_name} with "
                f"id {self.id} is either not initialized or frozen"
            )

    def update(self, *args, **kwargs) -> None:
        """Updates a Block.

        This method will immediately updates a Block, so its new contents
        should be shown in the next redraw of i3bar. It is basically the
        equivalent of calling Method's ``update_state()`` followed by
        ``push_update()``.

        The parameters of this method is passed as-is to Block's
        ``update_state()``.

        See Also:
          ``Block.update_state()`` arguments.
        """
        self.update_state(*args, **kwargs)
        self.push_update()

    def abort(self, *args, **kwargs) -> None:
        """Aborts a Block.

        This method will do one last update of the Block, and disable all
        further updates on it. Useful to show errors.

        Note that this does not necessary stops the Block from working
        (i.e.: its loop may still be running), it just stops the updates
        from showing in i3bar.

        The parameters of this method is passed as-is to Block's
        ``update_state()``.

        See Also:
          ``Block.update_state()`` arguments.
        """
        self.update(*args, **kwargs)
        self.frozen = True

    def setup(self, queue: asyncio.Queue) -> None:
        """Setup a Block.

        This method is called just before ``start()`` to setup some things
        necessary to make the Block work.

        While you may put your own initialization code here, don't forget
        to call ``super().setup(queue=queue)`` after overriding this method,
        so everything works correctly.

        Args:
          queue:
            ``asyncio.Queue`` instance that will be used to notify updates
            from this Block.
        """
        self.update_queue = queue
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

        Each of this method arguments is from `i3bar's protocol specification`_,
        since they're mapped directly (so a ``{"x": 1}`` results in a ``x=1``).

        Keyword Args:
          x:
            X11 root window coordinates where the click occurred.
          y:
            X11 root window coordinates where the click occurred.
          button:
            X11 button ID (for example 1 to 3 for left/middle/right mouse
            button).
          relative_x:
            Coordinates where the click occurred, with respect to the top left
            corner of the block.
          relative_y:
            Coordinates where the click occurred, with respect to the top left
            corner of the block.
          width:
            Width (in px) of the block.
          height:
            Height (in px) of the block.
          modifier:
            A list of the modifiers active when the click occurred. The
            order in which modifiers are listed is not guaranteed.

        See Also:
          ``i3pyblocks.types.MouseButton`` has the mapping of the available
          mouse button IDs.
          ``i3pyblocks.types.KeyModifier`` has the mapping of the available
          modifiers.

        .. i3bar's protocol specification:
          https://i3wm.org/docs/i3bar-protocol.html#_click_events
        """
        pass

    async def signal_handler(self, *, sig: signal.Signals) -> None:
        """Callback called when a signal event happens to this Block.

        Keyword Args:
          sig:
            Signals enum with the signal that originated this event. This can
            be used to differentiate between different signals.
        """
        pass

    @abc.abstractmethod
    async def start(self) -> None:
        """Starts a Block.

        This is an abstract method, so it should be overriden.

        This method is where you generally wants to put your main loop to
        update the state of the Block. This loop can either be triggered by
        events or can be an infinity loop. It can even be a single call
        to ``update()``, but in this case your Block will only be updated
        once.
        """
        pass


class PollingBlock(Block):
    """Polling Block.

    This is the most common Block implementation. It is a Block that runs
    a loop where it executes ``run()`` method and sleeps for ``sleep`` seconds,
    afterwards running ``run()`` again, keeping this cycle forever.

    You must not instantiate this class directly, instead you should
    subclass it and implement ``run()`` method first.

    Args:
      sleep: sleep in seconds between each call to ``run()``.

    See Also:
      ``Block()`` arguments.
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
            while True:
                await self.run()
                await asyncio.sleep(self.sleep)
        except Exception as e:
            core.logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e


class ExecutorBlock(Block):
    """Executor Block.

    This is a special Block implementation to be used when it is not possible
    to implement functionality using asyncio, for example, when a external
    library uses its own event loop.

    What this block does is to call ``run()`` method inside an `executor`_,
    that is run in a separate thread or process depending of the selected
    executor. Since it is running in a separate thread/process, it does not
    interfere with the main asyncio loop.

    You must not instantiate this class directly, instead you should
    subclass it and implement ``run()`` method first.

    Args:
      executor: an optional `Executor instance`_. If not passed it
    will use the default one.

    See also:
      ``Block()`` arguments.

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
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self.run)
        except Exception as e:
            core.logger.exception(f"Exception in {self.block_name}")
            self.abort(f"Exception in {self.block_name}: {e}", urgent=True)
            raise e
