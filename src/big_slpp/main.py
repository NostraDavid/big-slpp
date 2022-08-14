import re
import sys
from numbers import Number
from typing import Any, Optional

ERRORS: dict[str, str] = {
    "unexp_end_string": "Unexpected end of string while parsing Lua string.",
    "unexp_end_table": "Unexpected end of table while parsing Lua string.",
    "mfnumber_minus": "Malformed number (no digits after initial minus).",
    "mfnumber_dec_point": "Malformed number (no digits after decimal point).",
    "mfnumber_sci": "Malformed number (bad scientific format).",
}


def sequential(lst: list[Any]) -> bool:
    """Are the variables in the list sequestial?"""
    length: int = len(lst)
    if length == 0 or lst[0] != 0:
        return False
    for i in range(length):
        if i + 1 < length:
            if lst[i] + 1 != lst[i + 1]:
                return False
    return True


class ParseError(Exception):
    pass


class SLPP(object):
    def __init__(self) -> None:
        self.text: str = ""  # the text/code to parser
        self.ch: Optional[str] = ""  # the current character we're handling
        self.at: int = 0  # the current position within the text
        self.len: int = 0  # total length of self.text
        self.depth: int = 0  # no clue yet what this is, lol
        self.space: re.Pattern[str] = re.compile(r"\s", re.M)  # regex to gobble whitespaces
        self.alnum: re.Pattern[str] = re.compile(r"\w", re.M)  # regex to gobble alphanumerics
        self.newline: str = "\n"
        self.tab: str = "\t"

    def decode(self, text) -> Optional[Any]:
        if not text:
            return None
        self.text = text
        self.at, self.ch, self.depth = 0, "", 0
        self.len = len(text)
        self.next_chr()
        result: Optional[Any] = self.value()
        return result

    def encode(self, obj) -> str:
        self.depth = 0
        return self.__encode(obj)

    def __encode(self, obj: str | bytes | bool | None | Number | list | tuple | dict) -> str:
        s: str = ""
        tab: str = self.tab
        newline: str = self.newline

        if isinstance(obj, str):
            s += '"%s"' % obj.replace(r'"', r"\"")
        elif isinstance(obj, bytes):
            s += '"{}"'.format("".join(r"\x{:02x}".format(c) for c in obj))
        elif isinstance(obj, bool):
            s += str(obj).lower()
        elif obj is None:
            s += "nil"
        elif isinstance(obj, Number):
            s += str(obj)
        elif isinstance(obj, (list, tuple, dict)):
            self.depth += 1
            if len(obj) == 0 or (
                not isinstance(obj, dict)
                and len([x for x in obj if isinstance(x, Number) or (isinstance(x, str) and len(x) < 10)]) == len(obj)
            ):
                newline = tab = ""
            dp: str = tab * self.depth
            s += "%s{%s" % (tab * (self.depth - 2), newline)
            if isinstance(obj, dict):
                key_list: list[str] = ["[%s]" if isinstance(k, Number) else '["%s"]' for k in obj.keys()]
                contents: list[str] = [
                    dp + (key + " = %s") % (k, self.__encode(v)) for (k, v), key in zip(obj.items(), key_list)
                ]
                s += (",%s" % newline).join(contents)
            else:
                s += (",%s" % newline).join([dp + self.__encode(el) for el in obj])
            self.depth -= 1
            s += ",%s%s}" % (newline, tab * self.depth)
        return s

    def white(self) -> None:
        """Gobble up whitespaces"""
        while self.ch:
            if self.space.match(self.ch):
                self.next_chr()
            else:
                break
        self.comment()

    def comment(self) -> None:
        if not (self.ch == "-" and self.next_is("-")):
            return
        self.next_chr()
        # TODO: for fancy comments need to improve
        multiline: bool | None = self.next_chr() and self.ch == "[" and self.next_is("[")
        while self.ch:
            if multiline:
                if self.ch == "]" and self.next_is("]"):
                    self.next_chr()
                    self.next_chr()
                    self.white()
                    break
            # `--` is a comment, skip to next new line
            elif re.match("\n", self.ch):
                self.white()
                break
            self.next_chr()

    def next_is(self, value: Optional[str]) -> bool:
        if self.at >= self.len:
            return False
        return self.text[self.at] == value

    def prev_is(self, value: str) -> bool:
        if self.at < 2:
            return False
        return self.text[self.at - 2] == value

    def next_chr(self) -> bool:
        if self.at >= self.len:
            self.ch = None
            return False
        self.ch = self.text[self.at]
        self.at += 1
        return True

    def value(
        self,
    ) -> Optional[Any]:
        self.white()
        if not self.ch:
            return None
        if self.ch == "{":
            return self.object()
        if self.ch == "[":
            self.next_chr()
        if self.ch in ['"', "'", "["]:
            return self.string(self.ch)
        if self.ch.isdigit() or self.ch == "-":
            return self.number()
        return self.word()

    def string(self, end: Optional[str] = None) -> str:
        s: str = ""
        start: Optional[str] = self.ch
        if end == "[":
            end = "]"
        if start in ['"', "'", "["]:
            double: bool = start == "[" and self.prev_is(start)
            while self.next_chr():
                if self.ch == end and (not double or self.next_is(end)):
                    self.next_chr()
                    if start != "[" or self.ch == "]":
                        if double:
                            self.next_chr()
                        return s
                if self.ch == "\\" and start == end:
                    self.next_chr()
                    if self.ch != end:
                        s += "\\"
                s += self.ch
        raise ParseError(ERRORS["unexp_end_string"])

    def object(self) -> dict[str | float | int | bool | tuple[Any], Any] | list[Any]:
        o: dict[str | float | int | bool | tuple[Any], Any] | list[Any] = {}
        k: str | float | int | bool | tuple[Any] | None = None
        idx: int = 0
        numeric_keys: bool = False
        self.depth += 1
        self.next_chr()
        self.white()
        if self.ch and self.ch == "}":
            self.depth -= 1
            self.next_chr()
            return o  # Exit here
        else:
            while self.ch:
                self.white()
                if self.ch == "{":
                    o[idx] = self.object()
                    idx += 1
                    continue
                elif self.ch == "}":
                    self.depth -= 1
                    self.next_chr()
                    if k is not None:
                        o[idx] = k
                    if len([key for key in o if isinstance(key, (str, float, bool, tuple))]) == 0:
                        so: list[Any] = sorted([key for key in o])
                        if sequential(so):
                            ar: list[Any] = []
                            for key in o:
                                ar.insert(key, o[key])
                            o = ar  # this changes o's type
                    return o  # or here
                else:
                    if self.ch == ",":
                        self.next_chr()
                        continue
                    else:
                        k = self.value()
                        if self.ch == "]":
                            self.next_chr()
                    self.white()
                    ch: str = self.ch
                    if ch in ("=", ","):
                        self.next_chr()
                        self.white()
                        if ch == "=":
                            o[k] = self.value()
                        else:
                            o[idx] = k
                        idx += 1
                        k = None
        raise ParseError(ERRORS["unexp_end_table"])  # Bad exit here

    words: dict[str, bool | None] = {"true": True, "false": False, "nil": None}

    def word(self) -> str | bool | None:
        s: Optional[str] = ""
        if self.ch != "\n":
            s = self.ch
        self.next_chr()
        while self.ch is not None and self.alnum.match(self.ch) and s not in self.words:
            # In the while, we ensure that self.ch isn't None, so shut up, Pylance!
            s += self.ch  # type: ignore
            self.next_chr()
        return self.words.get(s, s)

    def number(self) -> int | float:
        def next_digit(err) -> str:
            n: str = self.ch
            self.next_chr()
            if not self.ch or not self.ch.isdigit():
                raise ParseError(err)
            return n

        n: str = ""
        try:
            if self.ch == "-":
                n += next_digit(ERRORS["mfnumber_minus"])
            n += self.digit()
            if n == "0" and self.ch in ["x", "X"]:
                n += self.ch
                self.next_chr()
                n += self.hex()
            else:
                if self.ch and self.ch == ".":
                    n += next_digit(ERRORS["mfnumber_dec_point"])
                    n += self.digit()
                if self.ch and self.ch in ["e", "E"]:
                    n += self.ch
                    self.next_chr()
                    if not self.ch or self.ch not in ("+", "-"):
                        raise ParseError(ERRORS["mfnumber_sci"])
                    n += next_digit(ERRORS["mfnumber_sci"])
                    n += self.digit()
        except ParseError:
            t, e = sys.exc_info()[:2]
            print(e)
            return 0
        try:
            return int(n, 0)
        except Exception:
            pass
        return float(n)

    def digit(self) -> str:
        n: str = ""
        while self.ch and self.ch.isdigit():
            n += self.ch
            self.next_chr()
        return n

    def hex(self) -> str:
        n: str = ""
        while self.ch and (self.ch in "ABCDEFabcdef" or self.ch.isdigit()):
            n += self.ch
            self.next_chr()
        return n


slpp: SLPP = SLPP()

__all__: list[str] = ["slpp"]
