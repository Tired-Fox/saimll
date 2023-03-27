from typing import Any, Callable, Optional
from types import GenericAlias, UnionType
from saimll.saiml import SAIML
from inspect import getfullargspec, signature, _empty


class Missing:
    def __repr__(self) -> str:
        return f"MISSING"


MISSING = Missing()

def _type(val: Any) -> type:
    if isinstance(val, type):
        return val
    return type(val)

def ppath(*args: str, clr: str = "yellow", spr: str = " > ") -> str:
    """Takes all the arguments, segments of path, and combines them with the given seperator and color.

    Args:
        clr (int): The color to apply to each segment of the path
        spr (str): The seperator between each segement of the path

    Returns:
        str: The formatted string
    """
    return f"{spr}".join([SAIML.parse(f"[@F {clr}$]{arg.strip()}[@F]") for arg in args])

def pprint(
    *values: Any,
    depth: int = 2,
    end: str = "\n",
    seperator: str = " ",
    handler: Optional[Callable] = None,
):
    """Pretty print any value with formatting and color."""
    from sys import stdout

    values = [p_value(value, depth=depth, handler=handler) for value in values]
    stdout.write(seperator.join(values) + end)


def p_value(
    value: Any,
    depth: int = 1,
    indent: int = 0,
    decode: bool = True,
    leading: bool = False,
    handler: Optional[Callable] = None,
) -> str:
    """Take a given value and return the appropriatly encoded value"""

    if value is None:
        return p_none(decode=decode)

    if isinstance(value, str):
        return p_str(value, indent=indent, decode=decode)

    if isinstance(value, bool):
        return p_bool(value, indent=indent, decode=decode)

    if isinstance(value, (int, float)):
        return p_num(value, indent=indent, decode=decode)

    if isinstance(value, (list, tuple, set)):
        return p_collection(
            value, depth=depth, indent=indent, decode=decode, leading=leading
        )

    if isinstance(value, dict):
        return p_dict(value, depth=depth, indent=indent, decode=decode, leading=leading)

    if isinstance(value, Callable) and not isinstance(value, type):
        if handler is not None:
            return handler(value, depth, indent, decode, leading)
        return p_def(value, indent=indent, decode=decode)

    if handler is not None:
        return handler(value, depth, indent, decode, leading)
    return p_type(value, indent=indent, decode=decode)


