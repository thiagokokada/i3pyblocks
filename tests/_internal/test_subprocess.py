import pytest

from i3pyblocks._internal import subprocess


@pytest.mark.asyncio
async def test_arun():
    process = await subprocess.arun(
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

    process = await subprocess.arun(
        args=["cat", "-"],
        capture_output=True,
        text=True,
        input="Another hello",
        stdin=subprocess.PIPE,
    )

    assert process.stdout == "Another hello"
    assert process.returncode == 0
