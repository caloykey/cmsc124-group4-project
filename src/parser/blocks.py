from .helpers import name_of, error_at, check_line_end
from .expressions import parse_expression

def check_if_line(tokens, declared, if_stack):
    """Return (handled, error). Track if blocks without executing them."""

    first = tokens[0]
    keyword = name_of(first)

    # O RLY? must be followed by YA RLY.
    if (
        if_stack
        and if_stack[-1]["phase"] == "start"
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
            if_stack.append({
                "token": first,
                "phase": "start"
            })

        return True, error

    if keyword in {"YA RLY", "MEBBE", "NO WAI", "OIC"}:
        if not if_stack:
            return True, error_at(
                tokens,
                f"Unexpected {keyword}: no matching O RLY?.",
                first
            )

        block = if_stack[-1]

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

        # OIC closes the innermost if block.
        error = check_line_end(tokens, 1)

        if not error:
            if_stack.pop()

        return True, error

    return False, None