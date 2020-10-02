import asyncio
import inspect
import sys
from concurrent.futures import Executor
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Dict, Optional

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


def delegates(to_f, delegated_params=["args", "kwargs"]):
    r"""Delegate function parameters signature.

    Based on here: https://www.fast.ai/2019/08/06/delegation/

    Allow delegation of functions or methods using ``*args`` and ``**kwargs``.
    Meant to be used as a decorator.

    For example::

        def foo(a, b):
            pass

        @delegates(foo)
        def bar(**kwargs):
            foo(**kwargs)

    When inspecting the parameters from ``bar``, we will have ``bar(a, b)``
    instead of ``bar(**kwargs)``.

    :param to_f: Target function/method to delegate.

    :param replace: Arguments to replace in the destination function.
    """

    def delegate_signature(from_f):
        from_sig = inspect.signature(from_f)
        from_params = dict(from_sig.parameters)
        for param in delegated_params:
            from_params.pop(param, None)

        to_sig = inspect.signature(to_f)
        to_params = dict(to_sig.parameters)

        new_params = {**to_params, **from_params}
        from_f.__signature__ = from_sig.replace(parameters=new_params.values())

        return from_f

    return delegate_signature


def run_async(fn: Callable, executor: Executor = None) -> Callable[..., Awaitable[Any]]:
    """Calls an sync function async.

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

    .. _`executor`:
        https://docs.python.org/3/library/concurrent.futures.html#executor-objects
    """

    @wraps(fn)
    async def run(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(fn, *args, **kwargs))

    return run


async def get_aio_reader(loop: asyncio.AbstractEventLoop) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    return reader
