from typing import Any
import pytest

from big_slpp.main import slpp


# Utility functions


def is_iterator(obj) -> bool:
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def differs(value, origin) -> None:
    if type(value) is not type(origin):
        raise AssertionError("Types does not match: {0}, {1}".format(type(value), type(origin)))

    if isinstance(origin, dict):
        for key, item in origin.items():
            try:
                differs(value[key], item)
            except KeyError:
                raise AssertionError(
                    """{0} not match original: {1}; Key: {2}, item: {3}""".format(value, origin, key, item)
                )
        return

    if isinstance(origin, str):
        assert value == origin, "{0} not match original: {1}.".format(value, origin)
        return

    if is_iterator(origin):
        for i in range(0, len(origin)):
            try:
                differs(value[i], origin[i])
            except IndexError:
                raise AssertionError("{0} not match original: {1}. Item {2} not found".format(value, origin, origin[i]))
        return

    assert value == origin, "{0} not match original: {1}.".format(value, origin)


def test_is_iterator() -> None:
    assert is_iterator(list()), "list is not an iterable!?"
    assert is_iterator(set()), "set is not an iterable!?"
    assert is_iterator(dict()), "dict is not an iterable!?"
    assert not is_iterator(int), "int is an iterable!?"
    assert not is_iterator(str), "str is an iterable!?"
    assert not is_iterator(float), "float is an iterable!?"


def test_differ() -> None:
    # Same:
    differs(1, 1)
    differs([2, 3], [2, 3])
    differs({"1": 3, "4": "6"}, {"4": "6", "1": 3})
    differs("4", "4")

    # Different:
    with pytest.raises(AssertionError, match="1 not match original: 2.\nassert 1 == 2"):
        differs(1, 2)
    with pytest.raises(AssertionError, match="2 not match original: 3.\nassert 2 == 3"):
        differs([2, 3], [3, 2])
    with pytest.raises(
        AssertionError, match="{'6': 4, '3': '1'} not match original: {'4': '6', '1': 3}; Key: 4, item: 6"
    ):
        differs({"6": 4, "3": "1"}, {"4": "6", "1": 3})
    with pytest.raises(AssertionError, match="4 not match original: no."):
        differs("4", "no")


def test_numbers() -> None:
    # Integer and float:
    assert slpp.decode("3") == 3
    assert slpp.decode("4.1") == 4.1
    assert slpp.encode(3) == "3"
    assert slpp.encode(4.1) == "4.1"

    # Negative float:
    assert slpp.decode("-0.45") == -0.45
    assert slpp.encode(-0.45) == "-0.45"

    # Scientific:
    assert slpp.decode("3e-7") == 3e-7
    assert slpp.decode("-3.23e+17") == -3.23e17
    assert slpp.encode(3e-7) == "3e-07"
    assert slpp.encode(-3.23e17) == "-3.23e+17"

    # Hex:
    assert slpp.decode("0x3a") == 0x3A

    differs(
        slpp.decode(
            """{
        ID = 0x74fa4cae,
        Version = 0x07c2,
        Manufacturer = 0x21544948
    }"""
        ),
        {"ID": 0x74FA4CAE, "Version": 0x07C2, "Manufacturer": 0x21544948},
    )


def test_bool() -> None:
    assert slpp.encode(True) == "true"
    assert slpp.encode(False) == "false"

    assert slpp.decode("true") is True
    assert slpp.decode("false") is False


def test_nil() -> None:
    assert slpp.encode(None) == "nil"
    assert slpp.decode("nil") is None


def test_table() -> None:
    # Bracketed string key:
    assert slpp.decode("{[10] = 1}") == {10: 1}

    # Void table:
    assert slpp.decode("{nil}") == {}

    # Values-only table:
    assert slpp.decode('{"10"}') == ["10"]

    # Last zero
    assert slpp.decode("{0, 1, 0}") == [0, 1, 0]

    # Mixed encode
    assert slpp.encode({"0": 0, "name": "john"}) == '{\n\t["0"] = 0,\n\t["name"] = "john"\n}'


def test_string() -> None:
    # Escape test:
    assert slpp.decode(r"'test\'s string'") == "test's string"

    # Add escaping on encode:
    assert slpp.encode({"a": 'func("call()");'}) == '{\n\t["a"] = "func(\\"call()\\");"\n}'

    # Strings inside double brackets
    longstr: str = ' ("word") . [ ["word"] . ["word"] . ("word" | "word" | "word" | "word") . ["word"] ] '
    assert slpp.decode("[[" + longstr + "]]") == longstr

    # self.assertEqual(slpp.decode("{ [0] = [[" + longstr + ']], [1] = "a"}'), [longstr, "a"])

    assert slpp.decode("{ [0] = [[" + longstr + ']], [1] = "a"}') == [longstr, "a"]


def test_basic() -> None:
    # No data loss:
    data: str = '{ array = { 65, 23, 5 }, dict = { string = "value", array = { 3, 6, 4}, mixed = { 43, 54.3, false, string = "value", 9 } } }'
    d: Any | None = slpp.decode(data)
    differs(d, slpp.decode(slpp.encode(d)))


def test_unicode() -> None:
    assert slpp.encode("Привет") == '"Привет"'
    assert slpp.encode({"s": "Привет"}) == '{\n\t["s"] = "Привет"\n}'


def test_consistency() -> None:
    def t(data) -> None:
        d: Any | None = slpp.decode(data)
        assert d == slpp.decode(slpp.encode(d))

    t('{ 43, 54.3, false, string = "value", 9, [4] = 111, [1] = 222, [2.1] = "text" }')
    t("{ 43, 54.3, false, 9, [5] = 111, [7] = 222 }")
    t("{ [7] = 111, [5] = 222, 43, 54.3, false, 9 }")
    t("{ 43, 54.3, false, 9, [4] = 111, [5] = 52.1 }")
    t("{ [5] = 111, [4] = 52.1, 43, [3] = 54.3, false, 9 }")
    t('{ [1] = 1, [2] = "2", 3, 4, [5] = 5 }')


def test_comments() -> None:
    def t(data, res) -> None:
        assert slpp.decode(data) == res

    t(
        '-- starting comment\n{\n["multiline_string"] = "A multiline string where one of the lines starts with\n-- two dashes",\n-- middle comment\n["another_multiline_string"] = "A multiline string where one of the lines starts with\n-- two dashes\nfollowed by another line",\n["trailing_comment"] = "A string with" -- a trailing comment\n}\n-- ending comment',
        {
            "multiline_string": "A multiline string where one of the lines starts with\n-- two dashes",
            "another_multiline_string": "A multiline string where one of the lines starts with\n-- two dashes\nfollowed by another line",
            "trailing_comment": "A string with",
        },
    )
    t('"--3"', "--3")
    t(
        '{\n["string"] = "A text\n--[[with\ncomment]]\n",\n--[[\n["comented"] = "string\nnewline",\n]]}',
        {"string": "A text\n--[[with\ncomment]]\n"},
    )
