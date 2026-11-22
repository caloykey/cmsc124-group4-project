import re
from math import isfinite

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

def to_number(value):
    value_type = value["type"]
    data = value["value"]

    if value_type in {"NUMBR", "NUMBAR"}:
        return make_value(value_type, data)

    if value_type == "TROOF":
        return make_value("NUMBR", int(data))

    if value_type == "YARN":
        if re.fullmatch(r"-?[0-9]+", data):
            return make_value("NUMBR", int(data))

        if re.fullmatch(r"-?[0-9]+\.[0-9]+", data):
            number = float(data)

            if isfinite(number):
                return make_value("NUMBAR", number)

    raise ValueError(f"Cannot implicitly convert {value_type} value {data!r} to a number.")