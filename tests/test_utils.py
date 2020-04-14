from i3pyblocks import utils


def test_calculate_threshold():
    fixture = [(-1, "item0"), (0, "item1"), (5.5, "item2"), (10, "item3")]

    assert utils.calculate_threshold(fixture, -2) is None
    assert utils.calculate_threshold(fixture, -1) == "item0"
    assert utils.calculate_threshold(fixture, 0) == "item1"
    assert utils.calculate_threshold(fixture, 5) == "item1"
    assert utils.calculate_threshold(fixture, 5.5) == "item2"
    assert utils.calculate_threshold(fixture, 6) == "item2"
    assert utils.calculate_threshold(fixture, 10) == "item3"
    assert utils.calculate_threshold(fixture, 11) == "item3"


def test_non_nullable_dict():
    assert utils.non_nullable_dict(foo="bar", spams=None) == {"foo": "bar"}
