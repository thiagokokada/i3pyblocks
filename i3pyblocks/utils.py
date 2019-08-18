from typing import List, Optional, Tuple


Items = List[Tuple[float, Optional[str]]]


class Color:
    GOOD: Optional[str] = "#00FF00"
    NEUTRAL: Optional[str] = None
    URGENT: Optional[str] = "#FF0000"
    WARN: Optional[str] = "#FFFF00"


class IECUnits:
    KiB: int = 1024
    MiB: int = 1024 * KiB
    GiB: int = 1024 * MiB
    TiB: int = 1024 * GiB
    PiB: int = 1024 * TiB
    EiB: int = 1024 * PiB


def _calculate_threshold(items: Items, value: float) -> Optional[str]:
    selected_item = None

    for threshold, item in items:
        if value >= threshold:
            selected_item = item
        else:
            break

    return selected_item
