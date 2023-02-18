"""Colors

Colors must be RGB, Xterm index, predefined, or hex.

* RGB = 255,255,255 ... `[@F 255,255,255]`
* Xterm = 0-255 ... `[@B 123]`
* hex = #aaa or #aaaaaa ... `[@F #abc]` or `[@B #abcabc]`
* predefined = black, red, green, yellow, blue, magenta, cyan, and white ... `[@F green]`

Function macros can be of types rainbow, gradient, esc, and repr

* rainbow takes a string and returns a rainbow formatted string
* gradient is more complex. It takes a comma seperated string with the format {color n}...,string.
    * All but last value is the color value. Must have at least two colors which are hex.
    * Finally, the last value is the string that the gradient will be applied too.
* esc takes a string and returns the literal value thus escaping the markup
* repr takes a given string and returns the literal value surrounded by `'`
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Union

__all__ = [
    "UNDERLINE",
    "BOLD",
    "RESET",
    "FUNC",
    "build_color",
]


@dataclass
class ColorType:
    FG: int = 30
    BG: int = 40
    BOTH: list = (30, 40)


FUNC = {
    "rainbow": lambda string: __RAINBOW(string),
    "repr": lambda string: repr(string),
}

PREDEFINED = {
    "black": lambda c: f"{c + 0}",
    "red": lambda c: f"{c + 1}",
    "green": lambda c: f"{c + 2}",
    "yellow": lambda c: f"{c + 3}",
    "blue": lambda c: f"{c + 4}",
    "magenta": lambda c: f"{c + 5}",
    "cyan": lambda c: f"{c + 6}",
    "white": lambda c: f"{c + 7}",
}
RGB = lambda c, r, g, b: f"{c + 8};2;{r};{g};{b}"
XTERM = lambda c, v: f"{c + 8};5;{v}"
RESETCOLOR = lambda ctype: f"{ctype + 9}"
RESET = "\x1b[0m"


def HEX(context: int, hex: str) -> str:
    """Converts 3 or 6 digit hex into an rgb literal

    Args:
        context (int): Whether the hex is for the foreground or background
        hex (str): The hex code

    Raises:
        ValueError: If the hex code is not in the valid format

    Returns:
        str: Ansi RGB color
    """
    hex = hex.lstrip("#")
    l = len(hex)

    if l == 6:
        r, g, b = tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))
        return RGB(context, r, g, b)
    elif l == 3:
        hex = "".join(h + h for h in hex)
        r, g, b = tuple(int(hex[i : i + 2], 16) for i in (0, 2))
        return RGB(context, r, g, b)

    raise ValueError(f"Expected hex with length of 3 or 6")


@dataclass
class BOLD:
    """The bold value based on the current toggle value."""

    POP: int = 22
    PUSH: int = 1

    @staticmethod
    def inverse(current: int) -> BOLD:
        return BOLD.POP if current == BOLD.PUSH else BOLD.PUSH


@dataclass
class UNDERLINE:
    """The bold value based on the current toggle value."""

    POP: int = 24
    PUSH: int = 4

    @staticmethod
    def inverse(current: int):
        return UNDERLINE.POP if current == UNDERLINE.PUSH else UNDERLINE.PUSH


@dataclass
class LINK:
    CLOSE: str = "\x1b]8;;\x1b\\"
    OPEN: str = lambda url: f"\x1b]8;;{url}\x1b\\"


def get_color(types: Union[int, list[int]], content: str) -> Union[int, list[int]]:
    """Parse and translate the color value from hex, xterm, rgb, and predefined color values.

    Args:
        types (Union[int, list[int]]): Tells what types to generate the color for. This include fg, bg, and both fg and bg.
        content (str): The color string that is to be parsed

    Returns:
        Union[int, list[int]]: List of color code values according to the needed types
    """
    from re import match

    results = []
    content = content.lower()
    for ctype in types:
        if len(content) == 0:
            results.append(RESETCOLOR(ctype))
        elif content.startswith("#"):
            if len(content) == 4 and match(r"#[a-fA-F0-9]{3}", content):
                results.append(HEX(ctype, content))
            elif len(content) == 7 and match(r"#[a-fA-F0-9]{6}", content):
                results.append(HEX(ctype, content))
        elif match(r"\d{1,3}\s*[,;]\s*\d{1,3}\s*[,;]\s*\d{1,3}", content):
            rgb = content.replace(";", ",").split(",")
            results.append(RGB(ctype, rgb[0].strip(), rgb[1].strip(), rgb[2].strip()))
        elif match(r"\d{1,3}", content):
            results.append(XTERM(ctype, content))
        else:
            if content in PREDEFINED:
                results.append(PREDEFINED[content](ctype))
            else:
                raise ValueError(
                    f"The color, \x1b[1;31m{content}\x1b[0m, does not match any valid format"
                )

    return results


def build_color(color: str) -> tuple[ColorType, str]:
    """Takes a color macro and determines if it is type fg, bg, or both.
    It will get the color string and produce color codes for each type that was specified.

    Args:
        color (str): The color macro to parse

    Returns:
        tuple[ColorType, str]: Tuple of the ColorType fg, bg, or both, along with the color codes
    """
    color = color[1:]
    ctype = ColorType.BOTH
    content = color.strip()

    if color.startswith(("F", "B")):
        ctype = color[0]
        content = color[1:].strip(" ")
        if ctype == "F":
            ctype = [ColorType.FG]
        elif ctype == "B":
            ctype = [ColorType.BG]

    return ctype, get_color(ctype, content)


def __RAINBOW(input: str) -> str:
    """Take a string input and make each character rainbow

    Args:
        input (str): The string to make into a rainbow

    Returns:
        str: Rainbow string
    """
    # red orange yellow green blue purple
    context = 30
    colors = [
        f"\x1b[{XTERM(context, 196)}m",
        f"\x1b[{XTERM(context, 202)}m",
        f"\x1b[{XTERM(context, 190)}m",
        f"\x1b[{XTERM(context, 41)}m",
        f"\x1b[{XTERM(context, 39)}m",
        f"\x1b[{XTERM(context, 92)}m",
    ]

    out = []
    for i, char in enumerate(input):
        out.append(colors[i % len(colors)] + char)
    out.append("\x1b[39;49m")

    return "".join(out)
