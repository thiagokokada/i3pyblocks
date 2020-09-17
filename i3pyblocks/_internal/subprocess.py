from asyncio.subprocess import STDOUT  # noqa: F401
from asyncio.subprocess import (
    DEVNULL,
    PIPE,
    create_subprocess_exec,
    create_subprocess_shell,
)
from subprocess import CompletedProcess
from typing import AnyStr, Iterable, Optional

from i3pyblocks._internal import models


async def arun(
    args: models.CommandArgs,
    *,
    stdin: Optional[int] = DEVNULL,
    input: Optional[AnyStr] = None,
    stdout: Optional[int] = DEVNULL,
    stderr: Optional[int] = DEVNULL,
    capture_output: bool = False,
    shell: Optional[bool] = None,
    text: bool = None,
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
        https://docs.python.org/3.8/library/subprocess.html#subprocess.run
    """
    if capture_output:
        stdout = PIPE
        stderr = PIPE

    if shell is None:
        if isinstance(args, str):
            shell = True
        else:
            shell = False

    if shell:
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
