import asyncio
import sys
from functools import partial, wraps
from typing import Dict, Optional, cast

from i3pyblocks._internal import models


def calculate_threshold(items: models.Threshold, value: float) -> Optional[str]:
    selected_item = None

    for threshold, item in dict(items).items():
        if value >= threshold:
            selected_item = item
        else:
            break

    return selected_item


def non_nullable_dict(**kwargs) -> Dict:
    return {k: v for k, v in kwargs.items() if v is not None}


# https://dev.to/0xbf/turn-sync-function-to-async-python-tips-58nn
def run_async(fn: models.Decorator) -> models.Decorator:
    @wraps(fn)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(fn, *args, **kwargs))

    return cast(models.Decorator, run)


async def get_aio_reader(loop: asyncio.AbstractEventLoop) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    return reader
