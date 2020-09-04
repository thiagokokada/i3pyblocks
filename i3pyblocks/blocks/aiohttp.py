import aiohttp
from typing import Any, Awaitable, Callable

from i3pyblocks import blocks, types


async def empty_callback(_resp: aiohttp.ClientResponse) -> str:
    return ""


class RequestBlock(blocks.PollingBlock):
    def __init__(
        self,
        url: str,
        method: str = "get",
        format: str = "{text}",
        request_opts: types.Dictable[str, Any] = (),
        response_callback: Callable[
            [aiohttp.ClientResponse], Awaitable[str]
        ] = empty_callback,
        sleep: int = 60,
        *,
        _aiohttp=aiohttp,
        **kwargs
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.url = url
        self.method = method
        self.response_callback = response_callback
        self.request_opts = dict(request_opts)
        self.aiohttp = _aiohttp

    async def run(self) -> None:
        async with self.aiohttp.ClientSession() as session:
            async with session.request(
                method=self.method,
                url=self.url,
                **self.request_opts,
            ) as resp:
                response_callback = await self.response_callback(resp)

                if "{text}" in self.format:
                    text = await resp.text()
                else:
                    text = None

                self.update(
                    self.format.format(
                        response_callback=response_callback,
                        text=text,
                        status=resp.status,
                    )
                )
