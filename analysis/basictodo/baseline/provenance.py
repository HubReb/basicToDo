#!/usr/bin/env python3
"""Records, from inside a process, where the application code was loaded from.

    provenance.py serve  <out.json> -- <uvicorn args>   run uvicorn as `python -m uvicorn` would
    provenance.py script <out.json> <script> [args]     run a script as `python <script>` would
    provenance.py show   <record.json>                  print a record's one-line summary

The venv may hold an editable install of another checkout, so "which tree
did this run?" is answered by the process itself, not by a separate probe.
Every loaded module of the application (`backend.*`, and the top-level
`app.*` that backend/scripts/init_db.py imports) must come from the current
working directory, or the run aborts with exit code 3. Paths are stored
relative to that directory, so a record carries no local path.

The pytest counterpart is pytest_provenance.py.
"""
import json
import os
import runpy
import subprocess
import sys

APP_PREFIXES = ("backend", "app")


def _version(dist):
    try:
        from importlib.metadata import version

        return version(dist)
    except Exception:
        return None


def collect(process):
    root = os.getcwd()
    modules, outside = {}, []
    for name, mod in sorted(sys.modules.items()):
        if name.split(".")[0] not in APP_PREFIXES:
            continue
        path = getattr(mod, "__file__", None)
        if not path:
            continue
        path = os.path.realpath(path)
        if path.startswith(root + os.sep):
            modules[name] = os.path.relpath(path, root)
        else:
            outside.append(name)
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        sha, dirty = None, None
    return {
        "process": process,
        "tree": sha,
        "tree_has_uncommitted_changes": dirty,
        "python": sys.version.split()[0],
        "venv": os.path.relpath(sys.prefix, root),
        "fastapi": _version("fastapi"),
        "starlette": _version("starlette"),
        "app_modules_loaded": len(modules) + len(outside),
        "app_modules_outside_tree": outside,
        "backend.app": modules.get("backend.app"),
        "modules": modules,
    }


def summary(record):
    return (
        f"provenance [{record['process']}]: tree {record['tree']}, venv {record['venv']}, "
        f"fastapi {record['fastapi']}, backend.app -> {record['backend.app']}, "
        f"{record['app_modules_loaded']} app modules, "
        f"outside tree: {record['app_modules_outside_tree'] or 'none'}"
    )


def write(record, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)
        f.write("\n")
    print(summary(record), file=sys.stderr, flush=True)
    if record["app_modules_outside_tree"] or not record["backend.app"]:
        sys.exit(3)


def serve(out_path, uvicorn_args):
    # `python -m` puts the working directory first on sys.path; do the same.
    sys.path[0] = os.getcwd()
    import backend.app.api.api  # noqa: F401  (the module uvicorn will serve)

    write(collect("uvicorn server"), out_path)
    from uvicorn.main import main as uvicorn_main

    uvicorn_main(args=uvicorn_args)


def script(out_path, path, args):
    # `python <script>` puts the script's directory first on sys.path.
    sys.argv = [path, *args]
    sys.path[0] = os.path.dirname(os.path.abspath(path))
    try:
        runpy.run_path(path, run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise
    write(collect(os.path.basename(path)), out_path)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "serve" and sys.argv[3] == "--":
        serve(sys.argv[2], sys.argv[4:])
    elif len(sys.argv) >= 4 and sys.argv[1] == "script":
        script(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif len(sys.argv) == 3 and sys.argv[1] == "show":
        with open(sys.argv[2], encoding="utf-8") as f:
            print(summary(json.load(f)))
    else:
        sys.exit(__doc__)
