def make_value(value_type, value):
    return {"type": value_type, "value": value}


def to_boolean(value):
    value_type = value["type"]
    data = value["value"]

    if value_type == "NOOB":
        return False

    if value_type == "TROOF":
        return data

    if value_type in {"NUMBR", "NUMBAR"}:
        return data != 0

    if value_type == "YARN":
        return data != ""

    raise ValueError(f"Cannot convert {value_type} to TROOF.")