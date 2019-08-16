from typing import Dict, Optional


class IECUnits:
    KiB = 1024
    MiB = 1024 * KiB
    GiB = 1024 * MiB
    TiB = 1024 * GiB
    PiB = 1024 * TiB
    EiB = 1024 * PiB


def _calculate_threshold(
    items: Dict[float, Optional[str]], value: float
) -> Optional[str]:
    selected_item = None

    for threshold, item in items.items():
        if value >= threshold:
            selected_item = item
        else:
            break

    return selected_item
