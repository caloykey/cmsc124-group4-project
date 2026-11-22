from .expressions import evaluate_expression
from .values import make_value, to_boolean, to_yarn, cast_value, to_number

def execute_statement(node, symbols, write_output=None, read_input=None):
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
            parts.append(to_yarn(value)["value"])

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
            signal = execute_statement(statement, symbols, write_output, read_input)

            if signal == "break":
                return signal

        return

    if kind == "break":
        return "break"

    if kind == "switch":
        target = symbols["IT"]
        matched = False

        for case in node["cases"]:
            if not matched:
                case_value = evaluate_expression(case["value"], symbols)
                matched = (
                    target["type"] == case_value["type"]
                    and target["value"] == case_value["value"]
                )

            if matched:
                for statement in case["body"]:
                    signal = execute_statement(statement, symbols, write_output, read_input)

                    if signal == "break":
                        return

        for statement in node.get("default_body", []):
            signal = execute_statement(statement, symbols, write_output, read_input)

            if signal == "break":
                return

        return

    if kind == "loop":
        name = node["variable"]
        operation = node["operation"]
        mode = node.get("mode")

        if name not in symbols:
            raise ValueError(f"Variable '{name}' has not been declared.")

        if operation not in {"UPPIN", "NERFIN"}:
            raise ValueError(f"Unsupported loop operation: {operation}")

        if mode not in {None, "TIL", "WILE"}:
            raise ValueError(f"Unsupported loop condition: {mode}")

        symbols[name] = to_number(symbols[name])

        step = 1 if operation == "UPPIN" else -1

        while True:
            if mode is not None:
                condition = evaluate_expression(node["condition"], symbols)
                condition_true = to_boolean(condition)

                if mode == "TIL" and condition_true:
                    break

                if mode == "WILE" and not condition_true:
                    break

            for statement in node["body"]:
                signal = execute_statement(statement, symbols, write_output, read_input)

                if signal == "break":
                    return

            value = to_number(symbols[name])

            symbols[name] = make_value(
                value["type"],
                value["value"] + step,
            )

        return

    if kind == "input":
        name = node["name"]

        if name not in symbols:
            raise ValueError(f"Variable '{name}' has not been declared.")

        if read_input is None:
            raise ValueError("GIMMEH requires an input callback.")

        text = read_input(name)

        if text is None:
            raise ValueError("Input cancelled.")

        symbols[name] = make_value("YARN", text)
        return

    if kind == "recast":
        name = node["name"]

        if name not in symbols:
            raise ValueError(f"Variable '{name}' has not been declared.")

        value = cast_value(symbols[name], node["target_type"])
        symbols[name] = value
        return

    raise ValueError(f"Unsupported statement kind: {kind}")


def register_functions(program):
    functions = {}

    definitions = list(program.get("functions", []))
    definitions.extend(
        statement
        for statement in program["body"]
        if statement["kind"] == "function"
    )

    for definition in definitions:
        name = definition["name"]
        parameters = definition["parameters"]

        if name in functions:
            raise ValueError(f"Function '{name}' has already been defined.")

        if len(parameters) != len(set(parameters)):
            raise ValueError(f"Function '{name}' has duplicate parameters.")

        functions[name] = definition

    return functions


def execute_program(program, write_output=None, read_input=None):
    symbols = {"IT": make_value("NOOB", None)}
    errors = []

    for statement in program["body"]:
        try:
            signal = execute_statement(statement, symbols, write_output, read_input)
            if signal == "break":
                raise ValueError("GTFO requires an enclosing switch, loop, or function.")
        except ValueError as error:
            errors.append({
                "message": str(error),
                "line": statement.get("line", 1),
                "column": statement.get("column", 1),
            })
            break

    return symbols, errors