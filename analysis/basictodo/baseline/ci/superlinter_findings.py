"""Summarizes a local super-linter v9 log by linter and file.

    superlinter_findings.py <log>

For every "Errors found in <LINTER>" block, collects the repository-relative
paths mentioned in its stdout/stderr and prints them, grouped as
analysis docs and evidence (analysis/, UPLIFT_NOTES.md) or everything else.
A mentioned path is not always a linted file: a formatter's diff can quote
paths from the file's content (shfmt on a script that names backend/app).
"""

import re
import sys
from collections import defaultdict

ANSI = re.compile(r"\x1b\[[0-9;]*m")
START = re.compile(r"\[ERROR\]\s+Errors found in (\S+)")
END = re.compile(
    r"\[(NOTICE|ERROR|INFO)\]\s+(Successfully linted|Errors found in|Super-linter detected)"
)
# A path below one of the top-level directories, or one of the root files.
# Dotted module names (backend.app.x) and bare words are not paths.
PATH = re.compile(
    r"(?:/tmp/lint/)?((?:\.github|analysis|backend|frontend)/[\w./@\-]+|UPLIFT_NOTES\.md|pyproject\.toml|uv\.lock)"
)


def main(path):
    findings = defaultdict(set)
    current = None
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = ANSI.sub("", raw)
        m = START.search(line)
        if m:
            current = m.group(1)
            findings[current]
            continue
        if current and END.search(line):
            current = None
            continue
        if current:
            for p in PATH.findall(line):
                findings[current].add(p.rstrip(".,:;)"))
    for linter in sorted(findings):
        files = sorted(findings[linter])
        docs = [
            f
            for f in files
            if f.startswith("analysis/") or f.startswith("UPLIFT_NOTES")
        ]
        other = [f for f in files if f not in docs]
        print(
            f"{linter}: {len(files)} path(s) mentioned; analysis/notes {len(docs)}, other {len(other)}"
        )
        for f in other:
            print(f"    {f}")


if __name__ == "__main__":
    main(sys.argv[1])
