from typing import Dict, Optional


def _calculate_threshold(colors: Dict[float, Optional[str]], value) -> Optional[str]:
    for threshold, color in colors.items():
        if value <= threshold:
            return color
    return None