def p_def(value: Callable, indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded colored bool str.

    Args:
        value (bool): The bool to encode.
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Returns:
        `[@F #8aadf4]{value}` == `\\x1b[38;5;147m{value}\\x1b[0m`
    """

    def build_arg_data(args: list[str], defaults: set[Any], annotations: dict):
        styled_args = []
        if args is not None:
            for i in range(len(args) - 1, -1, -1):
                styled_args.append([args[i], MISSING, MISSING])
            if defaults is not None:
                for i, default in enumerate(defaults):
                    styled_args[i][2] = default
            styled_args.reverse()
            if annotations is not None:
                for i, arg in enumerate(styled_args):
                    if arg[0] in annotations:
                        styled_args[i][1] = annotations[arg[0]]

        return styled_args

    (
        args,
        varargs,
        varkw,
        defaults,
        kwonlyargs,
        kwonlydefaults,
        annotations,
    ) = getfullargspec(value)
    styled_args = build_arg_data(args, defaults, annotations)
    styled_args.extend(build_arg_data(kwonlyargs, kwonlydefaults, annotations))

    if varargs is not None:
        styled_args.append(
            [
                f"*{varargs}",
                annotations[varargs] if varargs in annotations else MISSING,
                MISSING,
            ]
        )

    if varkw is not None:
        styled_args.append(
            [
                f"**{varkw}",
                annotations[varkw] if varkw in annotations else MISSING,
                MISSING,
            ]
        )

    args = []
    for arg in styled_args:
        args.append(p_arg(arg, decode=False))

    return_annotation = signature(value).return_annotation
    if return_annotation == _empty:
        return_annotation = f" -> {p_none(decode=False)}"
    else:
        return_annotation = f" -> {p_value(return_annotation, decode=False)}"

    val = f"[@F #8aadf4$]{value.__name__}[$@F]({', '.join(args)}){return_annotation}"
    if decode:
        return SAIML.parse(val)
    return val


def p_arg(value: tuple[str, Any, Any], indent: int = 0, decode: bool = True):
    if isinstance(value[1], (GenericAlias, UnionType, str)):
        _type = (
            f": [@F#f5a97f]{SAIML.escape(str(value[1]))}[@F]" if not isinstance(value[1], Missing) else ""
        )
    elif isinstance(value[1], type):
        _type = f": [$]{p_value(value[1], decode=False)}[$]"

    if (
        callable(value[2])
        and not isinstance(value[2], Missing)
        and value[2] is not None
    ):
        _default = f" = [$]{value[2]!r}[$]"
    else:
        _default = (
            f" = {p_value(value[2], decode=False)}"
            if not isinstance(value[2], Missing)
            else ""
        )
    val = f"{' '*indent}[@F#f5bde6$]{value[0]}[$@F]{_type}{_default}"
    
    if decode:
        return SAIML.parse(val)
    return val


def p_type(value: type, indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded colored bool str.

    Args:
        value (bool): The bool to encode.
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Returns:
        `[@F #f5a97f]{value}` == `\\x1b[38;5;147m{value}\\x1b[0m`
    """

    if isinstance(value, type):
        val = f"[@F #f5a97f]{SAIML.escape(_type(value).__name__)}[@F]"
    else:
        if hasattr(value, "__repr__"):
            val = repr(value)
        elif hasattr(value, "__str__"):
            val = str(value)
        else:
            val = f"[@F #f5a97f]{SAIML.escape(type(value).__name__)}[@F]"

    if decode:
        return SAIML.parse(val)
    return val


def p_dict(
    data: dict,
    depth: int = 1,
    indent: int = 0,
    decode: bool = True,
    leading: bool = False,
) -> str:
    """Construct an ansi encoded colored dictionary str.

    Args:
        data (dict): The dictionary to encode.
        depth (int): Amount of recursion before cutting out data.
        indent (int): The amount of spaces added to the prefix of the value. Indent
        is appied to all lines but to the first line of a multiline string. If there
        is only one line the indent is applied to the one line.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Returns:
        `[@F 210]None` == `\\x1b[38;5;210mNone\\x1b[0m`
    """
    open_bracket = p_symbol("{", decode=False)
    close_bracket = p_symbol("}", decode=False)

    values = []
    if depth == 0:
        val = open_bracket + "[@F 210]…[@F]" + close_bracket
    else:
        # list dict and tuple are ellipsed when at max depth
        for key, value in data.items():
            values.append(
                f"""{p_str(key, decode=False)}: {
                        p_value(
                            value,
                            depth=depth-1,
                            indent=indent+2,
                            decode=False,
                        )
                }"""
            )

        if len(values) > 0:
            val = (
                (" " * indent)
                if leading
                else ""
                + open_bracket
                + "\n"
                + (" " * (indent + 2))
                + f",\n{' ' * (indent + 2)}".join(values)
                + "\n"
                + (" " * indent)
                + close_bracket
            )
        else:
            val = open_bracket + close_bracket

    if decode:
        return SAIML.parse(val)
    return val


def p_none(indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded colored `None` str.

    Args:
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Returns:
        `[@F 147]None` or `\\x1b[38;5;147mNone\\x1b[0m`
    """

    val = "[@F 147]None[@F]"
    if decode:
        return SAIML.parse(val)
    return val


def p_num(num: int | float, indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded colored int str.

    Args:
        num (int): The number to encode.
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Returns:
        `[@F yellow]{num}` == `\\x1b[33m{num}\\x1b[0m`
    """

    val = f"[@F yellow]{num}[@F]"
    if decode:
        return SAIML.parse(val)
    return val


def p_bool(value: bool, indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded colored bool str.

    Args:
        value (bool): The bool to encode.
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Returns:
        `[@F 147]{value}` == `\\x1b[38;5;147m{value}\\x1b[0m`
    """

    val = f"[@F 147]{value}[@F]"
    if decode:
        return SAIML.parse(val)
    return val


def p_str(string: str, indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded green repr of a string.

    Args:
        string (str): The string to encode.
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Example:
        `The \\n cat` == `\\x1b[32m'The \\n cat'\\x1b[0m`

    Returns:
        `[@F green]{repr(str)}` == `\\x1b[32m{repr(str)}\\x1b[0m`
    """
    from re import sub

    string = SAIML.escape(repr(string))

    # Color special characters
    string = sub(
        r"(\\\\n|\\\\t|\\\\r|\\\\x1b|(?<=b)\\\[[0-9;]+m)",
        r"[@F cyan]\1[@F green]",
        string,
    )

    val = f"[@F green]{string}[@F]"
    if decode:
        return SAIML.parse(val)
    return val


def p_symbol(sym: str, indent: int = 0, decode: bool = True) -> str:
    """Construct an ansi encoded bold symbol.

    Args:
        sym (str): The symbol to encode.
        indent (int): The amount of spaces added to the prefix of the value.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Example:
        `{` == `\\x1b[1m{\\x1b[0m`

    Returns:
        `*{symbol}*` == `\\x1b[1mNone\\x1b[0m`
    """

    val = f"*{SAIML.escape(sym)}*"
    if decode:
        return SAIML.parse(val)
    return val


def p_collection(
    collection: list | tuple,
    depth: int = 1,
    indent: int = 0,
    decode: bool = True,
    leading: bool = False,
) -> str:
    """Construct an ansi encoded bold symbol.

    Args:
        collection (list | tuple): The list or tuple to encode.
        indent (int): The amount of spaces added to the prefix of the value. Indent
        is appied to all lines but to the first line of a multiline string. If there
        is only one line the indent is applied to the one line.
        decode (bool): Whether to decode SAIML markup string to ansi.

    Example:
        `{` == `\\x1b[1m{\\x1b[0m`

    Returns:
        `*{symbol}*` == `\\x1b[1mNone\\x1b[0m`
    """

    if isinstance(collection, list):
        open_bracket = p_symbol("[", decode=False)
        close_bracket = p_symbol("]", decode=False)
    elif isinstance(collection, (tuple, set)):
        open_bracket = p_symbol("(", decode=False)
        close_bracket = p_symbol(")", decode=False)

    if depth == 0:
        val = open_bracket + "[@F 210]…[@F]" + close_bracket
    else:
        values = []
        for value in collection:
            values.append(
                p_value(
                    value,
                    depth=depth - 1,
                    indent=indent + 2,
                    decode=False,
                    leading=False,
                )
            )

        prefix = (" " * indent) if leading else ""
        if len(values) > 0:
            val = (
                prefix
                + open_bracket
                + "\n"
                + (" " * (indent + 2))
                + f",\n{' ' * (indent + 2)}".join(values)
                + "\n"
                + (" " * indent)
                + close_bracket
            )
        else:
            val = open_bracket + close_bracket

    if decode:
        return SAIML.parse(val)
    return val
