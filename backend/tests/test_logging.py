"""Application logging: TD-3 (one configured handler) and SEC-010 (neutralised messages)."""

import logging

import pytest

from backend.app.data_access.database import loggable_url
from backend.app.logger import FORMAT, MAX_VALUE_LENGTH, ROOT, CustomLogger


@pytest.fixture
def records():
    """The records of the "basictodo" loggers, as their handler receives them."""
    captured: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    handler = Capture()
    root = logging.getLogger(ROOT)
    root.addHandler(handler)
    yield captured
    root.removeHandler(handler)


def message(records):
    (record,) = records
    return record.getMessage()


class TestConfiguration:
    def test_one_formatted_handler_however_many_loggers(self):
        CustomLogger("First")
        CustomLogger("Second")
        CustomLogger("First")

        handlers = [
            h
            for h in logging.getLogger(ROOT).handlers
            if type(h).__name__ == "_Handler"
        ]

        assert len(handlers) == 1
        assert (
            handlers[0].formatter is not None and handlers[0].formatter._fmt == FORMAT
        )

    def test_info_is_emitted(self, records):
        CustomLogger("Info").info("started")

        assert message(records) == "started"

    def test_records_do_not_reach_the_root_logger(self):
        CustomLogger("Quiet")

        assert logging.getLogger(ROOT).propagate is False


class TestNeutralisation:
    @pytest.mark.parametrize(
        "value, logged",
        [
            ("a\nforged line", "a\\x0aforged line"),
            ("a\r\nb", "a\\x0d\\x0ab"),
            ("\x1b[31mred", "\\x1b[31mred"),
            ("a b c", "a\\u2028b\\u2029c"),
            ("a\x85b", "a\\x85b"),
            ("lone \udc80 surrogate", "lone \\udc80 surrogate"),
            ("Grüße, tab\there", "Grüße, tab\\x09here"),
        ],
    )
    def test_control_characters_in_values_are_escaped(self, records, value, logged):
        CustomLogger("Values").warning("Invalid UUID provided: %s", value)

        assert message(records) == f"Invalid UUID provided: {logged}"

    def test_f_string_messages_are_escaped_too(self, records):
        value = "x\ny"
        CustomLogger("FString").error(f"failed: {value}")

        assert message(records) == "failed: x\\x0ay"

    def test_long_values_are_cut(self, records):
        CustomLogger("Long").warning("value: %s", "v" * 1000)

        assert message(records) == f"value: {'v' * MAX_VALUE_LENGTH}... (1000 chars)"

    def test_exception_arguments_are_cut_and_escaped(self, records):
        CustomLogger("Exc").error(
            "Error in %s: %s", "create", RuntimeError("boom\n" + "x" * 300)
        )

        logged = message(records)
        assert logged.startswith("Error in create: boom\\x0a")
        assert logged.endswith("... (305 chars)")

    def test_numeric_formats_keep_working(self, records):
        CustomLogger("Numbers").info("%d of %.2f", 3, 2.5)

        assert message(records) == "3 of 2.50"

    @pytest.mark.parametrize(
        "msg, args",
        [
            ("%(a)s %(b)s", ({"a": 1},)),
            ("%c", (10**10,)),
            ("%d", ("not a number",)),
        ],
        ids=["missing key", "overflow", "type"],
    )
    def test_format_errors_never_reach_the_caller(self, records, msg, args):
        CustomLogger("Broken").info(msg, *args)

        assert message(records).endswith("(arguments could not be formatted)")

    def test_a_failing_str_never_reaches_the_caller(self, records):
        class Unprintable:
            def __str__(self) -> str:
                raise RuntimeError("no text")

        CustomLogger("Broken").info("value: %s", Unprintable())

        assert message(records) == "'value: %s' (arguments could not be formatted)"


class TestLoggableUrl:
    @pytest.mark.parametrize(
        "url, logged",
        [
            ("sqlite:///backend/todo.db", "sqlite:///backend/todo.db"),
            (
                "postgresql://user:secret@db.example/todo",
                "postgresql://user:***@db.example/todo",
            ),
            (
                "postgresql://user@db.example/todo?password=secret",
                "postgresql://user@db.example/todo",
            ),
        ],
    )
    def test_password_and_query_are_left_out(self, url, logged):
        assert loggable_url(url) == logged
