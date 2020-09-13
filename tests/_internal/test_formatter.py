from i3pyblocks._internal import formatter


def test_extended_formatter():
    ex_formatter = formatter.ExtendedFormatter()

    string = "ALL CAPS"
    assert ex_formatter.format("{string!l}", string=string) == "all caps"
    assert ex_formatter.format("{string!l:.3s}", string=string) == "all"
    assert ex_formatter.format("{!l:.3s}", string) == "all"

    string = "low caps"
    assert ex_formatter.format("{string!u}", string=string) == "LOW CAPS"
    assert ex_formatter.format("{string!u:.3s}", string=string) == "LOW"
    assert ex_formatter.format("{!u:.3s}", string) == "LOW"

    string = "capitalize THIS"
    assert ex_formatter.format("{string!c}", string=string) == "Capitalize this"

    string = "some amazing title"
    assert ex_formatter.format("{string!t}", string=string) == "Some Amazing Title"

    assert ex_formatter.format("{!u}", 0) == "0"
    assert ex_formatter.format("{!u}", object) == "<CLASS 'OBJECT'>"
    assert ex_formatter.format("{!u}", "Maße") == "MASSE"

    assert ex_formatter.format("{!l}", None) == "none"
    assert ex_formatter.format("{!l}", True) == "true"
    assert ex_formatter.format("{!l}", False) == "false"
