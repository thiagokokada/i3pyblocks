from typing import Dict, Optional, Union

from i3pyblocks import types


def calculate_threshold(
    items: types.Dictable, value: Union[int, float]
) -> Optional[str]:
    selected_item = None

    for threshold, item in dict(items).items():
        if value >= threshold:  # type: ignore
            selected_item = item
        else:
            break

    return selected_item


def non_nullable_dict(**kwargs) -> Dict:
    return {k: v for k, v in kwargs.items() if v is not None}
