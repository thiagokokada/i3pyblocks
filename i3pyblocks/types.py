from typing import Optional


class AlignText:
    CENTER: str = "center"
    RIGHT: str = "right"
    LEFT: str = "left"


class MarkupText:
    NONE: str = "none"
    PANGO: str = "pango"


class MouseButton:
    LEFT_BUTTON: int = 1
    MIDDLE_BUTTON: int = 2
    RIGHT_BUTTON: int = 3
    SCROLL_UP: int = 4
    SCROLL_DOWN: int = 5
    BACK: int = 8
    FORWARD: int = 9


class KeyModifier:
    MOD1: str = "Mod1"
    MOD2: str = "Mod2"
    MOD3: str = "Mod3"
    MOD4: str = "Mod4"
    SHIFT: str = "Shift"

    # Some alias to make things easier to use
    ALT = MOD1
    NUM_LOCK = MOD2
    SCROLL_LOCK = MOD3
    SUPER = MOD4


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
