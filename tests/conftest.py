import io
import sys

import pytest


@pytest.fixture
def mock_stdin(monkeypatch, return_value=""):
    monkeypatch.setattr(sys, "stdin", io.StringIO(return_value))
