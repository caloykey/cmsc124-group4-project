from .expressions import evaluate_expression
from .values import make_value, to_boolean


def execute_statement(node, symbols, write_output=None):
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

    if kind == "visible":
        if write_output is None:
            raise ValueError("VISIBLE requires an output callback.")

        parts = []

        for expression in node["values"]:
            value = evaluate_expression(expression, symbols)
            value_type = value["type"]

            if value_type == "TROOF":
                text = "WIN" if value["value"] else "FAIL"
            elif value_type in {"NUMBR", "NUMBAR", "YARN"}:
                text = str(value["value"])
            else:
                raise ValueError(f"Cannot display a {value_type} value.")

            parts.append(text)

        output = "".join(parts)

        if node.get("newline", True):
            output += "\n"

        write_output(output)
        return

    if kind == "if":
        selected_body = node.get("else_body", [])

        if to_boolean(symbols["IT"]):
            selected_body = node["then_body"]
        else:
            for branch in node.get("elif_branches", []):
                condition = evaluate_expression(branch["condition"], symbols)

                if to_boolean(condition):
                    selected_body = branch["body"]
                    break

        for statement in selected_body:
            execute_statement(statement, symbols, write_output)

        return

    raise ValueError(f"Unsupported statement kind: {kind}")

def execute_program(program, write_output=None):
    symbols = {"IT": make_value("NOOB", None)}
    errors = []

    for statement in program["body"]:
        try:
            execute_statement(statement, symbols, write_output)
        except ValueError as error:
            errors.append({
                "message": str(error),
                "line": statement.get("line", 1),
                "column": statement.get("column", 1),
            })
            break

    return symbols, errors