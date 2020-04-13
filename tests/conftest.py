import sys
import uuid

import pytest


@pytest.fixture
def mock_stdin(mocker):
    return mocker.patch.object(sys, "stdin")


@pytest.fixture
def mock_uuid4(mocker):
    return mocker.patch.object(uuid, "uuid4", return_value="uuid4")
