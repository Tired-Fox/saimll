from typing import Callable
from saimll.saiml.markup import SAIML
from .colors import Color

COLOR = str | int | tuple | Color
base_colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]


def _parse_color(color: COLOR, spec: str = "F"):
    code = ""
    if color is not None:
        if isinstance(color, str):
            if color.startswith("#"):
                code = f"@{spec} {','.join(Color.HEX(color).rgb())}"
            elif color.lower() in base_colors:
                code = f"@{spec} {color.lower()}"
            else:
                code = f"@{spec} {Color.XTERM(color).code}"
        elif isinstance(color, int):
            code = f"@{spec} {Color.XTERM(color).code}"
        elif isinstance(color, tuple):
            if len(color) != 3:
                raise ValueError("There may only be 3 values in the rgb tuple")

            if any(val < 0 or val > 255 for val in color):
                raise ValueError("RGB values may only be from 0 to 255")

            code = f"@{spec} {','.join(str(channel) for channel in color)}"
    return code


def style(
    *string,
    fg: COLOR = None,
    bg: COLOR = None,
    bold: bool = False,
    uline: bool = False,
    url: str = None,
    function: Callable | tuple[str, Callable] = None,
):
    """Stylize a string with foreground and background color, bold, underline, and url
    formatting.
    """

    value = " ".join(string)

    macro = []

    # foreground and background colors
    macro.append(_parse_color(fg))
    macro.append(_parse_color(bg, "B"))

    # url
    if url is not None:
        macro.append(f"~{url}")

    # Run through function
    if isinstance(function, str):
        if function in SAIML._funcs:
            macro.append(f"^{function}")
        else:
            raise KeyError(f"{function} is a unkown custom function")
    elif isinstance(function, tuple):
        if len(function) == 2 and isinstance(function[0], str) and callable(function[1]):
            SAIML.define(function[0], function[1])
            macro.append(f"^{function[0]}")
        else:
            raise TypeError(
                "If you are providing a new custom function it must be a tuple of one \
str and one Callable"
            )
    head = ""

    # Bold
    if bold:
        head += "*"

    # Underline
    if uline:
        head += "_"

    # Parse with SAIML and return
    return SAIML.parse(
        f"[{' '.join(attr for attr in macro if attr.strip() != '')}]{head}{SAIML.escape(value)}"
    )
