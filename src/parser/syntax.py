from lexer.errors import create_error


def check_syntax(tokens):
    """
    Check the syntax of a token list.

    Returns a list of error dictionaries (empty if the syntax is valid).
    Each rule is added as its own check function so we can grow this
    one keyword at a time.
    """

    errors = []

    # Step 1: HAI ... KTHXBYE
    errors.extend(check_program_structure(tokens))

    # Step 2: statements between HAI and KTHXBYE
    # (VISIBLE, I HAS A, GIMMEH, arithmetic)
    errors.extend(check_statements(tokens))

    return errors


def check_program_structure(tokens):
    """A program must be: HAI [version] <body> KTHXBYE"""

    errors = []

    # Nothing to check against (blank or comment-only source)
    if not tokens:
        errors.append(
            create_error("Empty program: expected HAI.", 1, 1)
        )
        return errors

    # ---- HAI ----
    first = tokens[0]

    if first["lexeme"] != "HAI":
        errors.append(
            create_error(
                f"Program must start with HAI, found '{first['lexeme']}'.",
                first["line"],
                first["column"]
            )
        )
    elif len(tokens) > 1:
        # HAI may be followed by a version number (HAI 1.2),
        # but nothing else on the same line.
        following = tokens[1]
        on_same_line = following["line"] == first["line"]
        is_version = following["type"] == "NUMBAR"
        is_end = following["lexeme"] == "KTHXBYE"  # reported below

        if on_same_line and not is_version and not is_end:
            errors.append(
                create_error(
                    "HAI must be alone on its line "
                    "(only a version number may follow it).",
                    following["line"],
                    following["column"]
                )
            )

    # Any other HAI later in the program is a mistake
    for token in tokens[1:]:
        if token["lexeme"] == "HAI":
            errors.append(
                create_error(
                    "Unexpected HAI: it can only appear once, "
                    "at the start of the program.",
                    token["line"],
                    token["column"]
                )
            )

    # ---- KTHXBYE ----
    end_indexes = [
        index for index, token in enumerate(tokens)
        if token["lexeme"] == "KTHXBYE"
    ]

    if not end_indexes:
        last = tokens[-1]
        errors.append(
            create_error(
                "Missing KTHXBYE at the end of the program.",
                last["line"],
                last["column"] + len(last["lexeme"])
            )
        )
        return errors

    end_index = end_indexes[0]
    end_token = tokens[end_index]

    # KTHXBYE must be alone on its line
    if end_index > 0 and tokens[end_index - 1]["line"] == end_token["line"]:
        errors.append(
            create_error(
                "KTHXBYE must be alone on its line.",
                end_token["line"],
                end_token["column"]
            )
        )

    # Nothing is allowed after the first KTHXBYE
    if end_index < len(tokens) - 1:
        extra = tokens[end_index + 1]
        errors.append(
            create_error(
                "Unexpected code after KTHXBYE.",
                extra["line"],
                extra["column"]
            )
        )

    return errors


# ---------------------------------------------------------------------------
# Statements: VISIBLE, I HAS A, GIMMEH and arithmetic expressions
#
# Every parse_ function is a plain function that takes
#     tokens    - the tokens of ONE line (one statement)
#     position  - index of the next token to read
#     declared  - set of variable names declared so far (never modified)
# and returns a pair:
#     (new_position, error)      error is None when everything is fine
# ---------------------------------------------------------------------------

ARITHMETIC_OPERATORS = {
    "SUM OF",
    "DIFF OF",
    "PRODUKT OF",
    "QUOSHUNT OF",
    "MOD OF",
    "BIGGR OF",
    "SMALLR OF",
}

LITERAL_TYPES = {"NUMBR", "NUMBAR", "YARN", "TROOF"}


def name_of(token):
    """Lexeme with extra spaces between words removed ('I   HAS A' -> 'I HAS A')."""
    return " ".join(token["lexeme"].split())


def token_at(tokens, position):
    """The token at `position`, or None if the line has ended."""
    if position < len(tokens):
        return tokens[position]
    return None


