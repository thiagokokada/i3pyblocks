import argparse
import asyncio
import types
from importlib import machinery
from typing import List, Optional

from i3pyblocks.__version__ import __version__


async def clock_example():
    from i3pyblocks import core
    from i3pyblocks.blocks import datetime

    runner = core.Runner()
    runner.register_block(datetime.DateTimeBlock())

    await runner.start()


def main(args: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="i3pyblocks",
        description="A replacement for i3status, written in Python using asyncio.",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="path to configuration file",
        default=None,
        required=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parsed_args = parser.parse_args(args=args)

    if parsed_args.config:
        # Set the config file's __name__ to "__main__", so we can use __main__
        # guard in our config files
        loader = machinery.SourceFileLoader("__main__", parsed_args.config)
        mod = types.ModuleType(loader.name)
        loader.exec_module(mod)
    else:
        asyncio.run(clock_example())


if __name__ == "__main__":
    main()
