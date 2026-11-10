from errors import create_error
from .helpers import name_of, error_at, check_line_end
from .statements import check_statement
from .blocks import check_block_line


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
    else:
        header = []

        for token in tokens:
            if token["line"] != first["line"]:
                break
            header.append(token)

        position = 1

        # Optional version number after HAI.
        if (
            position < len(header)
            and header[position]["type"] == "NUMBAR"
            and not header[position]["lexeme"].startswith("-")
        ):
            position += 1

        error = check_line_end(header, position)

        if error:
            errors.append(error)

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
    errors = []
    block_stack = []
    declared = frozenset()
    inside_declarations = False
    declaration_block_seen = False
    opening_token = None

    for line_tokens in group_by_line(split_body(tokens)):
        first = line_tokens[0]
        keyword = name_of(first)

        if keyword == "HAI":
            continue

        if keyword == "WAZZUP":

            if block_stack:
                errors.append(error_at(
                    line_tokens,
                    "WAZZUP cannot appear inside a control-flow block.",
                    first
                ))
                continue

            if inside_declarations:
                errors.append(error_at(
                    line_tokens, "Nested WAZZUP is not allowed.", first
                ))
            elif declaration_block_seen:
                errors.append(error_at(
                    line_tokens, "Only one declaration block is allowed.", first
                ))
            else:
                inside_declarations = True
                declaration_block_seen = True
                opening_token = first

            error = check_line_end(line_tokens, 1)
            if error:
                errors.append(error)
            continue

        if keyword == "BUHBYE":
            if not inside_declarations:
                errors.append(error_at(
                    line_tokens, "BUHBYE found without WAZZUP.", first
                ))
            else:
                inside_declarations = False

            error = check_line_end(line_tokens, 1)
            if error:
                errors.append(error)
            continue

        if keyword == "I HAS A" and not inside_declarations:
            errors.append(error_at(
                line_tokens,
                "Variable declarations must be inside WAZZUP ... BUHBYE.",
                first
            ))
            continue

        if inside_declarations and keyword != "I HAS A":
            errors.append(error_at(
                line_tokens,
                "Only variable declarations are allowed before BUHBYE.",
                first
            ))
            continue

        handled, error = check_block_line(
            line_tokens, declared, block_stack
        )

        if handled:
            if error:
                errors.append(error)
            continue

        error, declared = check_statement(line_tokens, declared)

        if error:
            errors.append(error)

    if inside_declarations:
        errors.append(create_error(
            "Missing BUHBYE to close the declaration block.",
            opening_token["line"],
            opening_token["column"]
        ))

    for block in reversed(block_stack):
        opening = block["token"]

        if block["kind"] == "loop":
            message = (
                f"Missing IM OUTTA YR {block['label']} "
                "to close the loop."
            )

        elif block["kind"] == "function":
            message = (
                f"Missing IF U SAY SO to close "
                f"function '{block['name']}'."
            )
        
        else:
            message = (
                f"Missing OIC to close the {block['kind']} block."
            )

        errors.append(create_error(
            message,
            opening["line"],
            opening["column"]
        ))

    return errors
