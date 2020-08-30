# i3pyblocks

[![CircleCI](https://circleci.com/gh/thiagokokada/i3pyblocks/tree/master.svg?style=svg)](https://circleci.com/gh/thiagokokada/i3pyblocks/tree/master)
[![codecov](https://codecov.io/gh/thiagokokada/i3pyblocks/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagokokada/i3pyblocks)

A replacement for i3status, written in [Python][1] using [asyncio][2].

For Python 3.7+.

## Installation

First, it is recommended to create [venv][3] so this package is isolated
from other Python packages in your system.

```shell
python3 -m venv venv
source venv/bin/activate
```

Clone this repository and run:

```shell
pip install .
```

This will install a barebones version of `i3pyblocks`, but since the
dependencies are not installed not many modules will work. Each module is
inside a namespace with its our own name, so for example if you want to use
`i3pyblocks.modules.aionotify` you would need to install `aionotify` first:

```shell
pip install aionotify
```

Another option is to use the optional dependencies declared by `i3pyblocks`:

```shell
# You can also pass multiple dependencies separated by ','
pip install '.[aionotify]'
```

The current available module dependencies:
- [aionotify](https://github.com/rbarrois/aionotify)
- [i3ipc](https://github.com/altdesktop/i3ipc-python)
- [psutil](https://github.com/giampaolo/psutil)
- [pulsectl](https://github.com/mk-fg/python-pulse-control)

After installing the dependencies, you can run (assuming you installed all
dependencies):

```shell
python ./run.py
```

It will run an example configuration of `i3pyblocks` that should be sufficient
to demonstrate its capabilities. However you can customize this file as you
want.

Afterwards, you can put something like this in your `$HOME/.config/i3/config`
file:

```
bar {
    position top
    status_command /path/to/venv/python /path/to/your/run.py
}
```

## Usage

A very basic configuration file for `i3pyblocks` is shown below:

```python
import asyncio

from i3pyblocks import core
from i3pyblocks.modules import time

async def main():
    runner = core.Runner()

    runner.register_module(time.DateTimeModule())

    await runner.start()

asyncio.run(main())
```

Look in `run.py` file for a more detailed usage.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

Please make sure to update tests as appropriate.

## Development

To setup a development environment, setup a create a venv first and run:

```shell
make dev-install
```

To run the tests, you may run:

```shell
make tests
```

Look at the included `Makefile` for more available commands.


If you're using [NixOS](https://nixos.org/) or nix, an alternative way to get a
working environment variable is using the `shell.nix` file included in this
repo:

```shell
nix-shell shell.nix
```

## License

[MIT](https://choosealicense.com/licenses/mit/)

[1]: https://www.python.org/
[2]: https://docs.python.org/3/library/asyncio.html
[3]: https://docs.python.org/3/library/venv.html
