import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    if sys.version_info >= (3, 8):
        from typing import TypedDict
    else:
        from typing_extensions import TypedDict

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


else:
    State = Dict[str, Union[str, int, bool]]


CommandArgs = Union[str, Union[List[str], Tuple[str]]]
# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
Decorator = TypeVar("Decorator", bound=Callable[..., Any])
Threshold = Mapping[float, Optional[str]]
