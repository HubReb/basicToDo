#!/usr/bin/env bash
# Runs the backend gates the way python-app.yml does, against a given venv.
# Usage (from the repository root): run_suite.sh <venv> <outdir>
# The venv is used as-is (no uv sync), so a legacy-lock env stays legacy.
set -uo pipefail
ENV=$(realpath "$1")
OUT=$(realpath -m "$2")
mkdir -p "$OUT"
PY="$ENV/bin/python"

HERE=$(dirname "$(realpath "$0")")

# Logs must not depend on the caller's terminal settings.
unset FORCE_COLOR
export NO_COLOR=1 PY_COLORS=0

# The venv may hold an editable install of a different checkout; this tree
# wins. HERE provides provenance.py and the pytest_provenance plugin, which
# record from inside init_db and pytest where the app was loaded from.
export PYTHONPATH="$PWD:$HERE${PYTHONPATH:+:$PYTHONPATH}"

# CI sets no DATABASE_URL: the app falls back to backend/todo.db under cwd.
unset DATABASE_URL
rm -f backend/todo.db .coverage

"$PY" -c 'import fastapi, starlette, sqlalchemy, pydantic, pytest
print("fastapi", fastapi.__version__, "starlette", starlette.__version__,
      "sqlalchemy", sqlalchemy.__version__, "pydantic", pydantic.__version__,
      "pytest", pytest.__version__)' > "$OUT/versions.txt"
"$ENV/bin/python" - > "$OUT/freeze.txt" <<'EOF'
import importlib.metadata as m
for line in sorted({f'{d.metadata["Name"].lower()}=={d.version}' for d in m.distributions()}):
    print(line)
EOF

"$PY" "$HERE/provenance.py" script "$OUT/provenance-init_db.json" backend/scripts/init_db.py > "$OUT/init_db.log" 2>&1
echo "init_db exit $?" >> "$OUT/init_db.log"

PROVENANCE_OUT="$OUT/provenance-pytest.json" \
"$PY" -m pytest backend/tests/ -p no:cacheprovider -p pytest_provenance \
  --cov=backend/app \
  --cov-report=term-missing \
  --cov-report=xml:"$OUT/coverage.xml" \
  --junitxml="$OUT/junit.xml" > "$OUT/pytest.log" 2>&1
echo "pytest exit $?" >> "$OUT/pytest.log"

"$ENV/bin/mypy" backend/app/ > "$OUT/mypy.log" 2>&1
echo "mypy exit $?" >> "$OUT/mypy.log"

rm -f backend/todo.db .coverage
grep '^provenance' "$OUT/init_db.log"
python3 "$HERE/provenance.py" show "$OUT/provenance-pytest.json"
tail -n 3 "$OUT/pytest.log"
grep -E "^Found [0-9]+ error|^Success" "$OUT/mypy.log" || tail -n 2 "$OUT/mypy.log"
