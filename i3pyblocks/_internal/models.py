import sys
from typing import Mapping, Optional

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    try:
        from typing_extensions import TypedDict
    except ImportError:
        from typing import Dict

        class TypedDict(Dict):
            """TypedDict shim for Python <3.8."""

            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__()


class State(TypedDict, total=False):
    full_text: Optional[str]
    short_text: Optional[str]
    color: Optional[str]
    background: Optional[str]
    border: Optional[str]
    border_top: Optional[int]
    border_right: Optional[int]
    border_bottom: Optional[int]
    border_left: Optional[int]
    min_width: Optional[int]
    align: Optional[str]
    urgent: Optional[bool]
    separator: Optional[bool]
    separator_block_width: Optional[int]
    markup: Optional[str]


Threshold = Mapping[float, Optional[str]]
