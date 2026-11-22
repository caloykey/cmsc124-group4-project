from .values import make_value


def evaluate_expression(node):
    if node["kind"] == "literal":
        return make_value(node["type"], node["value"])

    raise ValueError(f"Unsupported expression kind: {node['kind']}")