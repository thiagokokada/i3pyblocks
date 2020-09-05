import asyncio
from typing import Any, Awaitable, Callable

import aiohttp

from i3pyblocks import blocks, core, types

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=5)


async def text_callback(resp: aiohttp.ClientResponse) -> str:
    return await resp.text()


class RequestBlock(blocks.PollingBlock):
    def __init__(
        self,
        url: str,
        method: str = "get",
        format: str = "{response}",
        format_error: str = "ERROR",
        request_opts: types.Dictable[str, Any] = (("timeout", DEFAULT_TIMEOUT),),
        response_callback: Callable[
            [aiohttp.ClientResponse], Awaitable[str]
        ] = text_callback,
        sleep: int = 60,
        *,
        _aiohttp=aiohttp,
        **kwargs
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.format_error = format_error
        self.url = url
        self.method = method
        self.response_callback = response_callback
        self.request_opts = dict(request_opts)
        self.aiohttp = _aiohttp

    async def run(self) -> None:
        try:
            async with self.aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=self.url,
                    **self.request_opts,
                ) as resp:
                    response = await self.response_callback(resp)

                    self.update(
                        self.format.format(
                            response=response,
                            status=resp.status,
                        )
                    )
        except (
            aiohttp.ClientResponseError,
            aiohttp.ClientConnectorError,
            asyncio.TimeoutError,
        ) as exception:
            self.update(self.format_error.format(exception=str(exception)))
            core.logger.exception(exception)
