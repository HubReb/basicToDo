#!/usr/bin/env python3
"""The Phase 4 sample database: rows written through the HTTP API.

    make_sample_db.py populate <base-url> <requests.json>
    make_sample_db.py describe <sample.db> <out-dir>

populate sends a fixed request sequence that leaves one row per case the
data layer has to carry: active with and without description, description
NULL, done, soft-deleted with and without description, done and deleted,
edited, a 255-character non-ASCII title and the nil UUID. An over-long title
(RULE-013) is rejected and stores nothing. Every response must have the
expected status, or the run stops. The ids are fixed; the timestamps are
whatever the server writes.

describe copies the database to <out-dir>/sample-legacy.db and writes, next
to it, its sha256 (sha256sum format), a text dump (sqlite3 iterdump) and
schema.json, the database's sqlite_master as [type, name, tbl_name, sql]
rows ordered by type and name.

Standard library only; run make_sample_db.sh rather than this file directly.
"""

import hashlib
import http.client
import json
import os
import shutil
import sqlite3
import sys
import urllib.parse


def todo_id(n):
    return f"5a3e0000-0000-4000-8000-{n:012d}"


NIL_ID = "00000000-0000-0000-0000-000000000000"
LONG_TITLE = ("Grüße aus Köln. " * 16)[:255]

# (method, path, body, expected status, case)
SEQUENCE = [
    (
        "POST",
        "/todo",
        {"id": todo_id(1), "title": "Buy milk", "description": "two litres"},
        200,
        "active",
    ),
    (
        "POST",
        "/todo",
        {"id": todo_id(2), "title": "Water the plants"},
        200,
        "active, no description",
    ),
    (
        "POST",
        "/todo",
        {"id": todo_id(3), "title": "Call the plumber", "description": "kitchen sink"},
        200,
        "",
    ),
    ("PUT", f"/todo/{todo_id(3)}", {"description": None}, 200, "description NULL"),
    (
        "POST",
        "/todo",
        {"id": todo_id(4), "title": "Pay rent", "description": "by the 3rd"},
        200,
        "",
    ),
    ("PUT", f"/todo/{todo_id(4)}", {"done": True}, 200, "done"),
    (
        "POST",
        "/todo",
        {
            "id": todo_id(5),
            "title": "Book train tickets",
            "description": "Berlin to Hamburg",
        },
        200,
        "",
    ),
    ("DELETE", f"/todo/{todo_id(5)}", None, 200, "soft-deleted"),
    ("POST", "/todo", {"id": todo_id(6), "title": "Return library books"}, 200, ""),
    ("DELETE", f"/todo/{todo_id(6)}", None, 200, "soft-deleted, no description"),
    (
        "POST",
        "/todo",
        {"id": todo_id(7), "title": "File the tax return", "description": "for 2025"},
        200,
        "",
    ),
    ("PUT", f"/todo/{todo_id(7)}", {"done": True}, 200, ""),
    ("DELETE", f"/todo/{todo_id(7)}", None, 200, "done and soft-deleted"),
    (
        "POST",
        "/todo",
        {"id": todo_id(8), "title": "Draft title", "description": "first wording"},
        200,
        "",
    ),
    ("PUT", f"/todo/{todo_id(8)}", {"title": "Final title"}, 200, "edited"),
    (
        "POST",
        "/todo",
        {"id": todo_id(9), "title": LONG_TITLE},
        200,
        "255 characters, non-ASCII",
    ),
    ("POST", "/todo", {"id": NIL_ID, "title": "Nil id"}, 200, "nil UUID (RULE-020)"),
    (
        "POST",
        "/todo",
        {"id": todo_id(10), "title": "x" * 256},
        409,
        "256 characters: CHECK rejects (RULE-013)",
    ),
    ("GET", "/todo?limit=100", None, 200, "list of active todos"),
]


def populate(base_url, out_path):
    url = urllib.parse.urlsplit(base_url)
    log = []
    for method, path, body, expected, case in SEQUENCE:
        conn = http.client.HTTPConnection(url.hostname, url.port, timeout=30)
        payload = None if body is None else json.dumps(body)
        headers = {} if body is None else {"Content-Type": "application/json"}
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        text = response.read().decode("utf-8")
        conn.close()
        log.append(
            {
                "case": case,
                "method": method,
                "path": path,
                "body": body,
                "status": response.status,
                "response": text,
            }
        )
        if response.status != expected:
            sys.exit(
                f"{method} {path}: expected {expected}, got {response.status}: {text}"
            )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"populate: {len(log)} requests, all with the expected status")


def describe(db_path, out_dir):
    target = os.path.join(out_dir, "sample-legacy.db")
    shutil.copyfile(db_path, target)
    with open(target, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    with open(target + ".sha256", "w", encoding="utf-8") as f:
        f.write(f"{digest}  sample-legacy.db\n")

    conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        with open(
            os.path.join(out_dir, "sample-legacy.dump.txt"), "w", encoding="utf-8"
        ) as f:
            for line in conn.iterdump():
                f.write(line + "\n")
        schema = conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
        rows = conn.execute(
            'SELECT COUNT(*), SUM(deleted), SUM(done) FROM "toDo"'
        ).fetchone()
    finally:
        conn.close()
    with open(os.path.join(out_dir, "schema.json"), "w", encoding="utf-8") as f:
        f.write(
            "[\n" + ",\n".join(" " + json.dumps(list(row)) for row in schema) + "\n]\n"
        )
    print(
        f"describe: {rows[0]} rows ({rows[1]} deleted, {rows[2]} done), sha256 {digest}"
    )


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "populate":
        populate(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[1] == "describe":
        describe(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
