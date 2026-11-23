from .helpers import name_of, token_at
from .expressions import BINARY_OPERATORS, VARIADIC_BOOLEAN_OPERATORS
from .syntax import group_by_line, split_body


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def create_node(kind, token, **fields):
    """Make a node. `token` supplies its line and column."""
    return {
        "kind": kind,
        "line": token["line"],
        "column": token["column"],
        **fields
    }


def is_node(value):
    return isinstance(value, dict) and "kind" in value


def format_ast(node, indent=0, label=None):
    """Return the tree as indented text, for debugging or display."""

    pad = "|" + "-" * indent
    prefix = f"{pad}{label}: " if label else pad

    if isinstance(node, list):
        lines = [f"{pad}{label}:"] if label else []
        child_indent = indent + 1 if label else indent
        lines.extend(format_ast(item, child_indent) for item in node)
        return "\n".join(lines)

    inline = []
    children = []

    for key, value in node.items():
        if key in {"kind", "line", "column"}:
            continue

        is_tree = is_node(value) or (
            isinstance(value, list) and value and all(map(is_node, value))
        )

        if is_tree:
            children.append((key, value))
        else:
            inline.append(f"{key}={value!r}")

    header = f"{prefix}{node['kind']} @{node['line']}:{node['column']}"
    if inline:
        header += " " + " ".join(inline)

    lines = [header]
    lines.extend(
        format_ast(value, indent + 1, key) for key, value in children
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Expressions
#
# Every build_ function takes the tokens of ONE line and the position of the
# next token, and returns (node, new_position).
# ---------------------------------------------------------------------------

def build_literal(token):
    kind = token["type"]
    text = token["lexeme"]

    if kind == "NUMBR":
        value = int(text)
    elif kind == "NUMBAR":
        value = float(text)
    elif kind == "YARN":
        value = text[1:-1]
    elif kind == "TROOF":
        value = text.upper() == "WIN"
    else:  # NOOB is lexed as a TYPE_LITERAL
        kind = "NOOB"
        value = None

    return create_node("literal", token, type=kind, value=value, raw=text)


def build_type_name(token):
    return name_of(token).upper()


def skip_if(tokens, position, keyword):
    """Skip one token if it is `keyword`. Returns the new position."""
    token = token_at(tokens, position)

    if token is not None and name_of(token) == keyword:
        return position + 1

    return position


def build_operands(tokens, position):
    """Read `operand (AN operand)*`. Returns (operands, new_position)."""

    operand, position = build_expression(tokens, position)
    operands = [operand]

    while True:
        following = token_at(tokens, position)

        if following is None or name_of(following) != "AN":
            return operands, position

        operand, position = build_expression(tokens, position + 1)
        operands.append(operand)


def build_arguments(tokens, position):
    """Read `[YR expr [AN YR expr]...]` of a function call."""

    following = token_at(tokens, position)

    if following is None or name_of(following) != "YR":
        return [], position

    arguments = []
    position += 1

    while True:
        argument, position = build_expression(tokens, position)
        arguments.append(argument)

        following = token_at(tokens, position)

        if following is None or name_of(following) != "AN":
            return arguments, position

        position += 2  # skip AN YR


def build_expression(tokens, position):
    """Build one expression. Returns (node, new_position)."""

    token = token_at(tokens, position)

    if token is None:
        raise ValueError("build_ast: expected an expression.")

    name = name_of(token)
    position += 1

    # Literals: 12, 3.14, "text", WIN, FAIL, NOOB
    if token["type"] in {"NUMBR", "NUMBAR", "YARN", "TROOF"}:
        return build_literal(token), position

    if token["type"] == "TYPE_LITERAL" and name.upper() == "NOOB":
        return build_literal(token), position

    if token["type"] == "IDENTIFIER":
        return create_node("variable", token, name=token["lexeme"]), position

    if name == "NOT":
        operand, position = build_expression(tokens, position)
        return create_node(
            "unary", token, operator=name, operand=operand
        ), position

    if name in VARIADIC_BOOLEAN_OPERATORS:
        operands, position = build_operands(tokens, position)
        position = skip_if(tokens, position, "MKAY")
        return create_node(
            "variadic", token, operator=name, operands=operands
        ), position

    if name == "SMOOSH":
        operands, position = build_operands(tokens, position)
        position = skip_if(tokens, position, "MKAY")  # optional
        return create_node("smoosh", token, operands=operands), position

    if name == "MAEK":
        expression, position = build_expression(tokens, position)
        position = skip_if(tokens, position, "A")  # optional
        type_token = token_at(tokens, position)
        return create_node(
            "cast", token,
            expression=expression,
            target_type=build_type_name(type_token)
        ), position + 1

    if name == "I IZ":
        function_token = token_at(tokens, position)
        arguments, position = build_arguments(tokens, position + 1)
        position = skip_if(tokens, position, "MKAY")
        return create_node(
            "call", token,
            name=function_token["lexeme"],
            arguments=arguments
        ), position

    if name in BINARY_OPERATORS:
        left, position = build_expression(tokens, position)
        position += 1  # skip AN
        right, position = build_expression(tokens, position)
        return create_node(
            "binary", token, operator=name, left=left, right=right
        ), position

    raise ValueError(
        f"build_ast: unexpected '{token['lexeme']}' "
        f"at line {token['line']}, column {token['column']}."
    )


# ---------------------------------------------------------------------------
# Simple statements (one line each)
# ---------------------------------------------------------------------------

def build_visible(tokens):
    # VISIBLE <expression> [+ <expression> ...] [!]
    first, position = build_expression(tokens, 1)
    values = [first]

    while skip_if(tokens, position, "+") != position:
        value, position = build_expression(tokens, position + 1)
        values.append(value)

    newline = skip_if(tokens, position, "!") == position

    return create_node("visible", tokens[0], values=values, newline=newline)


def build_declaration(tokens):
    # I HAS A <variable> [ITZ <expression>]
    initializer = None

    if token_at(tokens, 2) is not None:
        initializer, _ = build_expression(tokens, 3)

    return create_node(
        "declaration", tokens[0],
        name=tokens[1]["lexeme"],
        initializer=initializer
    )


def build_input(tokens):
    return create_node("input", tokens[0], name=tokens[1]["lexeme"])


def build_assignment(tokens):
    # <variable> R <expression>
    value, _ = build_expression(tokens, 2)

    return create_node(
        "assignment", tokens[0], name=tokens[0]["lexeme"], value=value
    )


def build_recast(tokens):
    # <variable> IS NOW A <type>
    return create_node(
        "recast", tokens[0],
        name=tokens[0]["lexeme"],
        target_type=build_type_name(tokens[2])
    )


def build_return(tokens):
    expression, _ = build_expression(tokens, 1)
    return create_node("return", tokens[0], expression=expression)


def build_break(tokens):
    return create_node("break", tokens[0])


def build_expression_statement(tokens):
    expression, _ = build_expression(tokens, 0)
    return create_node("expression_statement", tokens[0], expression=expression)


SIMPLE_STATEMENTS = {
    "VISIBLE": build_visible,
    "I HAS A": build_declaration,
    "GIMMEH": build_input,
    "FOUND YR": build_return,
    "GTFO": build_break,
}


def build_simple_statement(tokens):
    first = tokens[0]
    keyword = name_of(first)

    if keyword in SIMPLE_STATEMENTS:
        return SIMPLE_STATEMENTS[keyword](tokens)

    if first["type"] == "IDENTIFIER":
        following = token_at(tokens, 1)

        if following is not None and name_of(following) == "R":
            return build_assignment(tokens)

        if following is not None and name_of(following) == "IS NOW A":
            return build_recast(tokens)

    return build_expression_statement(tokens)


# ---------------------------------------------------------------------------
# Blocks (span several lines)
#
# These take `lines` (a list of token lists, one per source line) and the
# `index` of the line to start at, and return (node, next_index).
# ---------------------------------------------------------------------------

def build_body(lines, index, stoppers):
    """
    Build statements until a line starting with one of `stoppers`.
    Returns (statements, index_of_the_stopping_line).
    """

    statements = []

    while index < len(lines) and name_of(lines[index][0]) not in stoppers:
        statement, index = build_statement(lines, index)
        statements.append(statement)

    return statements, index


def build_if(lines, index):
    # O RLY? / YA RLY / [MEBBE <expr>]... / [NO WAI] / OIC
    opener = lines[index][0]
    stoppers = {"MEBBE", "NO WAI", "OIC"}

    then_body, index = build_body(lines, index + 2, stoppers)  # skip YA RLY
    elif_branches = []
    else_body = []

    while index < len(lines):
        line = lines[index]
        keyword = name_of(line[0])

        if keyword == "MEBBE":
            condition, _ = build_expression(line, 1)
            body, index = build_body(lines, index + 1, stoppers)
            elif_branches.append(create_node(
                "elif_branch", line[0], condition=condition, body=body
            ))

        elif keyword == "NO WAI":
            else_body, index = build_body(lines, index + 1, {"OIC"})

        else:  # OIC
            break

    return create_node(
        "if", opener,
        then_body=then_body,
        elif_branches=elif_branches,
        else_body=else_body
    ), index + 1  # skip OIC


def build_switch(lines, index):
    # WTF? / OMG <literal> ... / [OMGWTF ...] / OIC
    opener = lines[index][0]
    stoppers = {"OMG", "OMGWTF", "OIC"}

    index += 1
    cases = []
    default_body = []

    while index < len(lines):
        line = lines[index]
        keyword = name_of(line[0])

        if keyword == "OMG":
            body, index = build_body(lines, index + 1, stoppers)
            cases.append(create_node(
                "case", line[0], value=build_literal(line[1]), body=body
            ))

        elif keyword == "OMGWTF":
            default_body, index = build_body(lines, index + 1, {"OIC"})

        else:  # OIC
            break

    return create_node(
        "switch", opener, cases=cases, default_body=default_body
    ), index + 1  # skip OIC


def build_loop(lines, index):
    # IM IN YR <label> UPPIN|NERFIN YR <var> [TIL|WILE <expr>] ... IM OUTTA YR <label>
    header = lines[index]

    mode = None
    condition = None

    if token_at(header, 5) is not None:
        mode = name_of(header[5])
        condition, _ = build_expression(header, 6)

    body, index = build_body(lines, index + 1, {"IM OUTTA YR"})

    return create_node(
        "loop", header[0],
        label=header[1]["lexeme"],
        operation=name_of(header[2]),
        variable=header[4]["lexeme"],
        mode=mode,
        condition=condition,
        body=body
    ), index + 1  # skip IM OUTTA YR


def build_function(lines, index):
    # HOW IZ I <name> [YR <param> [AN YR <param>]...] ... IF U SAY SO
    header = lines[index]
    parameters = []

    if token_at(header, 2) is not None:
        position = 3  # first parameter, after YR

        while True:
            parameters.append(header[position]["lexeme"])

            if token_at(header, position + 1) is None:
                break

            position += 3  # skip the parameter, AN and YR

    body, index = build_body(lines, index + 1, {"IF U SAY SO"})

    return create_node(
        "function", header[0],
        name=header[1]["lexeme"],
        parameters=parameters,
        body=body
    ), index + 1  # skip IF U SAY SO


# Statement start -> function that builds the whole block.
BLOCK_STATEMENTS = {
    "O RLY?": build_if,
    "WTF?": build_switch,
    "IM IN YR": build_loop,
    "HOW IZ I": build_function,
}


def build_statement(lines, index):
    """Build the statement (or block) starting at lines[index]."""

    line = lines[index]
    keyword = name_of(line[0])

    if keyword in BLOCK_STATEMENTS:
        return BLOCK_STATEMENTS[keyword](lines, index)

    return build_simple_statement(line), index + 1


# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------

def build_functions(tokens):
    """Build the function definitions in a stretch outside HAI/KTHXBYE."""

    lines = group_by_line(tokens)
    functions = []
    index = 0

    while index < len(lines):
        function, index = build_function(lines, index)
        functions.append(function)

    return functions


def build_declarations(lines):
    """
    Build the WAZZUP ... BUHBYE block, if there is one.
    Returns (declarations, index_of_the_first_line_after_it).
    """

    if not lines or name_of(lines[0][0]) != "WAZZUP":
        return [], 0

    declarations = []
    index = 1

    while index < len(lines) and name_of(lines[index][0]) != "BUHBYE":
        declarations.append(build_declaration(lines[index]))
        index += 1

    return declarations, index + 1  # skip BUHBYE


def build_ast(tokens):
    """
    Turn a token list into a program node.
    Call this only after check_syntax(tokens) returned no errors.
    """

    hai_index = next(
        i for i, token in enumerate(tokens) if token["lexeme"] == "HAI"
    )
    end_index = next(
        i for i in range(hai_index + 1, len(tokens))
        if tokens[i]["lexeme"] == "KTHXBYE"
    )

    hai_token = tokens[hai_index]
    version_token = token_at(tokens, hai_index + 1)
    version = None

    if (
        version_token is not None
        and version_token["line"] == hai_token["line"]
        and version_token["type"] == "NUMBAR"
    ):
        version = version_token["lexeme"]

    # The main program: everything between HAI and KTHXBYE.
    main_lines = group_by_line(
        split_body(tokens[hai_index:end_index + 1])
    )

    declarations, index = build_declarations(main_lines)
    statements, _ = build_body(main_lines, index, set())

    # Functions can sit before HAI, inside the program, or after KTHXBYE.
    # They are collected into one list, in source order.
    inner_functions = [
        node for node in statements if node["kind"] == "function"
    ]
    statements = [
        node for node in statements if node["kind"] != "function"
    ]

    functions = (
        build_functions(tokens[:hai_index])
        + inner_functions
        + build_functions(tokens[end_index + 1:])
    )

    return create_node(
        "program", hai_token,
        version=version,
        body=declarations + statements,   # declarations run first
        functions=functions
    )