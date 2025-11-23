"""Shared test data constants."""
from typing import List, Tuple

# SQL Injection test patterns
# Each tuple is (pattern, description)
SQL_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    ("--", "double dash comment"),
    (";", "semicolon separator"),
    ("/*", "multi-line comment start"),
    ("*/", "multi-line comment end"),
    ("DROP TABLE users", "DROP keyword"),
    ("DELETE FROM users", "DELETE keyword"),
    ("INSERT INTO users", "INSERT keyword"),
    ("UPDATE users SET", "UPDATE keyword"),
    ("SELECT * FROM users", "SELECT keyword"),
    ("UNION SELECT", "UNION keyword"),
    ("EXEC sp_executesql", "EXEC keyword"),
    ("EXECUTE sp_executesql", "EXECUTE keyword"),
    ("xp_cmdshell 'dir'", "xp_cmdshell"),
    ("SHUTDOWN WITH NOWAIT", "SHUTDOWN keyword"),
    ("CREATE TABLE test", "CREATE keyword"),
    ("ALTER TABLE users", "ALTER keyword"),
    ("RENAME TABLE users", "RENAME keyword"),
    ("TRUNCATE TABLE users", "TRUNCATE keyword"),
    ("DECLARE @var", "DECLARE keyword"),
    ("1=1 OR 1=1", "OR keyword"),
    ("drop table users", "lowercase DROP"),
    ("DeLeTe FrOm users", "mixed case DELETE"),
    ("Test; DROP TABLE", "semicolon followed by DROP"),
    ("Test -- comment", "double dash at end"),
    ("/* malicious */", "complete comment block"),
    ("'; DROP TABLE todos; --", "classic SQL injection"),
    ("Robert'); DROP TABLE students;--", "little bobby tables"),
    ("1' OR '1'='1", "always true condition"),
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

# Valid test strings that should NOT be flagged as SQL injection
# Note: These contain substrings that look like SQL keywords but are part of regular words
VALID_STRINGS_WITH_SQL_LIKE_CONTENT: List[str] = [
    "This was updated yesterday",  # contains "updated" (not "update" as keyword)
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
