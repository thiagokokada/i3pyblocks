from multiprocessing import Process
from textwrap import dedent

import pytest

from i3pyblocks import cli
from i3pyblocks.__version__ import __version__


def run_until_timeout(target, args, timeout=1):
    p = Process(target=target, args=args)
    p.start()
    p.join(timeout=timeout)
    p.terminate()


def test_example(capfd):
    run_until_timeout(target=cli.main, args=([],))

    captured = capfd.readouterr()

    assert '{"version": 1, "click_events": true}' in captured.out
    assert "DateTimeBlock" in captured.out


def test_config(capfd, tmpdir):
    config_file = tmpdir / "config.py"

    with open(config_file, "w") as f:
        config = dedent(
            """\
            import asyncio

            from i3pyblocks import Runner
            from i3pyblocks.blocks import basic, datetime


            async def main():
                runner = Runner()

                runner.register_block(basic.TextBlock("Hello World!"))
                runner.register_block(datetime.DateTimeBlock())

                await runner.start()


            if __name__ == "__main__":
                asyncio.run(main())
            """
        )
        f.write(config)

    run_until_timeout(target=cli.main, args=(["-c", str(config_file)],))

    captured = capfd.readouterr()

    assert '{"version": 1, "click_events": true}' in captured.out
    assert "DateTimeBlock" in captured.out
    assert "TextBlock" in captured.out


def test_non_existent_config():
    with pytest.raises(FileNotFoundError):
        cli.main(["-c", "non_existent_config"])


def test_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["-h"])

    captured = capsys.readouterr()
    assert "i3pyblocks" in captured.out
    assert captured.err == ""


def test_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])

    captured = capsys.readouterr()
    assert f"i3pyblocks {__version__}" in captured.out
    assert captured.err == ""
