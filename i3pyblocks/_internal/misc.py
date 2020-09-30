import asyncio
import sys
from functools import partial, wraps
from typing import Dict, Optional, cast

from i3pyblocks._internal import models


def calculate_threshold(items: models.Threshold, value: float) -> Optional[str]:
    """Calculates the threshold based on the current value and a dict."""
    selected_item = None

    for threshold, item in dict(items).items():
        if value >= threshold:
            selected_item = item
        else:
            break

    return selected_item


def non_nullable_dict(**kwargs) -> Dict:
    """Returns a dict without its keys with None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


def run_async(fn: models.Decorator) -> models.Decorator:
    r"""Calls an sync function async.

    Based on here: https://dev.to/0xbf/turn-sync-function-to-async-python-tips-58nn.

    Basically it wraps an sync function and runs it inside a `executor`_,
    so it runs it inside a thread or a processor and waits for it results.

    It is meant to be used as a decorator, so if you want you can do::

        @run_async
        def sync_func(a, b):
            pass

        await sync_func(1, b=2)

    Or if you just want to use it directly::

        await run_async(sync_func)(1, b=2)

    :param executor: `Executor`_ to be used to make the function async.

    :param \*args: Arguments passed to the function to be wrapped.

    :param \*\*kwargs: Keyword arguments passed to the function to be wrapped.

    .. _`executor`:
        https://docs.python.org/3/library/concurrent.futures.html#executor-objects
    """

    @wraps(fn)
    async def run(*args, executor=None, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(fn, *args, **kwargs))

    return cast(models.Decorator, run)


async def get_aio_reader(loop: asyncio.AbstractEventLoop) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    return reader
