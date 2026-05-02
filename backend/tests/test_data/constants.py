"""Shared test data constants."""

from typing import List, Tuple

# SQL Injection test patterns the sanitizer must still reject.
# The sanitizer only rejects structural markers (statement terminators
# and comment delimiters); bare keywords like DROP/DELETE pass through
# because the ORM parameterizes queries.
SQL_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    ("--", "double dash comment"),
    (";", "semicolon separator"),
    ("/*", "multi-line comment start"),
    ("*/", "multi-line comment end"),
    ("xp_cmdshell 'dir'", "xp_cmdshell"),
    ("Test; DROP TABLE", "semicolon followed by DROP"),
    ("Test -- comment", "double dash at end"),
    ("/* malicious */", "complete comment block"),
    ("'; DROP TABLE todos; --", "classic SQL injection"),
    ("Robert'); DROP TABLE students;--", "little bobby tables"),
    ("admin'--", "admin with comment"),
    ("' UNION SELECT * FROM users--", "UNION injection"),
]

# Common SQL injection patterns for API tests
API_SQL_INJECTION_PATTERNS: List[str] = [
    "'; DROP TABLE todo;--",
    "Robert'); DROP TABLE students;--",
    "1' OR '1'='1",
    "admin'--",
    "' UNION SELECT * FROM users--",
]

# Valid test strings that should NOT be flagged as SQL injection.
# Includes both substring-matches ("updated") and bare keywords as
# whole words ("Update resume"), since the sanitizer no longer
# blocks SQL keywords on their own.
VALID_STRINGS_WITH_SQL_LIKE_CONTENT: List[str] = [
    "This was updated yesterday",
    "Update resume",
    "Delete spam emails",
    "Create slides for Monday",
    "Select recipe ingredients",
    "Insert reminder for the meeting",
    "Drop off the laundry",
    "Truncate the long description",
    "tea or coffee",
]

# Unicode and special character test strings
UNICODE_TEST_STRINGS: List[Tuple[str, str]] = [
    ("Hello 世界 🌍", "mixed unicode with emoji"),
    ("买牛奶", "Chinese characters"),
    ("Café ☕", "accented chars with emoji"),
    ("🎉 Party time 🎂", "emoji only"),
]

# Whitespace test cases
WHITESPACE_TEST_CASES: List[Tuple[str, str, str]] = [
    ("  Test  ", "Test", "both leading and trailing"),
    ("   Leading spaces", "Leading spaces", "leading only"),
    ("Trailing spaces   ", "Trailing spaces", "trailing only"),
    ("   ", "", "whitespace only"),
]
