#!/usr/bin/env python3
"""Reads or writes a copy of the sample database through the application's own code.

    sample_db_io.py read  <db> <out.json>
    sample_db_io.py write <db> <out.json> <legacy|new>

Run it from the root of the tree under test, on that tree's venv, through
provenance.py script; sample_db_roundtrip.sh does that for both trees.

read: every row through the application's ORM mapping, soft-deleted rows
included, with the Python type of each value; plus the service's list of
active todos (ToDoSchema as JSON).

write: through the service (builder, validators, repository): two new todos,
one with and one without description; a title edit, a done and a soft delete
of three sample rows; and a 256-character title, which the CHECK constraint
rejects (RULE-013). Each side has its own ids and target rows, so both sides
can write to one file.
"""

import asyncio
import json
import os
import sys
import uuid

FIELDS = ("id", "title", "description", "created_at", "updated_at", "deleted", "done")

# The sample rows each side edits, marks done and deletes (disjoint).
TARGETS = {
    "new": {"edit": 1, "done": 2, "delete": 8},
    "legacy": {"edit": 3, "done": 9, "delete": 0},
}
SIDE_BLOCK = {"new": 100, "legacy": 200}


def sample_id(n):
    return (
        uuid.UUID(int=0) if n == 0 else uuid.UUID(f"5a3e0000-0000-4000-8000-{n:012d}")
    )


def value(v):
    return (
        v.isoformat()
        if hasattr(v, "isoformat")
        else (str(v) if isinstance(v, uuid.UUID) else v)
    )


def main():
    mode, db, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.environ["DATABASE_URL"] = f"sqlite:///{os.path.abspath(db)}"

    # Imported only now: the application reads DATABASE_URL on import. On the
    # legacy code, importing database also maps ToDoEntryData.
    from backend.app.data_access import database
    from backend.app.factory import create_todo_service
    from backend.app.models.todo import ToDoEntryData
    from backend.app.schemas.data_schemes.create_todo_schema import ToDoCreateScheme
    from backend.app.schemas.data_schemes.update_todo_schema import TodoUpdateScheme

    service = create_todo_service()

    if mode == "read":
        with database.SessionLocal() as session:
            entries = session.query(ToDoEntryData).all()
        rows = [
            {
                **{f: value(getattr(e, f)) for f in FIELDS},
                "types": {f: type(getattr(e, f)).__name__ for f in FIELDS},
            }
            for e in entries
        ]
        listed = asyncio.run(service.get_all_todos(limit=100))
        result = {
            "rows": sorted(rows, key=lambda r: r["id"]),
            "service_list": sorted(
                (t.model_dump(mode="json") for t in listed), key=lambda t: t["id"]
            ),
        }
    elif mode == "write":
        side = sys.argv[4]
        block, targets = SIDE_BLOCK[side], TARGETS[side]

        def attempt(name, call):
            try:
                outcome = asyncio.run(call)
                if hasattr(outcome, "model_dump"):
                    outcome = outcome.model_dump(mode="json")
                return {"step": name, "ok": True, "result": outcome}
            except Exception as exc:  # recorded, compared between the sides
                return {"step": name, "ok": False, "error": type(exc).__name__}

        result = [
            attempt(
                "create with description",
                service.create_todo(
                    ToDoCreateScheme(
                        id=sample_id(block + 1),
                        title=f"Written by the {side} code",
                        description="round trip",
                    )
                ),
            ),
            attempt(
                "create without description",
                service.create_todo(
                    ToDoCreateScheme(
                        id=sample_id(block + 2), title=f"Also by the {side} code"
                    )
                ),
            ),
            attempt(
                "edit a sample row",
                service.update_todo(
                    sample_id(targets["edit"]),
                    TodoUpdateScheme(title=f"Edited by the {side} code"),
                ),
            ),
            attempt(
                "mark a sample row done",
                service.update_todo(
                    sample_id(targets["done"]), TodoUpdateScheme(done=True)
                ),
            ),
            attempt(
                "delete a sample row", service.delete_todo(sample_id(targets["delete"]))
            ),
            attempt(
                "256-character title (RULE-013)",
                service.create_todo(
                    ToDoCreateScheme(id=sample_id(block + 3), title="y" * 256)
                ),
            ),
        ]
    else:
        sys.exit(__doc__)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
