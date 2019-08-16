from i3pyblocks.utils import _calculate_threshold


def test__calculate_threshold():
    fixture = {-1: "item0", 0: "item1", 5.5: "item2", 10: "item3"}

    assert _calculate_threshold(fixture, -2) is None
    assert _calculate_threshold(fixture, -1) == "item0"
    assert _calculate_threshold(fixture, 0) == "item1"
    assert _calculate_threshold(fixture, 5) == "item1"
    assert _calculate_threshold(fixture, 5.5) == "item2"
    assert _calculate_threshold(fixture, 6) == "item2"
    assert _calculate_threshold(fixture, 10) == "item3"
    assert _calculate_threshold(fixture, 11) == "item3"
