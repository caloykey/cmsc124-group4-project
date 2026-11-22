from .values import make_value, to_boolean, to_number, to_yarn, cast_value

def evaluate_expression(node, symbols=None):
    if symbols is None:
        symbols = {}

    kind = node["kind"]

    if kind == "literal":
        return make_value(node["type"], node["value"])

    if kind == "variable":
        name = node["name"]

        if name not in symbols:
            raise ValueError(f"Variable '{name}' has not been declared.")

        value = symbols[name]
        return make_value(value["type"], value["value"])   
    
    if kind == "unary":
        operator = node["operator"]

        if operator != "NOT":
            raise ValueError(f"Unsupported unary operator: {operator}")

        operand = evaluate_expression(node["operand"], symbols)
        return make_value("TROOF", not to_boolean(operand))

    if kind == "variadic":
        operator = node["operator"]

        if operator not in {"ALL OF", "ANY OF"}:
            raise ValueError(f"Unsupported variadic operator: {operator}")

        operands = node["operands"]

        if not operands:
            raise ValueError(f"{operator} requires at least one operand.")

        values = [
            to_boolean(evaluate_expression(operand, symbols))
            for operand in operands
        ]

        if operator == "ALL OF":
            result = all(values)
        else:
            result = any(values)

        return make_value("TROOF", result)

    if kind == "smoosh":
        operands = node["operands"]

        if not operands:
            raise ValueError("SMOOSH requires at least one operand.")

        parts = []

        for operand in operands:
            value = evaluate_expression(operand, symbols)
            parts.append(to_yarn(value)["value"])

        return make_value("YARN", "".join(parts))

    if kind == "cast":
        value = evaluate_expression(node["expression"], symbols)
        return cast_value(value, node["target_type"])

    if kind == "binary":
        operator = node["operator"]
        supported = {
            "SUM OF",
            "DIFF OF",
            "PRODUKT OF",
            "BIGGR OF",
            "SMALLR OF",
            "QUOSHUNT OF",
            "MOD OF",
            "BOTH OF",
            "EITHER OF",
            "WON OF",
            "BOTH SAEM",
            "DIFFRINT",
        }

        if operator not in supported:
            raise ValueError(f"Unsupported binary operator: {operator}")

        left = evaluate_expression(node["left"], symbols)
        right = evaluate_expression(node["right"], symbols)

        if operator in {"BOTH SAEM", "DIFFRINT"}:
            equal = (
                left["type"] == right["type"]
                and left["value"] == right["value"]
            )

            result = equal if operator == "BOTH SAEM" else not equal
            return make_value("TROOF", result)

        if operator in {"BOTH OF", "EITHER OF", "WON OF"}:
            left_boolean = to_boolean(left)
            right_boolean = to_boolean(right)

            if operator == "BOTH OF":
                result = left_boolean and right_boolean
            elif operator == "EITHER OF":
                result = left_boolean or right_boolean
            else:
                result = left_boolean != right_boolean

            return make_value("TROOF", result)

        left = to_number(left)
        right = to_number(right)

        left_value = left["value"]
        right_value = right["value"]


        numeric_types = {"NUMBR", "NUMBAR"}

        if left["type"] not in numeric_types or right["type"] not in numeric_types:
            raise ValueError(
                f"{operator} currently supports NUMBR and NUMBAR operands."
            )

        left_value = left["value"]
        right_value = right["value"]

        if operator == "SUM OF":
            result = left_value + right_value
        elif operator == "DIFF OF":
            result = left_value - right_value
        elif operator == "PRODUKT OF":
            result = left_value * right_value
        elif operator == "BIGGR OF":
            result = max(left_value, right_value)
        elif operator == "SMALLR OF":
            result = min(left_value, right_value)
        elif operator == "MOD OF":
            if right_value == 0:
                raise ValueError("Cannot calculate modulo by zero.")
            result = left_value % right_value
        else:
            if right_value == 0:
                raise ValueError("Cannot divide by zero.")

            if left["type"] == "NUMBR" and right["type"] == "NUMBR":
                result = abs(left_value) // abs(right_value)

                if (left_value < 0) != (right_value < 0):
                    result = -result
            else:
                result = left_value / right_value

        result_type = "NUMBR"

        if "NUMBAR" in (left["type"], right["type"]):
            result_type = "NUMBAR"
            result = float(result)

        return make_value(result_type, result)

    raise ValueError(f"Unsupported expression kind: {kind}")