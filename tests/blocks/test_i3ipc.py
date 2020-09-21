import pytest
from asynctest import CoroutineMock, patch
from helpers import misc, task

i3ipc = pytest.importorskip("i3pyblocks.blocks.i3ipc")


@pytest.mark.asyncio
async def test_window_title_block():
    with patch(
        "i3pyblocks.blocks.i3ipc.i3ipc_aio", autospec=True, spec_set=True
    ) as mock_i3ipc_aio:
        mock_i3ipc_aio.configure_mock(
            **{
                "Connection.return_value.connect": CoroutineMock(),
                "Connection.return_value.main": CoroutineMock(),
                "Connection.return_value.get_tree": CoroutineMock(),
            }
        )
        mock_connection = mock_i3ipc_aio.Connection.return_value

        tree_mock = mock_connection.get_tree.return_value
        window_mock = tree_mock.find_focused
        window_mock.return_value = misc.AttributeDict(name="Hello")

        instance = i3ipc.WindowTitleBlock()
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
