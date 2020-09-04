from xml.etree import ElementTree as Tree


def pango_markup(text: str, tag: str = "span", **attrib) -> str:
    e = Tree.Element(tag, attrib=attrib)
    e.text = text
    return Tree.tostring(e, encoding="unicode")
