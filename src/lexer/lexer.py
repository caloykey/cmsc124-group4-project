
import re

from .token import create_token
from errors import create_error

# LOLCODE keywords
KEYWORDS = [
    "IF U SAY SO",
    "IM OUTTA YR",
    "HOW IZ I",
    "FOUND YR",
    "IM IN YR",
    "BOTH SAEM",
    "DIFFRINT",
    "PRODUKT OF",
    "QUOSHUNT OF",
    "SMALLR OF",
    "BIGGR OF",
    "SUM OF",
    "DIFF OF",
    "MOD OF",
    "BOTH OF",
    "EITHER OF",
    "WON OF",
    "IS NOW A",
    "I HAS A",
    "I IZ",
    "VISIBLE",
    "GIMMEH",
    "SMOOSH",
    "MAEK",
    "UPPIN",
    "NERFIN",
    "WILE",
    "TIL",
    "YR",
    "AN",
    "ITZ",
    "R",
    "A",
    "NOT",
    "HAI",
    "KTHXBYE",
    "O RLY?",
    "YA RLY",
    "MEBBE",
    "NO WAI",
    "OIC",
    "WTF?",
    "OMG",
    "OMGWTF",
    "GTFO",
    "MKAY",
    "WIN",
    "FAIL",
    "NOOB",
    "NUMBR",
    "NUMBAR",
    "YARN",
    "TROOF",
    "WAZZUP",
    "BUHBYE",
    "ALL OF",
    "ANY OF",
]

# Match longer keywords before shorter ones to avoid partial matches
KEYWORDS.sort(key=len, reverse=True)

TYPE_LITERALS = {"NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"}

# Numeric patterns
NUMBAR_PATTERN = re.compile(r"-?[0-9]+\.[0-9]+")
NUMBR_PATTERN = re.compile(r"-?[0-9]+")
WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

# number followed by a dot
MALFORMED_NUMBAR_PATTERN = re.compile(r"-?[0-9]+\.(?![0-9])")


def is_word_character(character):
    return character.isalnum() or character == "_"


def match_keyword(line, position):
    """Return a keyword and its ending position if one matches."""

    remaining = line[position:]

    for keyword in KEYWORDS:
        # Allow whitespace between words in a multiword keyword.
        pattern_text = r"[ \t]+".join(
            re.escape(word) for word in keyword.split()
        )

        pattern = re.compile(pattern_text, re.IGNORECASE)
        match = pattern.match(remaining)

        if not match:
            continue

        start = position
        end = position + match.end()

        # Do not match a keyword inside a longer identifier
        if start > 0 and is_word_character(line[start - 1]):
            continue

        if end < len(line) and is_word_character(line[end]):
            continue

        return keyword, end

    return None, position


def tokenize(source):
    """
    Convert LOLCODE source code into tokens.

    Returns:
        tokens: a list of token dictionaries
        errors: a list of error dictionaries
    """

    tokens = []
    errors = []
    inside_block_comment = False

    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped_line = line.strip().upper()

        #Handle OBTW and TLDR block comments on their own lines
        if inside_block_comment:
            if stripped_line == "TLDR":
                inside_block_comment = False
            continue

        if stripped_line == "OBTW":
            inside_block_comment = True
            continue

        if stripped_line == "TLDR":
            errors.append(
                create_error(
                    "TLDR found without a matching OBTW.",
                    line_number,
                    line.find("TLDR") + 1
                )
            )
            continue

        position = 0

        while position < len(line):
            character = line[position]

            # Ignore whitespace
            if character.isspace():
                position += 1
                continue

            if line[position:position + 3].upper() == "BTW":
                before_ok = (
                    position == 0
                    or not is_word_character(line[position - 1])
                )
                after_ok = (
                    position + 3 == len(line)
                    or not is_word_character(line[position + 3])
                )

                if before_ok and after_ok:
                    break

            # Strings begin and end with double quotes
            if character == '"':
                start = position
                closing_quote = line.find('"', position + 1)

                if closing_quote == -1:
                    errors.append(
                        create_error(
                            "Unterminated string literal.",
                            line_number,
                            start + 1
                        )
                    )
                    break

                lexeme = line[start:closing_quote + 1]

                tokens.append(
                    create_token(
                        "YARN",
                        lexeme,
                        line_number,
                        start + 1
                    )
                )

                position = closing_quote + 1
                continue

            # Recognize multiword & single-word keywords
            keyword, end_position = match_keyword(line, position)

            if keyword is not None:
                lexeme = line[position:end_position]
                upper_lexeme = lexeme.upper()

                if upper_lexeme in {"WIN", "FAIL"}:
                    token_type = "TROOF"
                elif upper_lexeme in TYPE_LITERALS:
                    token_type = "TYPE_LITERAL"
                else:
                    token_type = "KEYWORD"

                tokens.append(
                    create_token(
                        token_type,
                        lexeme,
                        line_number,
                        position + 1
                    )
                )

                position = end_position
                continue

            # Recognize decimal numbers before whole numbers
            number_match = NUMBAR_PATTERN.match(line, position)

            if number_match:
                lexeme = number_match.group()

                tokens.append(
                    create_token(
                        "NUMBAR",
                        lexeme,
                        line_number,
                        position + 1
                    )
                )

                position = number_match.end()
                continue

            if character == "!":
                tokens.append(
                    create_token(
                        "KEYWORD",
                        character,
                        line_number,
                        position + 1
                    )
                )
                position += 1
                continue


            malformed_match = MALFORMED_NUMBAR_PATTERN.match(
                line, position
            )

            if malformed_match:
                errors.append(
                    create_error(
                        "Malformed NUMBAR literal.",
                        line_number,
                        position + 1
                    )
                )
                position = malformed_match.end()
                continue

            number_match = NUMBR_PATTERN.match(line, position)

            if number_match:
                lexeme = number_match.group()

                tokens.append(
                    create_token(
                        "NUMBR",
                        lexeme,
                        line_number,
                        position + 1
                    )
                )

                position = number_match.end()
                continue

            # Recognize identifiers
            word_match = WORD_PATTERN.match(line, position)

            if word_match:
                lexeme = word_match.group()

                tokens.append(
                    create_token(
                        "IDENTIFIER",
                        lexeme,
                        line_number,
                        position + 1
                    )
                )

                position = word_match.end()
                continue

            # Any unrecognized char becomes an error
            errors.append(
                create_error(
                    f"Invalid character: {character!r}",
                    line_number,
                    position + 1
                )
            )

            position += 1

    if inside_block_comment:
        errors.append(
            create_error(
                "Unterminated block comment: missing TLDR.",
                len(source.splitlines()) or 1,
                1
            )
        )


    return tokens, errors
