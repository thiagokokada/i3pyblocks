# This filename is proposital, since otherwise it would conflict with blocks/test_subprocess.py

import pytest

from i3pyblocks._internal import subprocess


@pytest.mark.asyncio
async def test_aio_run():
    process = await subprocess.aio_run(
        args="""
        cat -
        echo Hello World | cut -d" " -f2
        echo Someone 1>&2
        exit 1
        """,
        input=b"Hello ",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert process.stdout == b"Hello World\n"
    assert process.stderr == b"Someone\n"
    assert process.returncode == 1

    process = await subprocess.aio_run(
        args=["echo", "Another hello"],
        capture_output=True,
        text=True,
    )

    assert process.stdout == "Another hello\n"
    assert process.returncode == 0
