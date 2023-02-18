from __future__ import annotations
from functools import cached_property

from typing import Optional, overload
from re import match
import colorsys

from simll import SIML

from .xterm_colors import XTERM_COLORS


__all__ = ["Color"]


class ColorBase:
    """Base class for a color"""

    def as_str(self) -> str:
        """Stringify the color representation."""
        return f"{self.__class__.__name__}()"

    def rgb(self) -> tuple[int, int, int]:
        """Get the rgb values as a tuple."""
        return (0, 0, 0)

    def encode(self, *args: str) -> str:
        """Convert the color to a ansi code and return a formatted string with that color.
        This is usefull if you want to output the color to a terminal.
        """
        text = " ".join(args) if len(args) > 0 else "▉ {color} ▉"
        try:
            text = text.format(color=str(self))
        except Exception as exception:  # pylint: disable=unused-variable,broad-except
            pass
        r, g, b = self.rgb()
        return SIML.parse(f"[@F {r},{g},{b}]{text}")

    def __str__(self) -> str:
        return self.as_str()

    def __repr__(self) -> str:
        return self.as_str()


class Color:
    """A wrapper for the types of colors."""

    class RGB(ColorBase):
        """Red, green, and blue (RGB) representation of a color."""

        red: int
        """Amount of red in the color from 0 to 255."""

        green: int
        """Amount of green in the color from 0 to 255."""

        blue: int
        """Amount of blue in the color from 0 to 255."""

        @overload
        def __init__(self, color: int, alpha: Optional[int] = 1):
            ...

        def __init__(
            self,
            red: int,
            green: Optional[int] = None,
            blue: Optional[int] = None,
            alpha: Optional[int] = 1,
        ) -> None:
            if red is not None and green is None and blue is None:
                if red < 0 or red > 255:
                    raise ValueError("RGB value must be from 0 to 255.")
                self.red = red
                self.blue = red
                self.green = red
            else:
                if red < 0 or red > 255:
                    raise ValueError("Red value must be from 0 to 255.")
                self.red = red or 0
                if green < 0 or green > 255:
                    raise ValueError("Green value must be from 0 to 255.")
                self.green = green or 0
                if blue < 0 or blue > 255:
                    raise ValueError("Blue value must be from 0 to 255.")
                self.blue = blue or 0
            self._alpha = alpha

        @property
        def r(self) -> int:
            """Red value. Readonly"""
            return self.red

        @property
        def g(self) -> int:
            """Green value. Readonly"""
            return self.green

        @property
        def b(self) -> int:
            """Blue value. Readonly"""
            return self.blue

        @property
        def a(self) -> int:
            """Alpha/transparency value."""
            return self._alpha

        def to_hsl(self) -> Color.HSL:
            """Convert from rgb to hsl."""
            h, l, s = colorsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
            return Color.HSL(round(h * 360), s, l)

        def to_hex(self) -> Color.HEX:
            """Convert from rgb to hex."""
            red = "{val:x}".format(val=self.r)
            if len(red) == 1:
                red = red.ljust(2, "{val:x}".format(val=self.r))

            green = "{val:x}".format(val=self.g)
            if len(green) == 1:
                green = green.ljust(2, "{val:x}".format(val=self.g))

            blue = "{val:x}".format(val=self.b)
            if len(blue) == 1:
                blue = blue.ljust(2, "{val:x}".format(val=self.b))

            return Color.HEX(f"{red}{green}{blue}")

        def to_hsv(self) -> Color.HSV:
            """Convert from rgb to hsv."""
            h, s, v = colorsys.rgb_to_hsv(*self.normalized())
            return Color.HSV(round(h * 360), s, v)

        def to_yiq(self) -> Color.YIQ:
            """Convert from rgb to yiq."""
            return Color.YIQ(*colorsys.rgb_to_yiq(*self.normalized()))

        def normalized(self) -> tuple[float, float, float]:
            """Normalize the rgb values."""
            return (self.r / 255, self.g / 255, self.b / 255)

        @staticmethod
        def normalize(r: int, g: int, b: int) -> tuple[float, float, float]:
            """Normalize rgb values."""
            return (r / 255, g / 255, b / 255)

        def rgb(self) -> tuple[int, int, int]:
            return (self.r, self.g, self.b)

        def as_str(self) -> str:
            """Stringify the color representation."""
            return f"rgb({self.r},{self.g},{self.b},{self.a})"

    class HEX(ColorBase):
        """Hexadecimal representation of a color."""

        value: str
        """Hex code."""

        def __init__(self, code: str) -> None:
            code = code.strip().lstrip("#")
            if len(code) != 3 and len(code) != 6:
                raise ValueError("Hex codes must be either 3 or 6 in length.")

            if not all(match(r"[0-9a-fA-F]{3,6}", code) is not None for val in code):
                raise ValueError("Hex values must be 0-9 and A-F")

            self.value = code

        @property
        def code(self) -> str:
            """The hex value of the color. Readonly"""
            return self.value

        def to_rgb(self) -> Color.RGB:
            """Convert from hex to rgb."""
            return Color.RGB(*self.rgb())

        def rgb(self) -> tuple[int, int, int]:
            code = self.value
            if len(self.value) == 3:
                code = "".join([f"{val}{val}" for val in self.value])

            red = int(code[:2], 16)
            green = int(code[2:4], 16)
            blue = int(code[4:6], 16)

            return (red, green, blue)

        def as_str(self) -> str:
            """Stringify the color representation."""
            return f"#{self.code}"

    class HSL(ColorBase):
        """Hue, saturation, lightness (HSL) representation of a color."""

        hue: int
        """Hue of the color in degrees. 0-360 where 0 is red, 120 is green, and 240 is blue."""

        saturation: float
        """Saturation of the color as a percent. 0% means a shade of gray and 100% means full
        color."""

        lightness: float
        """Lightness of the color as a percent. 0% is black, 100% is white."""

        def __init__(self, h: int, s: float, l: float) -> None:
            if h < 0 or h > 360:
                raise ValueError(f"Hue must be a degree from 0 to 360: was {h}")
            self.hue = h

            if s > 1 or s < 0:
                raise ValueError(
                    f"Saturation must be a percentage from 0.0 to 1.0: was {s}"
                )
            self.saturation = s

            if l > 1 or l < 0:
                raise ValueError(
                    f"Lightness must be a percentage from 0.0 to 1.0: was {l}"
                )
            self.lightness = l

        @property
        def h(self) -> int:
            """Hue value in degrees. 0-360 where 0 is red, 120 is green, and 240 is blue.
            Readonly"""
            return self.hue

        @property
        def s(self) -> float:
            """Saturation value as a percent. 0% means a shade of gray and 100% means full color.
            Readonly"""
            return self.saturation

        @property
        def l(self) -> float:
            """Lightness value as a percent. 0% is black, 100% is white. Readonly"""
            return self.lightness

        def to_rgb(self) -> Color.RGB:
            """Convert from hsl to rgb."""
            return Color.RGB(*self.rgb())

        def rgb(self) -> tuple[int, int, int]:
            return tuple(
                round(i * 255)
                for i in colorsys.hls_to_rgb(self.h / 360, self.l, self.s)
            )

        def as_str(self) -> str:
            return f"hsl({self.h},{self.s},{self.l})"

    class HSV(ColorBase):
        """Hue, saturation, lightness (HSL) representation of a color."""

        hue: int
        """Hue of the color in degrees. 0-360 where 0 is red, 120 is green, and 240 is blue."""

        saturation: float
        """Saturation of the color as a percent. 0% means a shade of gray and 100% means full
        color."""

        value: float
        """Brightness of the color as a percent. 0% is black, 100% is white."""

        def __init__(self, h: int, s: float, v: float) -> None:
            if h < 0 or h > 360:
                raise ValueError(f"Hue must be a degree from 0 to 360: was {h}")
            self.hue = h

            if s > 1 or s < 0:
                raise ValueError(
                    f"Saturation must be a percentage from 0.0 to 1.0: was {s}"
                )
            self.saturation = s

            if v > 1 or v < 0:
                raise ValueError(
                    f"Lightness must be a percentage from 0.0 to 1.0: was {v}"
                )
            self.value = v

        @property
        def h(self) -> int:
            """Hue value in degrees. 0-360 where 0 is red, 120 is green, and 240 is blue.
            Readonly"""
            return self.hue

        @property
        def s(self) -> float:
            """Saturation value as a percent. 0% means a shade of gray and 100% means full color.
            Readonly"""
            return self.saturation

        @property
        def v(self) -> float:
            """Brightness value as a percent. 0% is black, 100% is white. Readonly"""
            return self.value

        def to_rgb(self) -> Color.RGB:
            """Convert from hsl to rgb."""
            return Color.RGB(*self.rgb())

        def rgb(self) -> tuple[int, int, int]:
            return tuple(
                round(i * 255)
                for i in colorsys.hsv_to_rgb(self.h / 360, self.s, self.v)
            )

        def as_str(self) -> str:
            return f"hsv({self.h},{self.s},{self.v})"

    class YIQ(ColorBase):
        """Luminance, in-phase, and quadrature (YIQ) representation of a color.
        Warning: Lossy when converting to other formats
        """

        luminance: int
        """grayscale value of the color."""

        in_phase: int
        """orange to blue value of the color."""

        quadrature: int
        """purple to green value of the color."""

        def __init__(self, y: float, i: float, q: float) -> None:
            if y < 0 or y > 1:
                raise ValueError(f"Luminance must be a value from 0 to 1: was {y}")
            self.luminance = y

            if i < -0.523 or i > 0.523:
                raise ValueError(
                    f"in_phase must be a value from -0.523 to 0.523: was {i}"
                )
            self.in_phase = i

            if q < -0.596 or q > 0.596:
                raise ValueError(
                    f"quadrature must be a value from -0.596 to 0.596: was {q}"
                )
            self.quadrature = q

        @property
        def y(self) -> int:
            """grayscale value of the color. Readonly"""
            return self.luminance

        @property
        def i(self) -> int:
            """orange to blue value of the color. Readonly"""
            return self.in_phase

        @property
        def q(self) -> int:
            """purple to green value of the color. Readonly"""
            return self.quadrature

        def to_rgb(self) -> Color.RGB:
            """Convert from yiq to rgb."""
            return Color.RGB(*self.rgb())

        def rgb(self) -> tuple[int, int, int]:
            return tuple(
                round(i * 255) for i in colorsys.yiq_to_rgb(self.y, self.i, self.q)
            )

        def as_str(self) -> str:
            return f"yiq({self.y},{self.i},{self.q})"

    class XTERM(ColorBase):
        """Xterm representation of a color. 256 colors."""

        def __init__(self, color: int | str) -> None:
            self.value = None

            if isinstance(color, int):
                if color < 0 or color > 255:
                    raise ValueError("Xterm color must be between 0 and 255")
                self.value = color

            longest_match = ""
            if isinstance(color, str):
                for xterm in XTERM_COLORS:
                    if xterm[1].lower() == color.lower():
                        self.value = xterm[0]
                    else:
                        matching = ""
                        for c1, c2 in zip(color.lower(), xterm[1].lower()):
                            if c1 != c2:
                                break
                            matching += c1

                        if len(matching) > len(longest_match):
                            longest_match = matching

                if self.value is None:
                    raise ValueError(
                        f"Invalid xterm color name {color!r}. Did you mean {longest_match!r}"
                    )

            if self.value is None:
                raise ValueError(f"Invalid xterm color code: was {color}")

        @property
        def code(self) -> int:
            """The color code of the xterm color. Readonly."""
            return self.value

        @cached_property
        def name(self) -> str:
            """The name of the xterm color."""
            return XTERM_COLORS[self.code][1]

        def to_rgb(self) -> Color.RGB:
            """Convert from xterm to rgb."""
            return Color.RGB(*XTERM_COLORS[self.code][2])

        def rgb(self) -> tuple[int, int, int]:
            return XTERM_COLORS[self.code][2]

        def as_str(self) -> str:
            return f"xterm({self.code})"

    @staticmethod
    def sample() -> str:
        """Build a ansi encoded sample that can be printed to the terminal."""

        rgb = Color.RGB(255, 0, 0)
        hsl = Color.HSL(173, 0.72, 0.49)
        hsv = Color.HSV(245, 0.522, 0.878)  # 746BE0
        c_hex = Color.HEX("#007900")
        yiq = Color.YIQ(0.393, -0.304, 0.087)
        xterm = Color.XTERM(166)

        colors = [
            rgb.preview(),
            c_hex.preview(),
            yiq.preview(),
            hsl.preview(),
            hsv.preview(),
            xterm.preview(),
        ]
        return "\n".join(colors)
