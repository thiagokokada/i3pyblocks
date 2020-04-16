# i3pyblocks

[![CircleCI](https://circleci.com/gh/thiagokokada/i3pyblocks/tree/master.svg?style=svg)](https://circleci.com/gh/thiagokokada/i3pyblocks/tree/master)
[![codecov](https://codecov.io/gh/thiagokokada/i3pyblocks/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagokokada/i3pyblocks)

A replacement for i3status, written in [Python][1] using [asyncio][2].

## Installation

For now, the best way to use i3pyblocks is installing [poetry][3] first:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

Afterwards, clone this repository and run:

```bash
poetry install
```

This will install the dependencies. Now run:

```bash
poetry run ./run.py
```

It will run an example configuration of i3pyblocks that should be sufficient to
demonstrate its capabilities. However you can customize this file as you want.

To run this as your substitute for i3status, the easiest way for now is to build
and install a wheel:

```bash
poetry build
pip install dist/i3pyblocks-0.0.1-py3-none-any.whl
```

Afterwards, you can put something like this in your `$HOME/.config/i3/config`
file:

```
bar {
    position top
    status_command /path/to/your/run.py
}
```

Remember that `run.py` file should have execution permission set (`chmod +x
run.py`) and have a `#!/usr/bin/env python3` as the first line of the script.

## Usage

A very basic configuration file for i3pyblocks is shown below:

```python
import asyncio

from i3pyblocks import core
from i3pyblocks.modules import time

async def main():
    runner = core.Runner()

    runner.register_module(time.LocalTimeModule())

    await runner.start()

asyncio.run(main())
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

[1]: https://www.python.org/
[2]: https://docs.python.org/3/library/asyncio.html
[3]: https://python-poetry.org/
