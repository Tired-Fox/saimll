"""SIML includes a parser to get literal strings from SIML markup, along with a pprint
function that outputs the literal string from a SIML markup.

Raises:
    MacroMissingError: If there is an incorrect macro or color specifier
    MacroError: If there is a general formatting error with a macro
"""
from __future__ import annotations

from typing import Iterator, Callable
from .tokens import Token, Color, Text, Bold, Underline, Formatter, HLink, Reset, Func, Escape
from .formatting import BOLD, UNDERLINE, RESET, LINK, FUNC

__all__ = [
    "SIML",
]


class SIMLParser:
    """Main class exposed by the library to give access the markup utility functions."""

    def __init__(self) -> None:
        self._funcs = FUNC

    def __split_macros(self, text: str) -> Iterator[str]:
        """Takes a macro, surrounded by brackets `[]` and splits the nested/chained macros.

        Args:
            text (str): The contents of the macro inside of brackets `[]`

        Yields:
            Iterator[str]: Iterates from each token to the next until entire macro is consumed
        """
        schars = ["$", "@", "~", "!"]
        last, index = 0, 0
        while index < len(text):
            if index != 0:
                if text[index] in schars:
                    yield text[last:index]
                    last = index

            index += 1

        if last != index:
            yield text[last:]

    def __parse_macro(self, text: str) -> list[Token]:
        """Takes the chained, nested, or single macros and generates a token based on it's type.

        Args:
            text (str): The macro content inside of brackets `[]`

        Returns:
            list[Token]: The list of tokens created from the macro content inside of brackets `[]`
        """
        tokens = []

        if len(text) == 0:
            tokens.append(Reset())
            return tokens

        for sub_macro in self.__split_macros(text):
            sub_macro = sub_macro.strip()
            if sub_macro.startswith("@"):
                tokens.append(Color(sub_macro))
            elif sub_macro.startswith("~"):
                tokens.append(HLink(sub_macro))
            elif sub_macro.startswith("^"):
                tokens.append(Func(sub_macro, self._funcs))
            elif sub_macro.startswith("$"):
                tokens.append(Escape())
        return tokens

    def __optimize(self, tokens: list) -> list:
        """Takes the generated tokens from the markup string and removes and combines tokens where
        possible.

        Example:
            Since there can be combinations such as fg, bg, bold, and underline they can be
            represented in two ways.
            * Unoptimized - `\\x1b[1m\\x1b[4m\\x1b[31m\\x1b[41m`
            * Optimized - `\\x1b[1;4;31;41m`


            Also, if many fg, bg, bold, and underline tokens are repeated they will be optimized.
            * `*Bold* *Still bold` translates to `\\x1b[1mBold still bold\\x1b[0m`
                * You can see that it removes unnecessary tokens as the affect is null.
            * `[@> red @> green]Green text` translates to `\\x1b[32mGreen text\\x1b[0m`
                * Here is an instance of overriding the colors. Order matters here, but since you
                are applying the foreground repeatedly only the last one will show up. So all
                previous declerations are removed.

        Args:
            tokens (list): The list of tokens generated from parsing the SIML markup

        Returns:
            list: The optimized list of tokens. Bold, underline, fg, and bg tokens are combined into
            Formatter tokens
        """
        open_link = False
        func = None
        formatter = Formatter()
        last_format = formatter
        output = []

        for token in tokens:
            if isinstance(token, Color):
                formatter.color = token
            elif isinstance(token, Bold):
                formatter.bold = token
            elif isinstance(token, Underline):
                formatter.underline = token
            elif isinstance(token, HLink):
                if token.closing and open_link:
                    open_link = False
                    output.append(token)
                elif not token.closing and open_link:
                    token.value = LINK.CLOSE + token.value
                    output.append(token)
                else:
                    open_link = True
                    output.append(token)
            elif isinstance(token, Func):
                func = token
            else:
                if not formatter.is_empty():
                    last_format = formatter
                    output.append(formatter)
                    formatter = Formatter()
                if func is not None:
                    new_value = func.exec(token.value)
                    if isinstance(new_value, str):
                        token.value = new_value
                        output.append(token)
                        output.append(last_format)
                    func = None
                else:
                    output.append(token)

        if not formatter.is_empty():
            last_format = formatter
            output.append(formatter)
        if open_link:
            output.append(HLink("~"))

        return output

    def __parse_tokens(self, string: str):
        """Splits the SIML markup string into tokens. If `*` or `_` are found then a Bold or
        Underline token will be generated respectively. If `[` is found then it marches to the end
        of the macro, `]`, and then parses it. All special characters can be escaped with `\\`

        Args:
            text (str): The SIML markup string that will be parsed

        Raises:
            MacroError: If a macro is not closed

        Returns:
            str: The translated ansi representation of the given sting
        """

        bold_state = BOLD.POP
        """BOLD: The current state/value of being bold. Either is bold, or is not bold."""

        underline_state = UNDERLINE.POP
        """UNDERLINE: The current state/value of being underlined. Either is underlined, or is not 
        underlined."""
        
        global_escape: bool = False
        """The escaped status based on the escape macro."""

        text: list = []
        """The chunks of text between special tokens."""

        output: list = []
        """Final output of the parse."""

        escaped: bool = False
        """Indicates whether to escape the next character or not."""

        index: int = 0
        """Current index of walking through the markup string."""

        def consume_macro(index: int, global_escape: bool):
            """Starts from start of the macro and grabs characters until at the end of the macro.

            Args:
                index (int): The current index in the string

            Raises:
                MacroError: If at the end of the markup string and the macro isn't closed

            Returns:
                int: Index after moving to the end of the macro
            """
            start = index
            index += 1
            char = string[index]
            macro = []
            while char != "]":
                macro.append(char)
                index += 1
                if index == len(string):
                    raise ValueError(f"Macro's must be closed \n {string[start-1:]}")
                char = string[index]
            tokens = self.__parse_macro("".join(macro))
            if len([token for token in tokens if isinstance(token, Escape)]) % 2 != 0:
                global_escape = not global_escape
            output.extend([token for token in tokens if not isinstance(token, Escape)])

            return index, global_escape

        while index < len(string):
            char = string[index]
            if char == "*" and not escaped and not global_escape:
                if len(text) > 0:
                    output.append(Text("".join(text)))
                    text = []
                bold_state = BOLD.inverse(bold_state)
                output.append(Bold(bold_state))
            elif char == "_" and not escaped and not global_escape:
                if len(text) > 0:
                    output.append(Text("".join(text)))
                    text = []
                underline_state = UNDERLINE.inverse(underline_state)
                output.append(Underline(underline_state))
            elif char == "[" and not escaped:
                if len(text) > 0:
                    output.append(Text("".join(text)))
                    text = []
                index, global_escape = consume_macro(index, global_escape)
            elif char == "\\" and not escaped:
                escaped = True
            else:
                text.append(char)
                escaped = False

            index += 1

        if len(text) > 0:
            output.append(Text("".join(text)))
            text = []

        return "".join(str(token) for token in self.__optimize(output)) + RESET

    def define(self, name: str, callback: Callable) -> None:
        """Adds a callable function to the functions macro. This allows it to be called from withing
        a macro. Functions must return a string, if it doesn't it will ignore the the return. It
        will automaticaly grab the next text block and use it for the input of the function.
        The function should manipulate the text and return the result.

        Args:
            name (str): The name associated with the function. Used in the macro
            callback (Callable): The function to call when the macro is executed
        """
        self._funcs.update({name: callback})

    def parse(self, text: str) -> str:
        """Parses a SIML markup string and returns the translated ansi equivilent.

        Args:
            text (str): The SIML markup string

        Returns:
            str: The ansi translated string
        """
        return self.__parse_tokens(text)

    def encode(self, text: str) -> str:
        """"""

    def print(self, *args) -> None:
        """Works similare to the buildin print function.
        Takes all arguments and passes them through the parser.
        When finished it will print the results to the screen with a space inbetween the args.

        Args:
            *args (Any): Any argument that is a string or has a __str__ implementation
        """
        parsed = []
        for arg in args:
            parsed.append(self.parse(str(arg)))

        print(*parsed)

    @staticmethod
    def escape(text: str) -> str:
        """Utility to automatically escape/encode special markup characters.

        Args:
            text (str): The string to encode/escape

        Returns:
            str: The escaped/encoded version of the given string
        """
        schars = ["\\", "*", "_", "["]
        for char in schars:
            text = f"\\{char}".join(text.split(char))
        return text

    @staticmethod
    def strip(text: str) -> str:
        """Removes SIML specific markup.

        Args:
            text (str): String to strip markup from.

        Returns:
            str: Version of text free from markup.S
        """
        from re import sub

        return sub(
            r"\x1b\[(\d{0,2};?)*m|(?<!\\)\*|(?<!\\)_|(?<!\\)\[[^\[\]]+\]|\\",
            "",
            text,
        )


SIML = SIMLParser()
