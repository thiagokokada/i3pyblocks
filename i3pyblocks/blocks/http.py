"""Blocks related to HTTP requests, based on `aiohttp`_.

This module contains PollingRequestBlock, that uses ``aiohttp`` to request HTTP
endpoints and shows the result in i3bar.

Since requesting HTTP can takes quite sometime, it is very important that we
use an async library for this task or we could block updates in i3pyblocks
until the end of the HTTP request. ``aiohttp`` fits this task very well.

PollingRequestBlock is based on ``PollingBlock`` since the idea of this Block
is to be used for things like weather updates, for example::

    PollingRequestBlock("https://wttr.in/?format=%c+%t")

But more advanced Blocks could update in response for a Webhook or a system
event (for example, a network change could trigger a request to get external
IP).

.. _aiohttp:
    https://github.com/aio-libs/aiohttp
"""

import asyncio
from typing import Any, Awaitable, Callable, Mapping

import aiohttp

from i3pyblocks import blocks, logger

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=5)


async def text_callback(resp: aiohttp.ClientResponse) -> str:
    """Returns the response result as text.

    Mostly useful for endpoints that returns just text on its output. Some
    examples::

        $ curl ifconfig.me/ip
        123.123.123.123
        $ curl 'wttr.in/?format=%t'
        +31°C
    """
    return await resp.text()


class PollingRequestBlock(blocks.PollingBlock):
    r"""Block that shows result of a periodic HTTP request.

    This Block continuously request a specified endpoint and shows the result
    and status code of the request in i3bar.

    :param format: Format string showed after a successful request. Supports
        both ``{response}`` and ``{status}`` placeholders.

    :param format_error: Format string showed in case of an error in request.

    :param request_opts: A mapping of options passed directly to the ``request()``
        method in ``aiohttp``. The list of available parameters
        is `aiohttp docs`_.

    :param response_callback: A function that will be called after the response
        is made to format the result. For example, consider an endpoiint that
        returns the JSON ``{"hello": "world"}``. We could format its output
        using::

            def json_callback(resp):
                j = await resp.json()
                return f"Hello {j['hello']}"

        This function would result in ``Hello world`` on ``{response}``
        placeholder.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.

    .. _aiohttp docs:
      https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession.request
    """

    def __init__(
        self,
        url: str,
        method: str = "get",
        format: str = "{response}",
        format_error: str = "ERROR",
        request_opts: Mapping[str, Any] = {"timeout": DEFAULT_TIMEOUT},
        response_callback: Callable[
            [aiohttp.ClientResponse], Awaitable[str]
        ] = text_callback,
        sleep: int = 60,
        **kwargs
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.format_error = format_error
        self.url = url
        self.method = method
        self.response_callback = response_callback
        self.request_opts = request_opts

    async def run(self) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=self.url,
                    **self.request_opts,
                ) as resp:
                    response = await self.response_callback(resp)

                    self.update(
                        self.ex_format(
                            self.format,
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
            logger.exception(exception)
