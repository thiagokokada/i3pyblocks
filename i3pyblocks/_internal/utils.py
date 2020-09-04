import asyncio
from asyncio import subprocess
from typing import Dict, Optional, Tuple, Union

from i3pyblocks import types


def calculate_threshold(
    items: types.Dictable, value: Union[int, float]
) -> Optional[str]:
    selected_item = None

    for threshold, item in dict(items).items():
        if value >= threshold:  # type: ignore
            selected_item = item
        else:
            break

    return selected_item


def non_nullable_dict(**kwargs) -> Dict:
    return {k: v for k, v in kwargs.items() if v is not None}


async def shell_run(
    command: str,
    input: Optional[bytes] = None,
    stdin: int = subprocess.DEVNULL,
    stdout: int = subprocess.DEVNULL,
    stderr: int = subprocess.DEVNULL,
) -> Tuple[bytes, bytes, subprocess.Process]:
    process = await asyncio.create_subprocess_shell(
        command, stdin=stdin, stdout=stdout, stderr=stderr
    )

    stdout_data, stderr_data = await process.communicate(input=input)

    return stdout_data, stderr_data, process
