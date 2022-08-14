def order_dict(dictionary: dict) -> dict:
    """unordered dict comes in, ordered dict comes out"""
    # https://stackoverflow.com/a/47882384
    result: dict = {}
    for k, v in sorted(dictionary.items(), key=lambda t: (isinstance(t[0], str), t[0])):
        if isinstance(v, dict):
            result[k] = order_dict(v)
        else:
            result[k] = v
    return result
