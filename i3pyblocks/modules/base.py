import abc
import asyncio
import signal
import uuid
from concurrent.futures import Executor
from typing import List, Optional

from i3pyblocks import core, utils, types


class Module(metaclass=abc.ABCMeta):
    """Base Module

    This is an abstract class defining the interface for what a Module is.
    It should not be used directly.

    Each of this method parameters defines the default state of the Module,
    that is, the value that will be shown unless overriden by Module's
    update_state() method. For example, let's say you want a module that
    has a permanent green background (unless overriden), so you can do
    something like:

    ```python
    module_instance = Module(background="#008000")
    ```

    The parameters are based on [i3bar's protocol specification][1],
    since they're mapped directly (so a `full_text="foo"` results in a
    `{"full_text": "foo"}`), except for `instance` that is generated
    randomly.

      - *full*_text: the full_text will be displayed by i3bar on the
    status line. This is the only required parameter. If full_text is an
    empty string, the block will be skipped
      - *short*_text: it will be used in case the status line needs
    to be shortened because it uses more space than your screen provides
      - *color*: to make the current state of the information easy to spot,
    colors can be used. Colors are specified in hex (like in HTML),
    starting with a leading hash sign. For example, #ff0000 means red
      - *background*: overrides the background color for this particular
    block
      - *border*: overrides the border color for this particular block
      - *border*_top: defines the width (in pixels) of the top border of
    this block. Defaults to 1
      - *border*_right: defines the width (in pixels) of the right border
    of this block. Defaults to 1
      - *border*_bottom: defines the width (in pixels) of the bottom
    border of this block. Defaults to 1
      - *border*_left: defines the width (in pixels) of the left border of
    this block. Defaults to 1
      - *min*_width: The minimum width (in pixels) of the block. If the
    content of the full_text key take less space than the specified
    min_width, the block will be padded to the left and/or the right side,
    according to the align key
      - *align*: align text on the center, right or left (default) of the
    block, when the minimum width of the latter, specified by the
    min_width key, is not reached
      - *urgent*: a boolean which specifies whether the current value is
    urgent
      - *separator*: a boolean which specifies whether a separator line
    should be drawn after this block. The default is true, meaning the
    separator line will be drawn
      - *separator*_block_width: the amount of pixels to leave blank
    after the block. In the middle of this gap, a separator line will
    be drawn unless separator is disabled.
      - *markup*: a string that indicates how the text of the block
    should be parsed. Pango markup only works if you use a pango font.

    [1]: https://i3wm.org/docs/i3bar-protocol.html#_blocks_in_detail
    """

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
        align: Optional[str] = types.Align.LEFT,
        urgent: Optional[bool] = False,
        separator: Optional[bool] = True,
        separator_block_width: Optional[int] = None,
        markup: Optional[str] = types.Markup.NONE,
    ) -> None:
        self.id = uuid.uuid4()
        self.name = name or self.__class__.__name__
        self.frozen = True

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
            align=align,
            urgent=urgent,
            separator=separator,
            separator_block_width=separator_block_width,
            markup=markup,
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
        """Updates Module's state

        The state is what will be shown by the Module in the next update,
        unless another update occur before a Module's `push_update()` method
        is called.

        Each of this method arguments is from
        [i3bar's protocol specification][1], since they're mapped directly
        (so a `full_text="foo"` results in a `{"full_text": "foo"}`), except
        for `name` (that is defined once in Module's constructor) and
        `instance` (that is generate randomly).

          - *full*_text: the full_text will be displayed by i3bar on the
        status line. This is the only required parameter. If full_text is an
        empty string, the block will be skipped
          - *short*_text: it will be used in case the status line needs
        to be shortened because it uses more space than your screen provides
          - *color*: to make the current state of the information easy to spot,
        colors can be used. Colors are specified in hex (like in HTML),
        starting with a leading hash sign. For example, #ff0000 means red
          - *background*: overrides the background color for this particular
        block
          - *border*: overrides the border color for this particular block
          - *border*_top: defines the width (in pixels) of the top border of
        this block. Defaults to 1
          - *border*_right: defines the width (in pixels) of the right border
        of this block. Defaults to 1
          - *border*_bottom: defines the width (in pixels) of the bottom
        border of this block. Defaults to 1
          - *border*_left: defines the width (in pixels) of the left border of
        this block. Defaults to 1
          - *min*_width: The minimum width (in pixels) of the block. If the
        content of the full_text key take less space than the specified
        min_width, the block will be padded to the left and/or the right side,
        according to the align key
          - *align*: align text on the center, right or left (default) of the
        block, when the minimum width of the latter, specified by the
        min_width key, is not reached
          - *urgent*: a boolean which specifies whether the current value is
        urgent
          - *separator*: a boolean which specifies whether a separator line
        should be drawn after this block. The default is true, meaning the
        separator line will be drawn
          - *separator*_block_width: the amount of pixels to leave blank
        after the block. In the middle of this gap, a separator line will
        be drawn unless separator is disabled.
          - *markup*: a string that indicates how the text of the block
        should be parsed. Pango markup only works if you use a pango font.

        [1]: https://i3wm.org/docs/i3bar-protocol.html#_blocks_in_detail
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
        """Returns the current state of Module as a Result map

        This will combine both the default state and the current state to
        generate the current state of the Module.
        """
        return {**self._default_state, **self._state}

    def push_update(self) -> None:
        """Push result to queue, so it can be retrieved"""
        if not self.frozen:
            self.update_queue.put_nowait((self.id, self.result()))
        else:
            core.logger.warn(
                f"Not pushing update since module {self.name} with "
                f"id {self.id} is frozen"
            )

    def update(self, *args, **kwargs) -> None:
        """Updates a Module

        This method will immediately updates a Module, so its new contents
        should be shown in the next redraw of i3bar. It is basically the
        equivalent of calling Method's `update_state()` followed by
        `push_update()`.

        The parameters of this method is passed as-is to Module's
        `update_state()`.

        **See also**: `Module.update_state()` parameters.
        """
        self.update_state(*args, **kwargs)
        self.push_update()

    def abort(self, *args, **kwargs) -> None:
        """Aborts a Module

        This method will do one last update of the Module, and disable all
        further updates on it. Useful to show errors.

        Note that this does not necessary stops the Module from working
        (i.e.: its loop may still be running), it just stops the updates
        from showing in i3bar.

        The parameters of this method is passed as-is to Module's
        `update_state()`.

        **See also**: `Module.update_state()` parameters.
        """
        self.update(*args, **kwargs)
        self.frozen = True

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
        """Callback called when a click event happens to this Module

        Each of this method arguments is from
        [i3bar's protocol specification][1], since they're mapped directly
        (so a `{"x": 1}` results in a `x=1`), except for `name` (that is
        defined once in Module's constructor) and `instance` (that is
        generate randomly).

          - *x*: X11 root window coordinates where the click occurred
          - *y*: X11 root window coordinates where the click occurred
          - *button*: X11 button ID (for example 1 to 3 for left/middle/right
        mouse button)
          - *relative*_x: coordinates where the click occurred, with respect
        to the top left corner of the block
          - *relative*_y: coordinates where the click occurred, with respect
        to the top left corner of the block
          - *width*: width (in px) of the block
          - *height*: height (in px) of the block
          - *modifier*: an array of the modifiers active when the click
        occurred. The order in which modifiers are listed is not guaranteed.

        [1]: https://i3wm.org/docs/i3bar-protocol.html#_click_events
        """
        pass

    async def signal_handler(self, *, sig: signal.Signals) -> None:
        """Callback called when a signal event happens to this Module

          - *sig*: signals.Signals' enum with the signal that originated
        this event
        """
        pass

    @abc.abstractmethod
    async def start(self, queue: asyncio.Queue = None) -> None:
        """Starts a Module

        This is an abstract method, so it should be overriden by any children.
        However it is also recommended to call this function from any
        children, since it does some necessary setup so the Module works
        correctly.

          - *queue*: asyncio.Queue instance that will be used to notify
        updates from this Module
        """
        if not queue:
            queue = asyncio.Queue()
        self.update_queue = queue
        self.frozen = False


class PollingModule(Module):
    """Polling Module

    This is the most simple Module implementation. It is a module that runs
    a loop where it executes `run()` method and sleeps for `sleep` seconds.

    You must not instantiate this class directly, instead you should
    subclass it and implement `run()` method first.

      - *sleep*: sleep in seconds between update

    **See also:** `Module()` parameters.
    """

    def __init__(self, sleep: int = 1, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sleep = sleep

    @abc.abstractmethod
    async def run(self) -> None:
        """Main loop in PollingModule

        This is the method that will be run at each X `sleep` seconds. Since
        this is an abstract method, it should be overriden by its children.
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
    """Executor Module

    This is a special Module implementation to be used when it is not possible
    to implement functionality using asyncio, for example, when a external
    library uses its own event loop.

    What this module does is to call `run()` method inside a [executor][1],
    that is run in a separate thread or process depending of the selected
    executor. Since it is running in a separate thread/process, it does not
    interfere with the main asyncio loop.

    You must not instantiate this class directly, instead you should
    subclass it and implement `run()` method first.

      - *executor*: an optional [`Executor`][2] instance. If not passed it
    will use the default one

    **See also:** `Module()` parameters.

    [1]: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor
    [2]: https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor
    """

    def __init__(self, executor: Optional[Executor] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.executor = executor

    @abc.abstractmethod
    def run(self) -> None:
        """Main loop in PollingModule

        This is the method that will be run inside a executor. Since this
        is an abstract method, it should be overriden by its children.
        """
        pass

    async def start(self, queue: asyncio.Queue = None) -> None:
        await super().start(queue)
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self.run)
        except Exception as e:
            core.logger.exception(f"Exception in {self.name}")
            self.abort(f"Exception in {self.name}: {e}", urgent=True)