def error_at(tokens, message, token=None):
    """Make an error pointing at `token`, or just past the end of the line."""
    if token is not None:
        return create_error(message, token["line"], token["column"])

    last = tokens[-1]
    return create_error(
        message,
        last["line"],
        last["column"] + len(last["lexeme"])
    )


def check_line_end(tokens, position):
    """Error if there are leftover tokens on the line."""
    token = token_at(tokens, position)

    if token is not None:
        return error_at(tokens, f"Unexpected '{token['lexeme']}'.", token)

    return None


def parse_expression(tokens, position, declared):
    """
    expression := NUMBR | NUMBAR | YARN | TROOF | variable
                | <arithmetic operator> expression AN expression
    """

    token = token_at(tokens, position)

    if token is None:
        return position, error_at(
            tokens, "Expected a value, variable, or expression."
        )

    position += 1

    # Literals: 12, 3.14, "text", WIN, FAIL
    if token["type"] in LITERAL_TYPES:
        return position, None

    # Variables must be declared with I HAS A first
    if token["type"] == "IDENTIFIER":
        if token["lexeme"] not in declared:
            return position, error_at(
                tokens,
                f"Variable '{token['lexeme']}' is used before it is "
                "declared (use I HAS A).",
                token
            )
        return position, None

    # SUM OF x AN y  (operands can be nested expressions)
    if name_of(token) in ARITHMETIC_OPERATORS:
        operator = name_of(token)

        position, error = parse_expression(tokens, position, declared)
        if error:
            return position, error

        separator = token_at(tokens, position)
        if separator is None or name_of(separator) != "AN":
            return position, error_at(
                tokens,
                f"Expected AN between the operands of {operator}.",
                separator
            )
        position += 1

        return parse_expression(tokens, position, declared)

    return position, error_at(
        tokens,
        f"Expected a value, variable, or expression, "
        f"found '{token['lexeme']}'.",
        token
    )


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


def parse_gimmeh(tokens, declared):
    """GIMMEH <variable>"""

    name_token = token_at(tokens, 1)

    if name_token is None or name_token["type"] != "IDENTIFIER":
        return error_at(
            tokens, "Expected a variable name after GIMMEH.", name_token
        ), declared

    if name_token["lexeme"] not in declared:
        return error_at(
            tokens,
            f"Variable '{name_token['lexeme']}' is used before it is "
            "declared (use I HAS A).",
            name_token
        ), declared

    return check_line_end(tokens, 2), declared


def parse_expression_statement(tokens, declared):
    """A lone expression such as SUM OF 1 AN 2 (its result goes to IT)."""

    position, error = parse_expression(tokens, 0, declared)
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


def check_statement(tokens, declared):
    """Check one line. Returns (error_or_None, declared_after)."""

    first = tokens[0]
    keyword = name_of(first)

    if keyword in STATEMENTS:
        return STATEMENTS[keyword](tokens, declared)

    if keyword in ARITHMETIC_OPERATORS:
        return parse_expression_statement(tokens, declared)

    return error_at(
        tokens,
        f"Unexpected '{first['lexeme']}' at the start of a statement.",
        first
    ), declared


def split_body(tokens):
    """Return the tokens between HAI and KTHXBYE."""

    start = 0

    # Skip the HAI line (including an optional version number)
    if tokens and name_of(tokens[0]) == "HAI":
        hai_line = tokens[0]["line"]
        start = 1
        while start < len(tokens) and tokens[start]["line"] == hai_line:
            start += 1

    end = len(tokens)
    for index in range(start, len(tokens)):
        if name_of(tokens[index]) == "KTHXBYE":
            end = index
            break

    return tokens[start:end]


def group_by_line(tokens):
    """Group tokens so each inner list is one line of source code."""

    lines = []

    for token in tokens:
        if lines and lines[-1][0]["line"] == token["line"]:
            lines[-1].append(token)
        else:
            lines.append([token])

    return lines


def check_statements(tokens):
    """Check every statement between HAI and KTHXBYE, one per line."""

    errors = []
    declared = frozenset()

    for line_tokens in group_by_line(split_body(tokens)):
        # A repeated HAI is already reported by check_program_structure
        if name_of(line_tokens[0]) == "HAI":
            continue

        error, declared = check_statement(line_tokens, declared)

        if error:
            errors.append(error)

    return errors
