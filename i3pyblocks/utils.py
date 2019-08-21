import logging
from typing import List, Optional, Tuple

Log = logging.getLogger("i3pyblocks")
Log.addHandler(logging.NullHandler())


Items = List[Tuple[float, Optional[str]]]


class Mouse:
    LEFT_BUTTON: int = 1
    MIDDLE_BUTTON: int = 2
    RIGHT_BUTTON: int = 3
    SCROLL_UP: int = 4
    SCROLL_DOWN: int = 5


class Color:
    GOOD: Optional[str] = "#00FF00"
    NEUTRAL: Optional[str] = None
    URGENT: Optional[str] = "#FF0000"
    WARN: Optional[str] = "#FFFF00"


class IECUnit:
    KiB: int = 1024
    MiB: int = 1024 * KiB
    GiB: int = 1024 * MiB
    TiB: int = 1024 * GiB
    PiB: int = 1024 * TiB
    EiB: int = 1024 * PiB


def calculate_threshold(items: Items, value: float) -> Optional[str]:
    selected_item = None

    for threshold, item in items:
        if value >= threshold:
            selected_item = item
        else:
            break

    return selected_item
