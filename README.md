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

This will install a barebones version of `i3pyblocks`, but since the optional
dependencies are not installed most blocks won't work.

Each block is inside a namespace with the name of its main dependency, so for
example if you want to use `i3pyblocks.blocks.aionotify` you would need to
install `aionotify` first:

```shell
# This install aionotify feature, including all dependencies necessary to work
pip install '.[aionotify]'
```

Another option is to install each dependency manually:

```shell
# Not recommended since you need to track each dependency manually
pip install aionotify
```

The current available block dependencies:
- [aionotify](https://github.com/rbarrois/aionotify)
- [i3ipc](https://github.com/altdesktop/i3ipc-python)
- [psutil](https://github.com/giampaolo/psutil)
- [pulsectl](https://github.com/mk-fg/python-pulse-control)

So to install all available dependencies:

```shell
# To install multiple dependencies, you can also pass multiple dependencies
# separated by ',', for example
pip install '.[aionotify,i3ipc,psutil,pulsectl]'
```

## Usage

After installing the dependencies, you can run (assuming you have installed all
dependencies):

```shell
python ./example.py
```

It will run an example configuration of `i3pyblocks` that should be sufficient
to demonstrate its capabilities. This file also has comments explaining how
the basics of `i3pyblocks` works, so it serves as a great start point for your
own configuration file.

Afterwards, you can put something like this in your `$HOME/.config/i3/config`
file:

```
bar {
    position top
    status_command /path/to/venv/python /path/to/your/my_i3pyblocks_config.py
}
```

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

## Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

[1]: https://www.python.org/
[2]: https://docs.python.org/3/library/asyncio.html
[3]: https://docs.python.org/3/library/venv.html
