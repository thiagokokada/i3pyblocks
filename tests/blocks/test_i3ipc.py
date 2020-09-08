import pytest
from asynctest import CoroutineMock, Mock
from helpers import misc, task

i3ipc = pytest.importorskip("i3ipc")
i3ipc_aio = pytest.importorskip("i3ipc.aio")
m_i3ipc = pytest.importorskip("i3pyblocks.blocks.i3ipc")


@pytest.mark.asyncio
async def test_window_title_block():
    mock_i3ipc = Mock(i3ipc)
    mock_i3ipc_aio = Mock(i3ipc_aio)

    mock_connection = mock_i3ipc_aio.Connection.return_value
    # For some reason asynctest.Mock didn't work here
    mock_connection.connect = CoroutineMock()
    mock_connection.main = CoroutineMock()
    mock_connection.get_tree = CoroutineMock()

    tree_mock = mock_connection.get_tree.return_value
    window_mock = tree_mock.find_focused
    window_mock.return_value = misc.AttributeDict(name="Hello")

    instance = m_i3ipc.WindowTitleBlock(_i3ipc=mock_i3ipc, _i3ipc_aio=mock_i3ipc_aio)
    await task.runner([instance.start()])

    result = instance.result()
    assert result["full_text"] == "Hello"

    await instance.clear_title()

    result = instance.result()
    assert result["full_text"] == ""

    # Sometimes window.name returns None
    window_mock.return_value = misc.AttributeDict(name=None)
    await instance.update_title(mock_connection)
    result = instance.result()
    assert result["full_text"] == ""
