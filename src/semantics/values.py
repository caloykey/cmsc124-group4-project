import re
from math import isfinite
from decimal import Decimal


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


def to_yarn(value):
    value_type = value["type"]
    data = value["value"]

    if value_type == "YARN":
        text = data
    elif value_type == "TROOF":
        text = "WIN" if data else "FAIL"
    elif value_type == "NUMBR":
        text = str(data)
    elif value_type == "NUMBAR":
        if not isfinite(data):
            raise ValueError("Cannot convert a non-finite NUMBAR to YARN.")

        text = format(Decimal(str(data)), "f")
        whole, separator, fraction = text.partition(".")

        if separator:
            text = whole + "." + fraction[:2]
    else:
        raise ValueError(f"Cannot implicitly convert {value_type} to YARN.")

    return make_value("YARN", text)


def cast_value(value, target_type):
    supported = {"NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"}

    if target_type not in supported:
        raise ValueError(f"Unknown type: {target_type}")

    if target_type == "NOOB":
        return make_value("NOOB", None)

    if target_type == "TROOF":
        return make_value("TROOF", to_boolean(value))

    if value["type"] == "NOOB":
        defaults = {
            "NUMBR": 0,
            "NUMBAR": 0.0,
            "YARN": "",
        }
        return make_value(target_type, defaults[target_type])

    if target_type == "YARN":
        return to_yarn(value)

    number = to_number(value)["value"]

    try:
        if target_type == "NUMBR":
            return make_value("NUMBR", int(number))

        number = float(number)
    except (ValueError, OverflowError) as error:
        raise ValueError(f"Cannot convert this value to {target_type}.") from error

    if not isfinite(number):
        raise ValueError("Cannot convert this value to a finite NUMBAR.")

    return make_value("NUMBAR", number)