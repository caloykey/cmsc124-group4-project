def create_error(message, line, column):
    return {
        "message": message,
        "line": line,
        "column": column
    }


def format_error(error):
    return (
        f"Line {error['line']}, "
        f"Column {error['column']}: "
        f"{error['message']}"
    )