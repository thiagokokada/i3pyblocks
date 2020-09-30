from asyncio.subprocess import STDOUT  # noqa: F401
from asyncio.subprocess import (
    DEVNULL,
    PIPE,
    create_subprocess_exec,
    create_subprocess_shell,
)
from subprocess import CompletedProcess, Popen
from typing import AnyStr, Iterable, Optional

from i3pyblocks._internal import models


def _get_shell(args: models.CommandArgs, shell: Optional[bool]) -> bool:
    if shell is None:
        if isinstance(args, str):
            return True
        else:
            return False

    return shell


async def arun(
    args: models.CommandArgs,
    *,
    stdin: Optional[int] = DEVNULL,
    input: Optional[AnyStr] = None,
    stdout: Optional[int] = DEVNULL,
    stderr: Optional[int] = DEVNULL,
    capture_output: bool = False,
    shell: Optional[bool] = None,
    text: bool = False,
    **other_subprocess_kwargs,
) -> CompletedProcess:
    """Wrapper around asyncio.subprocess with an API similar to `subprocess.run()`_.

    This is not complete and there is some deliberately differences:

        - Auto-detection of ``shell`` parameter based on arguments
        - By default, stdin/stdout/stderr point to /dev/null, so the process
          is isolated from outside

    It should offer a better experience than the default asyncio.subprocess
    API, so this is preferred than using asyncio.subprocess primitives. Can be
    expanded if/when needed.

    .. _subprocess.run():
        https://docs.python.org/3/library/subprocess.html#subprocess.run
    """
    if capture_output:
        stdout = PIPE
        stderr = PIPE

    if _get_shell(args, shell):
        assert isinstance(args, str)
        process = await create_subprocess_shell(
            args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            **other_subprocess_kwargs,
        )
    else:
        assert isinstance(args, Iterable)
        process = await create_subprocess_exec(
            args[0],
            *args[1:],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            **other_subprocess_kwargs,
        )

    result_stdout, result_stderr = await process.communicate(
        input=input.encode() if (input and text) else input,  # type: ignore
    )

    return CompletedProcess(
        args=args,
        returncode=process.returncode or 0,
        stdout=result_stdout.decode() if (result_stdout and text) else result_stdout,
        stderr=result_stderr.decode() if (result_stderr and text) else result_stderr,
    )


def popener(
    args: models.CommandArgs,
    *,
    stdin: Optional[int] = DEVNULL,
    stdout: Optional[int] = DEVNULL,
    stderr: Optional[int] = DEVNULL,
    shell: Optional[bool] = None,
    text: bool = False,
) -> Popen:
    """Wrapper around `subprocess.Popen`_, executing a child program in a new process.

    This is not complete and there is some deliberately differences:

        - Auto-detection of ``shell`` parameter based on arguments
        - By default, stdin/stdout/stderr point to /dev/null, so the process
          is isolated from outside

    Recommended for those cases where :func:`~i3pyblocks._internal.subprocess.arun`
    does not cover, i.e.: need to run a program completely in background and the
    result of its execution does not matter.

    .. _`subprocess.Popen`:
        https://docs.python.org/3/library/subprocess.html#subprocess.Popen
    """
    return Popen(
        args,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        shell=_get_shell(args, shell),
        universal_newlines=text,
    )
