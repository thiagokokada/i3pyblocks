.. i3pyblocks documentation master file, created by
   sphinx-quickstart on Fri Sep 11 22:59:22 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree** directive.

Welcome to i3pyblocks's documentation!
======================================

.. image:: https://img.shields.io/github/stars/thiagokokada/i3pyblocks.svg?style=social&label=Star&maxAge=2592000
   :target: https://github.com/thiagokokada/i3pyblocks/stargazers/
   :alt: GitHub stars
.. image:: https://badge.fury.io/py/i3pyblocks.svg
   :target: https://badge.fury.io/py/i3pyblocks
   :alt: PyPI version

.. image:: _static/screenshot.png
   :alt: Screenshot of i3pyblocks bar.

**i3pyblocks** is a replacement for `i3status`_, written in Python using
`asyncio`_.

Works in both `i3wm`_ and `sway`_.

.. _i3status:
   https://i3wm.org/i3status/manpage.html
.. _asyncio:
   https://docs.python.org/3/library/asyncio.html
.. _i3wm:
   https://i3wm.org/
.. _sway:
   https://swaywm.org/

Highlights
----------

- Fully asynchronous architecture, there is no polling in core (not even to
  update the i3bar!)
- Most blocks are implemented in a very efficient way, based on events (i.e.:
  `D-Bus`_, `inotify`_) instead of polling
- Flexible API allowing for full customization. You can even completely override
  some methods for you own needs if you want
- Modern Python 3.7+ codebase fully `type annotated`_, thanks to `mypy`_

.. _D-Bus:
   https://en.wikipedia.org/wiki/D-Bus
.. _inotify:
   https://en.wikipedia.org/wiki/Inotify
.. _type annotated:
   https://docs.python.org/3/library/typing.html
.. _mypy:
   https://mypy.readthedocs.io/

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   why-another-i3status-replacement
   user-guide
   creating-a-new-block
