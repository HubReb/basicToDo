#!/usr/bin/env python3
"""Turns a pytest junit.xml into a sorted per-test table.

    junit_table.py <junit.xml>                 prints "<test id>\t<outcome>"
    junit_table.py <junit.xml> --diff <a.tsv>  exits 1 if outcomes differ

Outcome is passed, failed, error or skipped. Durations are dropped, so two
runs of an unchanged suite give byte-identical tables.
"""
import sys
import xml.etree.ElementTree as ET


def table(path):
    rows = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        outcome = "passed"
        for tag in ("failure", "error", "skipped"):
            if tc.find(tag) is not None:
                outcome = {"failure": "failed"}.get(tag, tag)
        rows.append(f'{tc.get("classname")}::{tc.get("name")}\t{outcome}')
    return sorted(rows)


if __name__ == "__main__":
    rows = table(sys.argv[1])
    if len(sys.argv) == 4 and sys.argv[2] == "--diff":
        with open(sys.argv[3], encoding="utf-8") as f:
            expected = [line.rstrip("\n") for line in f if line.strip()]
        missing = sorted(set(expected) - set(rows))
        extra = sorted(set(rows) - set(expected))
        for line in missing:
            print(f"- {line}")
        for line in extra:
            print(f"+ {line}")
        print(f"{len(rows)} tests, {len(missing)} missing or changed, {len(extra)} new or changed")
        sys.exit(1 if missing or extra else 0)
    print("\n".join(rows))
