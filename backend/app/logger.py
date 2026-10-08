"""Application logging (TD-3) with neutralised messages (SEC-010).

Every CustomLogger writes through the standard logger "basictodo.<name>".
One handler on "basictodo" formats the records; it is installed once, the
first time a CustomLogger is created. "basictodo" does not propagate, so a
configured root logger does not print the records a second time.

A filter on each "basictodo.<name>" logger formats a record's message once,
before any handler sees it. String and exception arguments are cut at
MAX_VALUE_LENGTH characters first; other arguments keep their type, so %d
still works. The formatted message, f-strings included, then has its
control characters (C0, C1, U+2028, U+2029) and lone surrogates escaped, so
logged input cannot start a new line or send terminal escapes.
"""

import logging
from typing import Any, TextIO

ROOT = "basictodo"
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_VALUE_LENGTH = 200


def escape_controls(text: str) -> str:
    """The text with control characters and lone surrogates escaped."""
    out = []
    for char in text:
        code = ord(char)
        if (
            code < 0x20
            or 0x7F <= code <= 0x9F
            or code in (0x2028, 0x2029)
            or 0xD800 <= code <= 0xDFFF
        ):
            out.append(f"\\x{code:02x}" if code <= 0xFF else f"\\u{code:04x}")
        else:
            out.append(char)
    return "".join(out)


def _cut(value: Any) -> Any:
    if isinstance(value, (str, BaseException)):
        text = str(value)
        if len(text) > MAX_VALUE_LENGTH:
            return f"{text[:MAX_VALUE_LENGTH]}... ({len(text)} chars)"
        return text
    return value


class NeutraliseMessage(logging.Filter):
    """Formats a record's message once, with cut values and escaped controls."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            args = record.args
            if isinstance(args, tuple):
                args = tuple(_cut(arg) for arg in args)
            elif isinstance(args, dict):
                args = {key: _cut(arg) for key, arg in args.items()}
            message = str(record.msg)
            if args:
                message = message % args
        except Exception:  # never let a bad record reach the caller
            message = f"{record.msg!r} (arguments could not be formatted)"
        record.msg = escape_controls(message)
        record.args = None
        return True


class _Handler(logging.StreamHandler[TextIO]):
    """The one handler of the "basictodo" logger."""


def _configure() -> None:
    root = logging.getLogger(ROOT)
    if any(isinstance(handler, _Handler) for handler in root.handlers):
        return
    handler = _Handler()
    handler.setFormatter(logging.Formatter(FORMAT))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    root.propagate = False


class CustomLogger(logging.LoggerAdapter[logging.Logger]):
    """The application's logger for one component, e.g. CustomLogger("ToDoService")."""

    def __init__(self, name: str) -> None:
        _configure()
        logger = logging.getLogger(f"{ROOT}.{name}")
        if not any(isinstance(f, NeutraliseMessage) for f in logger.filters):
            logger.addFilter(NeutraliseMessage())
        super().__init__(logger, {})
