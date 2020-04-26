import sys

import pytest


@pytest.fixture
def mock_stdin(mocker):
    return mocker.patch.object(sys, "stdin")
