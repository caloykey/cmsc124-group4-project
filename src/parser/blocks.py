from .helpers import name_of, error_at, check_line_end, token_at
from .expressions import parse_expression, LITERAL_TYPES

def check_if_line(tokens, declared, block_stack):
    """Return (handled, error). Track if blocks without executing them."""

    first = tokens[0]
    keyword = name_of(first)

    # O RLY? must be followed by YA RLY.
    if (
        block_stack
        and block_stack[-1]["kind"] == "if"
        and block_stack[-1]["phase"] == "start"
        and keyword != "YA RLY"
    ):
        return True, error_at(
            tokens,
            "Expected YA RLY after O RLY?.",
            first
        )

    if keyword == "O RLY?":
        error = check_line_end(tokens, 1)

        if not error:
            block_stack.append({
                "kind": "if",
                "token": first,
                "phase": "start"
            })

        return True, error

    if keyword in {"YA RLY", "MEBBE", "NO WAI"}:
        if not block_stack or block_stack[-1]["kind"] != "if":
            return True, error_at(
                tokens,
                f"Unexpected {keyword}: no matching O RLY?.",
                first
            )

        block = block_stack[-1]

        if keyword == "YA RLY":
            if block["phase"] != "start":
                return True, error_at(
                    tokens,
                    "YA RLY must occur once, before other branches.",
                    first
                )

            error = check_line_end(tokens, 1)

            if not error:
                block["phase"] = "then"

            return True, error

        if keyword == "MEBBE":
            if block["phase"] not in {"then", "elif"}:
                return True, error_at(
                    tokens,
                    "MEBBE must follow YA RLY or MEBBE, "
                    "and cannot follow NO WAI.",
                    first
                )

            position, error = parse_expression(tokens, 1, declared)

            if not error:
                error = check_line_end(tokens, position)

            if not error:
                block["phase"] = "elif"

            return True, error

        if keyword == "NO WAI":
            if block["phase"] not in {"then", "elif"}:
                return True, error_at(
                    tokens,
                    "NO WAI must follow YA RLY or MEBBE "
                    "and can only occur once.",
                    first
                )

            error = check_line_end(tokens, 1)

            if not error:
                block["phase"] = "else"

            return True, error

    return False, None

def check_switch_line(tokens, block_stack):
    """Check switch delimiters, literal cases, and GTFO."""

    first = tokens[0]
    keyword = name_of(first)

    if keyword == "WTF?":
        error = check_line_end(tokens, 1)

        if not error:
            block_stack.append({
                "kind": "switch",
                "token": first,
                "phase": "start",
                "cases": 0
            })

        return True, error

    if keyword in {"OMG", "OMGWTF"}:
        if (
            not block_stack
            or block_stack[-1]["kind"] != "switch"
        ):
            return True, error_at(
                tokens,
                f"Unexpected {keyword}: no matching switch "
                "at this nesting level.",
                first
            )

        block = block_stack[-1]

        if block["phase"] == "default":
            return True, error_at(
                tokens,
                "OMGWTF must be last and can only occur once.",
                first
            )

        if keyword == "OMG":
            literal = token_at(tokens, 1)

            if (
                literal is None
                or not (
                    literal["type"] in LITERAL_TYPES
                    or (
                        literal["type"] == "TYPE_LITERAL"
                        and name_of(literal) == "NOOB"
                    )
                )
            ):
                return True, error_at(
                    tokens,
                    "Expected a literal after OMG.",
                    literal
                )

            error = check_line_end(tokens, 2)

            if not error:
                block["cases"] += 1
                block["phase"] = "case"

            return True, error

        error = check_line_end(tokens, 1)

        if not error:
            block["phase"] = "default"

        return True, error

    if keyword == "GTFO":
        error = check_line_end(tokens, 1)

        if error:
            return True, error

        if not any(
            block["kind"] == "switch"
            for block in block_stack
        ):
            return True, error_at(
                tokens,
                "GTFO requires an enclosing switch.",
                first
            )

        return True, None

    return False, None


def check_block_line(tokens, declared, block_stack):
    """Dispatch block checks and close the nearest block."""

    first = tokens[0]
    keyword = name_of(first)

    if keyword == "OIC":
        error = check_line_end(tokens, 1)

        if error:
            return True, error

        if not block_stack:
            return True, error_at(
                tokens,
                "Unexpected OIC: no matching if or switch.",
                first
            )

        block = block_stack[-1]

        if block["kind"] == "if" and block["phase"] == "start":
            return True, error_at(
                tokens,
                "Missing YA RLY before OIC.",
                first
            )

        if block["kind"] == "switch" and block["cases"] == 0:
            return True, error_at(
                tokens,
                "A switch requires at least one OMG case.",
                first
            )

        block_stack.pop()
        return True, None

    # A switch body cannot start before a case label.
    if (
        block_stack
        and block_stack[-1]["kind"] == "switch"
        and block_stack[-1]["phase"] == "start"
        and keyword not in {"OMG", "OMGWTF"}
    ):
        return True, error_at(
            tokens,
            "Expected OMG or OMGWTF before switch statements.",
            first
        )

    handled, error = check_if_line(
        tokens, declared, block_stack
    )

    if handled:
        return handled, error

    return check_switch_line(tokens, block_stack)