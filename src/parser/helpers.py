from errors import create_error

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
