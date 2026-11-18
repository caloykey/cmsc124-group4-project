from .helpers import name_of, token_at, error_at

ARITHMETIC_OPERATORS = {
    "SUM OF",
    "DIFF OF",
    "PRODUKT OF",
    "QUOSHUNT OF",
    "MOD OF",
    "BIGGR OF",
    "SMALLR OF",
}

BOOLEAN_OPERATORS = {
    "BOTH OF",
    "EITHER OF",
    "WON OF",
}

VARIADIC_BOOLEAN_OPERATORS = {
    "ALL OF",
    "ANY OF",
}

COMPARISON_OPERATORS = {
    "BOTH SAEM",
    "DIFFRINT",
}

BINARY_OPERATORS = ARITHMETIC_OPERATORS | BOOLEAN_OPERATORS | COMPARISON_OPERATORS

LITERAL_TYPES = {"NUMBR", "NUMBAR", "YARN", "TROOF"}
TYPE_NAMES = {"NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"}


def parse_expression(tokens, position, declared, in_variadic=False, nested=False):
    """
    Validate LOLCODE expressions, including nested operations.

    Returns (next_position, error).
    """

    token = token_at(tokens, position)

    if token is None:
        return position, error_at(
            tokens, "Expected a value, variable, or expression."
        )

    # SMOOSH cannot be nested inside another expression.
    if name_of(token) == "SMOOSH" and nested:
        return position, error_at(
            tokens,
            "SMOOSH cannot be nested inside another expression.",
            token
        )

    position += 1

    # Literals: 12, 3.14, "text", WIN, FAIL, NOOB
    if (
        token["type"] in LITERAL_TYPES
        or (
            token["type"] == "TYPE_LITERAL"
            and name_of(token) == "NOOB"
        )
    ):
        return position, None

    # Variable existence and scope belong to semantic analysis.
    if token["type"] == "IDENTIFIER":
        return position, None

    # Unary boolean operator
    if name_of(token) == "NOT":
        return parse_expression(
            tokens, position, declared, in_variadic, True
        )

    # ALL OF / ANY OF
    if name_of(token) in VARIADIC_BOOLEAN_OPERATORS:
        operator = name_of(token)

        if in_variadic:
            return position, error_at(
                tokens,
                "ALL OF and ANY OF cannot be nested "
                "inside ALL OF or ANY OF.",
                token
            )

        # First operand
        position, error = parse_expression(
            tokens, position, declared, True, True
        )

        if error:
            return position, error

        while True:
            following = token_at(tokens, position)

            if following is None:
                return position, error_at(
                    tokens,
                    f"Expected MKAY to close {operator}."
                )

            if name_of(following) == "MKAY":
                return position + 1, None

            if name_of(following) != "AN":
                return position, error_at(
                    tokens,
                    f"Expected AN or MKAY after an operand of {operator}.",
                    following
                )

            position += 1

            # Additional operand
            position, error = parse_expression(
                tokens, position, declared, True, True
            )

            if error:
                return position, error

    # String concatenation
    if name_of(token) == "SMOOSH":

        # First operand
        position, error = parse_expression(
            tokens, position, declared, in_variadic, True
        )

        if error:
            return position, error

        while True:
            following = token_at(tokens, position)

            # End of line can terminate SMOOSH.
            if following is None:
                return position, None

            # Optional MKAY
            if name_of(following) == "MKAY":
                return position + 1, None

            if name_of(following) != "AN":
                return position, error_at(
                    tokens,
                    "Expected AN or MKAY after a SMOOSH operand.",
                    following
                )

            position += 1

            # Additional operand
            position, error = parse_expression(
                tokens, position, declared, in_variadic, True
            )

            if error:
                return position, error

    # Explicit typecasting
    if name_of(token) == "MAEK":
        position, error = parse_expression(
            tokens, position, declared, in_variadic, True
        )

        if error:
            return position, error

        # A is optional.
        following = token_at(tokens, position)

        if following is not None and name_of(following) == "A":
            position += 1

        type_token = token_at(tokens, position)

        if (
            type_token is None
            or type_token["type"] != "TYPE_LITERAL"
            or name_of(type_token) not in TYPE_NAMES
        ):
            return position, error_at(
                tokens,
                "Expected a type after MAEK: "
                "NOOB, NUMBR, NUMBAR, YARN, or TROOF.",
                type_token
            )

        return position + 1, None

    # Function call
    if name_of(token) == "I IZ":
        function_name = token_at(tokens, position)

        if (
            function_name is None
            or function_name["type"] != "IDENTIFIER"
        ):
            return position, error_at(
                tokens,
                "Expected a function name after I IZ.",
                function_name
            )

        position += 1
        following = token_at(tokens, position)

        # Optional function arguments
        if following is not None and name_of(following) == "YR":
            position += 1

            while True:
                position, error = parse_expression(
                    tokens, position, declared, in_variadic, True
                )

                if error:
                    return position, error

                following = token_at(tokens, position)

                if following is None or name_of(following) != "AN":
                    break

                position += 1
                separator = token_at(tokens, position)

                if separator is None or name_of(separator) != "YR":
                    return position, error_at(
                        tokens,
                        "Expected YR after AN in a function call.",
                        separator
                    )

                position += 1

        closing = token_at(tokens, position)

        if closing is None or name_of(closing) != "MKAY":
            return position, error_at(
                tokens,
                "Expected MKAY to close the function call.",
                closing
            )

        return position + 1, None

    # Binary arithmetic, boolean, and comparison operators
    if name_of(token) in BINARY_OPERATORS:
        operator = name_of(token)

        # First operand
        position, error = parse_expression(
            tokens, position, declared, in_variadic, True
        )

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

        # Second operand
        return parse_expression(
            tokens, position, declared, in_variadic, True
        )

    # Unrecognized expression
    return position, error_at(
        tokens,
        f"Expected a value, variable, or expression, "
        f"found '{token['lexeme']}'.",
        token
    )
