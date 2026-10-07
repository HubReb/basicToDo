"""The rules for a todo's title and description (Q6.2), shared by the request schemas.

The order matters:
1. control characters (Unicode category Cc) and lone surrogates (Cs) are
   checked in the raw value, before stripping, since str.strip() would
   remove some of them (U+001C to U+001F, U+0085) from the ends;
2. the value is stripped;
3. its length is counted in code points, the way SQLite's length() counts.

Titles allow no control character at all, tab and newline included.
Descriptions allow tab, line feed and carriage return (multiline text).
"""

import unicodedata

MAX_TEXT_LENGTH = 255
DESCRIPTION_CONTROLS = frozenset("\t\n\r")


def _check_characters(value: str, field: str, allowed: frozenset[str]) -> None:
    for char in value:
        category = unicodedata.category(char)
        if category == "Cs":
            raise ValueError(f"{field} must not contain unpaired surrogates")
        if category == "Cc" and char not in allowed:
            raise ValueError(f"{field} must not contain control characters")


def _check_length(value: str, field: str) -> None:
    if len(value) > MAX_TEXT_LENGTH:
        raise ValueError(f"{field} must be at most {MAX_TEXT_LENGTH} characters")


def clean_title(value: str) -> str:
    """The title, stripped; ValueError if it breaks a rule."""
    _check_characters(value, "title", frozenset())
    stripped = value.strip()
    if not stripped:
        raise ValueError("title must not be null.")
    _check_length(stripped, "title")
    return stripped


def clean_description(value: str | None) -> str | None:
    """The description, stripped; None stays None; ValueError if it breaks a rule."""
    if value is None:
        return None
    _check_characters(value, "description", DESCRIPTION_CONTROLS)
    stripped = value.strip()
    _check_length(stripped, "description")
    return stripped
