from aiohttp import web

from i3pyblocks.blocks import aiohttp as m_aiohttp


async def test_request_block(aiohttp_server):
    async def hello_handler(request):
        return web.Response(text="Hello")

    app = web.Application()
    app.router.add_get("/", hello_handler)
    server = await aiohttp_server(app)

    instance = m_aiohttp.RequestBlock(url=f"http://127.0.0.1:{server.port}")

    await instance.run()

    assert instance.result()["full_text"] == "Hello"


async def test_request_block_with_callback(aiohttp_server):
    async def json_handler(request):
        return web.json_response({"hello": "world"})

    async def json_callback(resp):
        j = await resp.json()
        return j["hello"]

    app = web.Application()
    app.router.add_get("/", json_handler)
    server = await aiohttp_server(app)

    instance = m_aiohttp.RequestBlock(
        url=f"http://127.0.0.1:{server.port}",
        format="{response_callback}",
        response_callback=json_callback,
    )

    await instance.run()

    assert instance.result()["full_text"] == "world"
