import asyncio
import sys
from typing import Any, Awaitable
from xml.etree import ElementTree as Tree


def pango_markup(text: str, tag: str = "span", **attrib) -> str:
    r"""Helper to generate Pango markup for text.

    This helper makes it easier to generate Pango markup for arbitrary text,
    allowing for greater customization of text than the default attributes
    offered by i3bar protocol.

    Simple usage:

    >>> pango_markup("Hello, world!", font_weight="bold")
    '<span font_weight="bold">Hello, world!</span>'

    It can also generate markups for other tags supported in Pango:

    >>> pango_markup("Italic text", tag="i")
    '<i>Italic text</i>'

    Keep in mind that there is no checks if your code is correct, so you can
    pass completely nonsense attributes/tags that will be ignored by Pango:

    >>> pango_markup("Spam", foo="bar")
    '<span foo="bar">Spam</span>'

    :param text: Text to be put inside the tag.

    :param tag: XML tag that will be generated. By default it is ``<span>``.

    :param \*\*attrib: Arbitrary attributes that will be added to tag.

    .. seealso::

        Look at https://developer.gnome.org/pango/stable/pango-Markup.html for
        information about the available tags and attributes.
    """
    e = Tree.Element(tag, attrib=attrib)
    e.text = text
    return Tree.tostring(e, encoding="unicode")


def asyncio_run(awaitable: Awaitable, *, debug: bool = False) -> Any:
    """Wrapper for Python's < 3.7 similar to asyncio.run().

    In Python >= 3.7 this function simple calls `asyncio.run()`, but in older
    Python versions this function will try to simulate its functionality, the
    best way it can with the available public API of asyncio.

    If you're going to only use your configuration in Python 3.7+, I recommend
    skipping this function and using `asyncio.run()`_ directly,

    .. _asyncio.run():
        https://docs.python.org/3.7/library/asyncio-task.html#asyncio.run
    """
    if sys.version_info >= (3, 7):
        return asyncio.run(awaitable, debug=debug)

    # Emulate asyncio.run() on older versions
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.set_debug(debug)
        return loop.run_until_complete(awaitable)
    finally:
        asyncio.set_event_loop(None)
        loop.close()
