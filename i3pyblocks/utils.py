from xml.etree import ElementTree as Tree


def pango_markup(text: str, tag: str = "span", **attrib) -> str:
    """Helper to generate Pango markup for text

    This helper makes it easier to generate Pango markup for arbitrary text,
    allowing for greater customization of text than the default attributes
    offered by i3bar protocol.

    Args:
      text:
        Text to be put inside the tag.
      tag:
        XML tag that will be generated. By default it is ``<span>``.
      **attrib:
        Arbitrary attributes that will be added to tag.

    Examples:
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

    See Also:
      Look at https://developer.gnome.org/pango/stable/pango-Markup.html for
      information about the available tags and attributes.
    """
    e = Tree.Element(tag, attrib=attrib)
    e.text = text
    return Tree.tostring(e, encoding="unicode")
