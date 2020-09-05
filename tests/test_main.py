import pytest
from asynctest import CoroutineMock

from i3pyblocks import __main__ as main
from i3pyblocks.__version__ import __version__


def test_example():
    mock_clock_example = CoroutineMock()
    main.clock_example = mock_clock_example

    main.main([])

    mock_clock_example.assert_awaited_once()


def test_config(capsys, tmpdir):
    config_file = tmpdir / "config.py"

    with open(config_file, "w") as f:
        f.write('print("Hello world!")')

    main.main(["-c", str(config_file)])

    captured = capsys.readouterr()
    assert "Hello world!" in captured.out
    assert captured.err == ""


def test_non_existent_config():
    with pytest.raises(FileNotFoundError):
        main.main(["-c", "non_existent_config"])


def test_help(capsys):
    with pytest.raises(SystemExit):
        main.main(["-h"])

    captured = capsys.readouterr()
    assert "i3pyblocks" in captured.out
    assert captured.err == ""


def test_version(capsys):
    with pytest.raises(SystemExit):
        main.main(["--version"])

    captured = capsys.readouterr()
    assert f"i3pyblocks {__version__}" in captured.out
    assert captured.err == ""
