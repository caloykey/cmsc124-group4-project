from .values import make_value


def evaluate_expression(node):
    kind = node["kind"]

    if kind == "literal":
        return make_value(node["type"], node["value"])

    if kind == "binary":
        operator = node["operator"]
        supported = {
            "SUM OF",
            "DIFF OF",
            "PRODUKT OF",
            "BIGGR OF",
            "SMALLR OF",
            "QUOSHUNT OF",
        }

        if operator not in supported:
            raise ValueError(f"Unsupported binary operator: {operator}")

        left = evaluate_expression(node["left"])
        right = evaluate_expression(node["right"])

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