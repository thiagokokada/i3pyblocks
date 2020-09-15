import asyncio
import sys
from typing import Dict, Optional

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


async def get_aio_reader(loop: asyncio.AbstractEventLoop) -> asyncio.StreamReader:
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    return reader
