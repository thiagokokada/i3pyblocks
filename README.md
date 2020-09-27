# i3pyblocks

[![PyPI version](https://badge.fury.io/py/i3pyblocks.svg)](https://badge.fury.io/py/i3pyblocks)
[![Test](https://github.com/thiagokokada/i3pyblocks/workflows/Test/badge.svg)](https://github.com/thiagokokada/i3pyblocks/actions)
[![Lint](https://github.com/thiagokokada/i3pyblocks/workflows/Lint/badge.svg)](https://github.com/thiagokokada/i3pyblocks/actions)
[![Documentation Status](https://readthedocs.org/projects/i3pyblocks/badge/?version=latest)](https://i3pyblocks.readthedocs.io/en/latest/?badge=latest)
[![Codecov](https://codecov.io/gh/thiagokokada/i3pyblocks/branch/master/graph/badge.svg)](https://codecov.io/gh/thiagokokada/i3pyblocks)

![Screenshot](https://raw.github.com/thiagokokada/i3pyblocks/master/docs/_static/screenshot.png)

A replacement for i3status, written in [Python][python] using [asyncio][asyncio].

Works in both [i3wm][i3wm] and [sway][sway].

For Python 3.6+.

## Installation and Usage

Look at the [example.py][example.py] file for inspiration and check the
[User guide][user-guide] section of documentation.

## Development

To setup a development environment, create a new [venv][venv] first and run:

```shell
make dev-install
```

To run the tests, you may run:

```shell
make test
```

Look at the included `Makefile` for more available commands.


If you're using [NixOS][nixos] or nixpkgs, an alternative way to
get a working environment variable is using the `shell.nix` file included in
this repo:

```shell
nix-shell shell-dev.nix
```

For more information, look at [Creating a new block][creating-a-new-block]
section of documentation.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to
discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

[python]: https://www.python.org/
[asyncio]: https://docs.python.org/3/library/asyncio.html
[i3wm]: https://i3wm.org/
[sway]: https://swaywm.org/
[venv]: https://docs.python.org/3/library/venv.html
[user-guide]: https://i3pyblocks.readthedocs.io/en/latest/user-guide.html
[nixos]: https://nixos.org/
[creating-a-new-block]: https://i3pyblocks.readthedocs.io/en/latest/creating-a-new-block.html
[example.py]: https://github.com/thiagokokada/i3pyblocks/blob/master/example.py
