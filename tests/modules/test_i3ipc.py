import pytest
from asynctest import CoroutineMock
from unittest.mock import call, patch, Mock

from i3ipc import Event

from i3pyblocks.modules import i3ipc as m_i3ipc

from helpers import misc


# There isn't much to test in this module since we use the main loop
# from i3ipc itself, so this is mostly a sanity check to see if we can
# load this module successfully
@pytest.mark.asyncio
async def test_window_title_module():
    with patch("i3pyblocks.modules.i3ipc.Connection") as connection_mock:
        connection_mock_instance = connection_mock.return_value
        connection_mock_instance.connect = CoroutineMock()

        instance = m_i3ipc.WindowTitleModule()
        await instance.start()

        connection_mock_instance.on.assert_has_calls(
            [
                call(Event.WORKSPACE_FOCUS, instance.clear_title),
                call(Event.WINDOW_CLOSE, instance.clear_title),
                call(Event.WINDOW_TITLE, instance.update_title),
                call(Event.WINDOW_FOCUS, instance.update_title),
            ]
        )


@pytest.mark.asyncio
async def test_window_title_module_callbacks():
    instance = m_i3ipc.WindowTitleModule()
    connection_mock = Mock()
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
