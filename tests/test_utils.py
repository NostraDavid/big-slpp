import pytest
from big_slpp.utils import order_dict


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


def test_order_dict_normal_use() -> None:
    """
    Insert a dict with unsorted keys, get a dict with sorted keys out.
    """
    input: dict[str, str] = {
        "3": "a",
        "2": "b",
        "1": "c",
    }
    output = order_dict(input)
    assert list(input.keys()) == ["3", "2", "1"]
    assert list(output.keys()) != list(input.keys())
    assert list(output.keys()) == ["1", "2", "3"]


def test_order_dict_with_int_and_str_keys() -> None:
    """
    Insert a dict with ints and strs as keys, get a dict back that
    has ints first, strs second, fully ordered"""
    input: dict[int | str, str] = {
        3: "a",
        "c": "b",
        "b": "c",
        2: "d",
        "a": "e",
        1: "f",
    }
    output = order_dict(input)
    assert list(input.keys()) == [3, 'c', 'b', 2, 'a', 1]
    assert list(output.keys()) != list(input.keys())
    assert list(output.keys()) == [1, 2, 3, 'a', 'b', 'c']
