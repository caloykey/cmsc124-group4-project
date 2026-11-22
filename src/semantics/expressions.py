from .values import make_value


def evaluate_expression(node):
    kind = node["kind"]

    if kind == "literal":
        return make_value(node["type"], node["value"])

    if kind == "binary":
        operator = node["operator"]
        if operator not in {"SUM OF", "DIFF OF"}:
            raise ValueError(f"Unsupported binary operator: {operator}")

        left = evaluate_expression(node["left"])
        right = evaluate_expression(node["right"])

        numeric_types = {"NUMBR", "NUMBAR"}
        if left["type"] not in numeric_types or right["type"] not in numeric_types:
            raise ValueError(f"{operator} currently supports NUMBR and NUMBAR operands.")

        if operator == "SUM OF":
            result = left["value"] + right["value"]
        else:
            result = left["value"] - right["value"]

        result_type = "NUMBAR" if "NUMBAR" in (left["type"], right["type"]) else "NUMBR"
        return make_value(result_type, result)

    raise ValueError(f"Unsupported expression kind: {kind}")