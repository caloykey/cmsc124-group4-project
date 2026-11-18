from errors import create_error
from .helpers import name_of, error_at, check_line_end
from .statements import check_statement
from .blocks import check_block_line


def check_syntax(tokens):
    errors = check_program_structure(tokens)

    hai_index = next(
        (i for i, token in enumerate(tokens)
         if token["lexeme"] == "HAI"),
        None
    )

    if hai_index is None:
        return errors

    end_index = next(
        (i for i in range(hai_index + 1, len(tokens))
         if tokens[i]["lexeme"] == "KTHXBYE"),
        None
    )

    if end_index is None:
        return errors

    # Functions before HAI.
    errors.extend(check_external_functions(tokens[:hai_index]))

    # Main program.
    errors.extend(
        check_statements(tokens[hai_index:end_index + 1])
    )

    # Functions after KTHXBYE.
    errors.extend(
        check_external_functions(tokens[end_index + 1:])
    )

    return errors


def check_program_structure(tokens):
    errors = []

    if not tokens:
        return [create_error("Empty program: expected HAI.", 1, 1)]

    hai_indexes = [
        i for i, token in enumerate(tokens)
        if token["lexeme"] == "HAI"
    ]

    if not hai_indexes:
        errors.append(error_at(
            tokens, "Missing HAI.", tokens[0]
        ))
        return errors

    hai_index = hai_indexes[0]
    hai_token = tokens[hai_index]

    # Check HAI and its optional version number.
    header = [
        token for token in tokens[hai_index:]
        if token["line"] == hai_token["line"]
    ]

    position = 1

    if (
        position < len(header)
        and header[position]["type"] == "NUMBAR"
        and not header[position]["lexeme"].startswith("-")
    ):
        position += 1

    error = check_line_end(header, position)
    if error:
        errors.append(error)

    # Only one HAI is allowed.
    for index in hai_indexes[1:]:
        errors.append(error_at(
            tokens,
            "Unexpected HAI: only one program is allowed.",
            tokens[index]
        ))

    # Find the closing KTHXBYE after HAI.
    end_indexes = [
        i for i, token in enumerate(tokens)
        if token["lexeme"] == "KTHXBYE"
        and i > hai_index
    ]

    if not end_indexes:
        errors.append(error_at(
            tokens, "Missing KTHXBYE at the end of the program."
        ))
        return errors

    end_index = end_indexes[0]
    end_token = tokens[end_index]

    if (
        end_index > 0
        and tokens[end_index - 1]["line"] == end_token["line"]
    ):
        errors.append(error_at(
            tokens,
            "KTHXBYE must be alone on its line.",
            end_token
        ))

    # An additional program delimiter is invalid.
    for index in end_indexes[1:]:
        errors.append(error_at(
            tokens,
            "Unexpected additional KTHXBYE.",
            tokens[index]
        ))

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


def check_external_functions(tokens):
    """Only allow function definitions outside the main program."""

    if not tokens:
        return []

    errors = check_statements(tokens)
    inside_function = False

    for line_tokens in group_by_line(tokens):
        first = line_tokens[0]
        keyword = name_of(first)

        if keyword == "HOW IZ I":
            inside_function = True

        elif keyword == "IF U SAY SO":
            inside_function = False

        elif not inside_function:
            errors.append(error_at(
                line_tokens,
                "Only function definitions are allowed "
                "outside HAI and KTHXBYE.",
                first
            ))

    return errors


def check_statements(tokens):
    errors = []
    block_stack = []
    declared = frozenset()
    inside_declarations = False
    declaration_block_seen = False
    opening_token = None
    body_started = False

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
            elif body_started:
                errors.append(error_at(
                    line_tokens,
                    "WAZZUP must appear before other statements.",
                    first
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

        body_started = True

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
