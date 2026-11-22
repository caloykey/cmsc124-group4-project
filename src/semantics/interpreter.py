from .expressions import evaluate_expression
from .values import make_value


def execute_statement(node, symbols):
    kind = node["kind"]

    if kind == "declaration":
        name = node["name"]

        if name in symbols:
            raise ValueError(f"Variable '{name}' has already been declared.")

        initializer = node.get("initializer")
        value = make_value("NOOB", None)

        if initializer is not None:
            value = evaluate_expression(initializer, symbols)

        symbols[name] = value
        return

    if kind == "assignment":
        name = node["name"]

        if name not in symbols:
            raise ValueError(f"Variable '{name}' has not been declared.")

        value = evaluate_expression(node["value"], symbols)
        symbols[name] = value
        return

    if kind == "expression_statement":
        value = evaluate_expression(node["expression"], symbols)
        symbols["IT"] = value
        return

    raise ValueError(f"Unsupported statement kind: {kind}")

def execute_program(program):
    symbols = {"IT": make_value("NOOB", None)}
    errors = []

    for statement in program["body"]:
        try:
            execute_statement(statement, symbols)
        except ValueError as error:
            errors.append({
                "message": str(error),
                "line": statement.get("line", 1),
                "column": statement.get("column", 1),
            })
            break

    return symbols, errors