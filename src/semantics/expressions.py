from .values import make_value


def evaluate_expression(node):
    kind = node["kind"]

    if kind == "literal":
        return make_value(node["type"], node["value"])

    if kind == "binary":
        operator = node["operator"]
        if operator != "SUM OF":
            raise ValueError(f"Unsupported binary operator: {operator}")

        left = evaluate_expression(node["left"])
        right = evaluate_expression(node["right"])

        numeric_types = {"NUMBR", "NUMBAR"}
        if left["type"] not in numeric_types or right["type"] not in numeric_types:
            raise ValueError("SUM OF currently supports NUMBR and NUMBAR operands.")

        result_type = "NUMBAR" if "NUMBAR" in (left["type"], right["type"]) else "NUMBR"
        return make_value(result_type, left["value"] + right["value"])

    raise ValueError(f"Unsupported expression kind: {kind}")