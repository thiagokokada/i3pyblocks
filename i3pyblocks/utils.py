from typing import Dict, Optional


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
