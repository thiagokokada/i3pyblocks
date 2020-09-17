.. i3pyblocks documentation master file, created by
   sphinx-quickstart on Fri Sep 11 22:59:22 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree** directive.

Welcome to i3pyblocks's documentation!
======================================

.. image:: _static/screenshot.png
   :alt: Screenshot of i3pyblocks bar.

**i3pyblocks** is a replacement for `i3status`_, written in Python using
`asyncio`_.

.. _i3status:
   https://i3wm.org/i3status/manpage.html
.. _asyncio:
   https://docs.python.org/3/library/asyncio.html

Why?
----

- Fully asynchronous architecture, there is no polling in core (not even to
  update the i3bar!)
- Most blocks are implemented in a very efficient way, based on events instead
  of polling
- Flexible API allowing for full customization. Includes `Pango`_ markup support
- Modern Python 3.6+ codebase fully type annotated, thanks to `mypy`_

.. _Pango:
   https://pango.gnome.org/
.. _mypy:
   https://mypy.readthedocs.io/

.. toctree::
   :maxdepth: 2
   :caption: Contents:
