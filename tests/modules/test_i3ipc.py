import pytest
from asynctest import CoroutineMock
from unittest.mock import MagicMock

from i3pyblocks.modules import i3ipc as m_i3ipc

from helpers import misc


# There isn't much to test in this module since we use the main loop
# from i3ipc itself, so this is mostly a sanity check to see if we can
# load this module successfully
@pytest.mark.asyncio
async def test_window_title_module():
    mock_i3ipc = MagicMock()
    mock_i3ipc_connection = MagicMock()
    connection_mock = mock_i3ipc_connection.return_value
    connection_mock.connect = CoroutineMock()

    instance = m_i3ipc.WindowTitleModule(
        _i3ipc=mock_i3ipc, _i3ipc_connection=mock_i3ipc_connection
    )
    await instance.start()


@pytest.mark.asyncio
async def test_window_title_module_callbacks():
    instance = m_i3ipc.WindowTitleModule()
    connection_mock = MagicMock()
    connection_mock.get_tree = CoroutineMock()
    tree_mock = connection_mock.get_tree.return_value
    window_mock = tree_mock.find_focused
    window_mock.return_value = misc.AttributeDict(name="Hello")

    await instance.update_title(connection_mock)

    result = instance.result()
    assert result["full_text"] == "Hello"

    await instance.clear_title()

    result = instance.result()
    assert result["full_text"] == ""
