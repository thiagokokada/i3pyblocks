# i3pyblocks

[![Test](https://github.com/thiagokokada/i3pyblocks/workflows/Test/badge.svg)](https://github.com/thiagokokada/i3pyblocks/actions)
[![Lint](https://github.com/thiagokokada/i3pyblocks/workflows/Lint/badge.svg)](https://github.com/thiagokokada/i3pyblocks/actions)
[![Documentation Status](https://readthedocs.org/projects/i3pyblocks/badge/?version=latest)](https://i3pyblocks.readthedocs.io/en/latest/?badge=latest)
[![Codecov](https://codecov.io/gh/thiagokokada/i3pyblocks/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagokokada/i3pyblocks)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![Screenshot](https://raw.github.com/thiagokokada/i3pyblocks/master/docs/_static/screenshot.png)

A replacement for i3status, written in [Python][1] using [asyncio][2].

Works in both [i3wm][3] and [sway][4].

For Python 3.6+.

## Installation

First, it is recommended to create [venv][5] so this package is isolated
from other Python packages in your system.

```shell
python3 -m venv venv
source venv/bin/activate
```

Afterwards, run:

```shell
pip install -e 'git+https://github.com/thiagokokada/i3pyblocks#egg=i3pyblocks'
```

This will install a barebones version of `i3pyblocks`, but since the optional
dependencies are not installed most blocks won't work.

Each block dependency is declared in `extra_requires` dictionary inside 
`setup.py` file, so for example if you want to use `i3pyblocks.blocks.inotify`
you have to install the extra dependencies declared in `blocks.inotify` feature:

```shell
# This will install the dependencies for `i3pyblocks.blocks.inotify`
pip install -e 'git+https://github.com/thiagokokada/i3pyblocks#egg=i3pyblocks[blocks.inotify]'
# You can also pass multiple dependencies separated by comma
pip install -e 'git+https://github.com/thiagokokada/i3pyblocks#egg=i3pyblocks[blocks.i3ipc,blocks.ps]'
```

## Usage

After installing the dependencies, you can run:

```shell
i3pyblocks
```

It will should display a clock example if everything is working as it should.
For a more elabore example, try to run the `example.py` file included in this
repository (needs installation of optional dependencies):


```shell
i3pyblocks -c example.py
```

This will run an example configuration of `i3pyblocks` that should demonstrate
its capabilities. This file also has comments explaining how the basics of
`i3pyblocks` works, so it serves as a great start point for your own
configuration file.

Afterwards, you can put something like this in your `$HOME/.config/i3/config` or
`$HOME/.config/sway/config` file:

```
bar {
    position top
    status_command /path/to/venv/i3pyblocks -c /path/to/your/my_i3pyblocks_config.py
}
```

For NixOS users, this repository have a separate branch `nix-overlay` that acts
as an overlay. Check branch's `README.md` for details.

## Development

To setup a development environment, create a new [venv][5] first and run:

```shell
make dev-install
```

To run the tests, you may run:

```shell
make tests
```

Look at the included `Makefile` for more available commands.


If you're using [NixOS](https://nixos.org/) or nixpkgs, an alternative way to
get a working environment variable is using the `shell.nix` file included in
this repo:

```shell
nix-shell shell-dev.nix
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

[1]: https://www.python.org/
[2]: https://docs.python.org/3/library/asyncio.html
[3]: https://i3wm.org/
[4]: https://swaywm.org/
[5]: https://docs.python.org/3/library/venv.html
