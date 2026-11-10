from .helpers import (
    name_of,
    token_at,
    error_at,
    check_line_end,
)

from .expressions import (
    parse_expression,
    BINARY_OPERATORS,
    VARIADIC_BOOLEAN_OPERATORS,
    TYPE_NAMES,
    LITERAL_TYPES,
)

def parse_declaration(tokens, declared):
    """I HAS A <variable> [ITZ <expression>]"""

    name_token = token_at(tokens, 1)

    if name_token is None or name_token["type"] != "IDENTIFIER":
        return error_at(
            tokens, "Expected a variable name after I HAS A.", name_token
        ), declared

    # The name counts as declared even if the rest of the line has an
    # error, so one mistake does not cause "used before declared" errors
    # further down. It is NOT declared yet while its own ITZ value is checked.
    new_declared = declared | {name_token["lexeme"]}

    following = token_at(tokens, 2)

    if following is None:
        return None, new_declared

    if name_of(following) != "ITZ":
        return error_at(
            tokens,
            f"Expected ITZ or end of line after the variable name, "
            f"found '{following['lexeme']}'.",
            following
        ), new_declared

    position, error = parse_expression(tokens, 3, declared)
    if error:
        return error, new_declared

    return check_line_end(tokens, position), new_declared

def parse_visible(tokens, declared):
    """VISIBLE <expression> [<expression> ...] [!]"""

    position = 1  # skip VISIBLE

    # At least one value
    position, error = parse_expression(tokens, position, declared)
    if error:
        return error, declared

    # More values, until the line ends or a "!" is reached
    while position < len(tokens) and tokens[position]["lexeme"] != "!":
        position, error = parse_expression(tokens, position, declared)
        if error:
            return error, declared

    # Optional "!" must be the last token
    if position < len(tokens):
        position += 1

    return check_line_end(tokens, position), declared

def parse_gimmeh(tokens, declared):
    """GIMMEH <variable>"""

    name_token = token_at(tokens, 1)

    if name_token is None or name_token["type"] != "IDENTIFIER":
        return error_at(
            tokens, "Expected a variable name after GIMMEH.", name_token
        ), declared

    return check_line_end(tokens, 2), declared

def parse_expression_statement(tokens, declared):
    """A lone expression such as SUM OF 1 AN 2 (its result goes to IT)."""

    position, error = parse_expression(tokens, 0, declared)
    if error:
        return error, declared

    return check_line_end(tokens, position), declared

def parse_assignment(tokens, declared):
    """<variable> R <expression>"""

    operator = token_at(tokens, 1)

    if operator is None or name_of(operator) != "R":
        return error_at(
            tokens, "Expected R after the variable name.", operator
        ), declared

    position, error = parse_expression(tokens, 2, declared)
    if error:
        return error, declared

    return check_line_end(tokens, position), declared

# Statement start -> function that checks it. Each one takes
# (tokens, declared) and returns (error_or_None, declared_after).
# To support a new statement, write a parse_ function and add it here.
STATEMENTS = {
    "VISIBLE": parse_visible,
    "I HAS A": parse_declaration,
    "GIMMEH": parse_gimmeh,
}

def parse_recast(tokens, declared):
    """<variable> IS NOW A <type>"""

    type_token = token_at(tokens, 2)

    if (
        type_token is None
        or type_token["type"] != "TYPE_LITERAL"
        or name_of(type_token) not in TYPE_NAMES
    ):
        return error_at(
            tokens,
            "Expected a type after IS NOW A: "
            "NOOB, NUMBR, NUMBAR, YARN, or TROOF.",
            type_token
        ), declared

    return check_line_end(tokens, 3), declared

def check_statement(tokens, declared):
    """Check one line. Returns (error_or_None, declared_after)."""

    first = tokens[0]
    keyword = name_of(first)

    if keyword in STATEMENTS:
        return STATEMENTS[keyword](tokens, declared)

    if (
        first["type"] in LITERAL_TYPES
        or (
            first["type"] == "TYPE_LITERAL"
            and keyword == "NOOB"
        )
    ):
        return parse_expression_statement(tokens, declared)

    if (keyword in BINARY_OPERATORS 
    or keyword in {"NOT","SMOOSH", "MAEK", "I IZ"} 
    or keyword in VARIADIC_BOOLEAN_OPERATORS):
        return parse_expression_statement(tokens, declared)

    if first["type"] == "IDENTIFIER":
        following = token_at(tokens, 1)

        if following is not None:
            if name_of(following) == "IS NOW A":
                return parse_recast(tokens, declared)

            if name_of(following) == "R":
                return parse_assignment(tokens, declared)

        return parse_expression_statement(tokens, declared)

    return error_at(
        tokens,
        f"Unexpected '{first['lexeme']}' at the start of a statement.",
        first
    ), declared
