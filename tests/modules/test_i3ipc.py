import pytest
from asynctest import CoroutineMock, Mock

import i3ipc
import i3ipc.aio

from i3pyblocks.modules import i3ipc as m_i3ipc

from helpers import misc, task


@pytest.mark.asyncio
async def test_window_title_module():
    mock_i3ipc = Mock(i3ipc)
    mock_i3ipc_aio = Mock(i3ipc.aio)

    mock_connection = mock_i3ipc_aio.Connection.return_value
    # For some reason asynctest.Mock didn't work here
    mock_connection.connect = CoroutineMock()
    mock_connection.main = CoroutineMock()
    mock_connection.get_tree = CoroutineMock()

    tree_mock = mock_connection.get_tree.return_value
    window_mock = tree_mock.find_focused
    window_mock.return_value = misc.AttributeDict(name="Hello")

    instance = m_i3ipc.WindowTitleModule(_i3ipc=mock_i3ipc, _i3ipc_aio=mock_i3ipc_aio)
    await task.runner([instance.start()])

    result = instance.result()
    assert result["full_text"] == "Hello"

    await instance.clear_title()

    result = instance.result()
    assert result["full_text"] == ""
