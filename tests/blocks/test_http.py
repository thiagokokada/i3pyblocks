import pytest

aiohttp = pytest.importorskip("aiohttp")
aiohttp_web = pytest.importorskip("aiohttp.web")
http = pytest.importorskip("i3pyblocks.blocks.http")


async def test_polling_request_block(aiohttp_server):
    async def hello_handler(request):
        return aiohttp_web.Response(text="Hello")

    app = aiohttp_web.Application()
    app.router.add_post("/", hello_handler)
    server = await aiohttp_server(app)

    instance = http.PollingRequestBlock(
        url=f"http://127.0.0.1:{server.port}",
        method="post",
        format="{status} {response}",
    )

    await instance.run()

    assert instance.result()["full_text"] == "200 Hello"


async def test_polling_request_block_error(aiohttp_server):
    # Host doesn't exist
    instance = http.PollingRequestBlock(
        url="http://127.0.0.1:12345",
        format_error="{exception:.14s}",
    )

    await instance.run()

    assert instance.result()["full_text"] == "Cannot connect"

    # Timeout
    instance = http.PollingRequestBlock(
        url="http://128.0.0.1:12345",
        request_opts={
            "timeout": aiohttp.ClientTimeout(total=0.1),
        },
    )

    await instance.run()

    assert instance.result()["full_text"] == "ERROR"


async def test_polling_request_block_with_callback(aiohttp_server):
    async def json_handler(request):
        return aiohttp_web.json_response({"hello": "world"})

    async def json_callback(resp):
        j = await resp.json()
        return f"Hello {j['hello']}"

    app = aiohttp_web.Application()
    app.router.add_get("/", json_handler)
    server = await aiohttp_server(app)

    instance = http.PollingRequestBlock(
        url=f"http://127.0.0.1:{server.port}",
        response_callback=json_callback,
    )

    await instance.run()

    assert instance.result()["full_text"] == "Hello world"
