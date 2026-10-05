"""pytest plugin: records where the application code was loaded from.

Load it with `-p pytest_provenance` (its directory must be on PYTHONPATH)
and set PROVENANCE_OUT to the output file. At the end of the session it
writes the same record as provenance.py, taken from the pytest process
itself, and fails the session if any application module came from outside
the working directory.
"""
import os

from provenance import collect


def pytest_sessionfinish(session, exitstatus):
    out = os.environ.get("PROVENANCE_OUT")
    if not out:
        return
    import json
    record = collect("pytest")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)
        f.write("\n")
    if record["app_modules_outside_tree"] or not record["backend.app"]:
        session.exitstatus = 3
