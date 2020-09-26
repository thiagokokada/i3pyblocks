import pytest

from i3pyblocks._internal import subprocess


@pytest.mark.asyncio
async def test_arun():
    process = await subprocess.arun(
        args="""
        cat -
        echo Bye World | cut -d" " -f2
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


def test_popener():
    process = subprocess.popener(
        args="""
        cat -
        echo Bye World | cut -d" " -f2
        echo Someone 1>&2
        exit 1
        """,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stdout_data, stderr_data = process.communicate(input="Hello ")
    assert process.returncode == 1
    assert stdout_data == "Hello World\n"
    assert stderr_data == "Someone\n"

    process = subprocess.popener(
        args=["echo", "Hello World"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert process.wait() == 0
    assert process.stdout.read() == b"Hello World\n"
