from big_slpp import slpp


def order_dict(dictionary: dict) -> dict:
    """
    Unordered dict comes in, ordered dict comes out.
    Compatible with dicts that contains keys that are both ints and/or strings.
    """
    # https://stackoverflow.com/a/47882384
    result: dict = {}
    for k, v in sorted(dictionary.items(), key=lambda t: (isinstance(t[0], str), t[0])):
        if isinstance(v, dict):
            result[k] = order_dict(v)
        else:
            result[k] = v
    return result


def wrap(s: str) -> str:
    """
    WoW doesn't save a table as root object, but a variable with a table,
    or even multiple variables, each with a table.

    To make them work in SLPP, we'll need to wrap them in extra
    staches/curly braces.
    """
    return "{" + s + "}"


def unwrap(ordered_dict: dict) -> str:
    """
    Turn the ordered dict into the same style of output that WoW generates.
    Just using slpp.decode() isn't going to cut it.
    """
    result: str = ""
    for k, v in ordered_dict.items():
        result += "\n" + k + " = " + slpp.encode(v)
    return result + "\n"
