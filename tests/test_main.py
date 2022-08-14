from typing import Any

from big_slpp import slpp
from big_slpp.utils import order_dict, wrap, unwrap
from tests.test_utils import differs
from pathlib import Path

TESTS: Path = Path(__file__).parent


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
    assert slpp.decode(r"{nil}") == {}

    # Values-only table:
    assert slpp.decode('{"10"}') == ["10"]

    # Last zero
    assert slpp.decode("{0, 1, 0}") == [0, 1, 0]

    # Mixed encode
    assert slpp.encode({"0": 0, "name": "john"}) == '{\n\t["0"] = 0,\n\t["name"] = "john",\n}'


def test_string() -> None:
    # Escape test:
    assert slpp.decode(r"'test\'s string'") == "test's string"

    # Add escaping on encode:
    assert slpp.encode({"a": 'func("call()");'}) == '{\n\t["a"] = "func(\\"call()\\");",\n}'

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
    assert slpp.encode({"s": "Привет"}) == '{\n\t["s"] = "Привет",\n}'


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


def test_saved_variables_npcscan_lua() -> None:
    """
    So, for context:

    World of Warcraft saves its addon data as lua files, but since Lua Tables do
    not sort their keys, that makes it hard to keep a clean track of my WoW
    settings, which I turned into a git repo, because sometimes the only changes
    are the keys (and their values) moving around.

    So I made a script that sorts the keys, with the help of SLPP, but it turns
    out that SLPP doesn't write the trailing comma, which I don't like.

    So I 'had' to cleanup the SLPP repo and add the functionality to keep that
    trailing comma.

    Anyway, the filepath the data is coming from is SavedVariabels/_NPCScan.lua,
    hence the name of the test.
    """
    with open(TESTS / "data" / "_NPCScan.lua", encoding="latin-1") as fp:
        input_str = fp.read()
    wrapped_input = wrap(input_str)
    output_dict = slpp.decode(wrapped_input)
    ordered_dict = order_dict(output_dict)
    unwrapped_output = unwrap(ordered_dict)
    with open(TESTS / "data" / "_NPCScan_sorted.lua", encoding="latin-1") as fp:
        expected_output = fp.read()
    assert unwrapped_output == expected_output


def test_saved_variables_npcscan_lua_minimal_example() -> None:
    input: str = """asd = { [2257] = true, [1312] = true, }"""
    wrapped_input = wrap(input)
    output_dict = slpp.decode(wrapped_input)
    ordered_dict = order_dict(output_dict)
    output_str = slpp.encode(ordered_dict)
    assert output_str == """{\n\t["asd"] = {\n\t\t[1312] = true,\n\t\t[2257] = true,\n\t},\n}"""


def test_saved_variables_carbonite_lua() -> None:
    """
    Same as test_saved_variables_npcscan_lua, but with Carbonite.lua.

    This file has escaped double-quotes in the key-names.
    Look for 'Zeppelin Pilot~\"Screaming\" Screed Luckheed', as example
    """
    with open(TESTS / "data" / "Carbonite.lua", encoding="latin-1") as fp:
        input_str = fp.read()
    wrapped_input = wrap(input_str)
    output_dict = slpp.decode(wrapped_input)
    ordered_dict = order_dict(output_dict)
    unwrapped_output = unwrap(ordered_dict)
    with open(TESTS / "data" / "Carbonite_sorted.lua", encoding="latin-1") as fp:
        expected_output = fp.read()
    assert unwrapped_output == expected_output
