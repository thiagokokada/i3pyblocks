import aiohttp
from aiohttp import web

from i3pyblocks.blocks import aiohttp as m_aiohttp


async def test_polling_request_block(aiohttp_server):
    async def hello_handler(request):
        return web.Response(text="Hello")

    app = web.Application()
    app.router.add_post("/", hello_handler)
    server = await aiohttp_server(app)

    instance = m_aiohttp.PollingRequestBlock(
        url=f"http://127.0.0.1:{server.port}",
        method="post",
        format="{status} {response}",
    )

    await instance.run()

    assert instance.result()["full_text"] == "200 Hello"


async def test_polling_request_block_error(aiohttp_server):
    # Host doesn't exist
    instance = m_aiohttp.PollingRequestBlock(
        url="http://127.0.0.1:12345",
        format_error="{exception:.14s}",
    )

    await instance.run()

    assert instance.result()["full_text"] == "Cannot connect"

    # Timeout
    instance = m_aiohttp.PollingRequestBlock(
        url="http://128.0.0.1:12345",
        request_opts={
            "timeout": aiohttp.ClientTimeout(total=0.1),
        },
    )

    await instance.run()

    assert instance.result()["full_text"] == "ERROR"


async def test_polling_request_block_with_callback(aiohttp_server):
    async def json_handler(request):
        return web.json_response({"hello": "world"})

    async def json_callback(resp):
        j = await resp.json()
        return f"Hello {j['hello']}"

    app = web.Application()
    app.router.add_get("/", json_handler)
    server = await aiohttp_server(app)

    instance = m_aiohttp.PollingRequestBlock(
        url=f"http://127.0.0.1:{server.port}",
        response_callback=json_callback,
    )

    await instance.run()

    assert instance.result()["full_text"] == "Hello world"
