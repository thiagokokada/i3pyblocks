from i3pyblocks import utils


def test_pango_markup():
    assert utils.pango_markup("Hello") == "<span>Hello</span>"
    assert (
        utils.pango_markup("Blue text", foreground="blue", size="x-large")
        == '<span foreground="blue" size="x-large">Blue text</span>'
    )
    assert (
        utils.pango_markup("Big italic", tag="i", size="x-large")
        == '<i size="x-large">Big italic</i>'
    )
