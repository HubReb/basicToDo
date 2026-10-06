#!/usr/bin/env bash
# The legacy sample database under the legacy code and the new code, in both
# directions, each side in its own process, tree and venv (provenance
# recorded). Works on copies; the committed file is only read.
# Usage: sample_db_roundtrip.sh <legacy-tree> <legacy-venv> <new-tree> <new-venv> <out-dir>
#   (a) both sides read a copy A, which must look the same to both;
#   (b) the new code writes to A, then both sides read A again;
#   (c) on a copy B, the legacy code writes, then the new code, then both read.
# The reads of one file must be identical, the write outcomes of both sides
# must match, and every stored value must have the legacy storage format.
set -euo pipefail
LEGACY_TREE=$(realpath "$1")
LEGACY_ENV=$(realpath "$2")
NEW_TREE=$(realpath "$3")
NEW_ENV=$(realpath "$4")
OUT=$(realpath -m "$5")
HERE=$(dirname "$(realpath "$0")")
BASELINE=$(dirname "$HERE")
SAMPLE="$HERE/sample-legacy.db"
mkdir -p "$OUT"

unset FORCE_COLOR
export NO_COLOR=1 PY_COLORS=0 PYTHONDONTWRITEBYTECODE=1
# As when the sample was made: local time five hours ahead of UTC.
export TZ=Etc/GMT-5

(cd "$HERE" && sha256sum -c --quiet sample-legacy.db.sha256)
cp "$SAMPLE" "$OUT/a.db"
cp "$SAMPLE" "$OUT/b.db"

# side, then the sample_db_io.py arguments; the record is named after the output.
run() {
  local side=$1; shift
  local tree env
  if [ "$side" = legacy ]; then tree=$LEGACY_TREE env=$LEGACY_ENV; else tree=$NEW_TREE env=$NEW_ENV; fi
  local name
  name=$(basename "$3" .json)
  (cd "$tree" && PYTHONPATH="$tree" "$env/bin/python" "$BASELINE/provenance.py" script \
    "$OUT/provenance-$name.json" "$HERE/sample_db_io.py" "$@" 2>&1 | grep '^provenance')
}

run legacy read "$OUT/a.db" "$OUT/a-0-read-legacy.json"
run new read "$OUT/a.db" "$OUT/a-0-read-new.json"
run new write "$OUT/a.db" "$OUT/a-1-write-new.json" new
run legacy read "$OUT/a.db" "$OUT/a-2-read-legacy.json"
run new read "$OUT/a.db" "$OUT/a-2-read-new.json"

run legacy write "$OUT/b.db" "$OUT/b-1-write-legacy.json" legacy
run new write "$OUT/b.db" "$OUT/b-2-write-new.json" new
run legacy read "$OUT/b.db" "$OUT/b-3-read-legacy.json"
run new read "$OUT/b.db" "$OUT/b-3-read-new.json"

python3 - "$OUT" <<'EOF' | tee "$OUT/summary.txt"
import json, re, sqlite3, sys
out = sys.argv[1]
load = lambda name: json.load(open(f"{out}/{name}.json", encoding="utf-8"))
failures = 0

def check(label, ok):
    global failures
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {label}")

for a, b in [("a-0-read-legacy", "a-0-read-new"), ("a-2-read-legacy", "a-2-read-new"), ("b-3-read-legacy", "b-3-read-new")]:
    check(f"{a} == {b} ({len(load(a)['rows'])} rows, {len(load(a)['service_list'])} listed)", load(a) == load(b))

# The new code's writes: same outcomes on A (alone) and on B (after the legacy writes).
outcomes = lambda steps: [(s["step"], s.get("error", "ok")) for s in steps]
legacy_w, new_a, new_b = load("b-1-write-legacy"), load("a-1-write-new"), load("b-2-write-new")
print("     write outcomes:", "; ".join(f"{step}: {result}" for step, result in outcomes(new_a)))
check("the new code's writes end the same on A and on B", outcomes(new_a) == outcomes(new_b))
check("the legacy code's writes end the same way", outcomes(legacy_w) == outcomes(new_a))

# Storage format of every stored value, by writer.
FORMAT = {
    "id": lambda v, t: t == "text" and re.fullmatch(r"[0-9a-f]{32}", v),
    "created_at": lambda v, t: t == "text" and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{6}", v),
    "updated_at": lambda v, t: t == "text" and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", v),
    "deleted": lambda v, t: t == "integer" and v in (0, 1),
    "done": lambda v, t: t == "integer" and v in (0, 1),
}
writers = {"legacy": 0, "new": 0}
for db in ("a", "b"):
    con = sqlite3.connect(f"file:{out}/{db}.db?mode=ro", uri=True)
    cols = ", ".join(f"{c}, typeof({c})" for c in FORMAT)
    for row in con.execute(f'SELECT {cols} FROM "toDo"'):
        values = dict(zip(FORMAT, zip(row[0::2], row[1::2])))
        # sample_db_io.py gives the new code's rows the ids ...100 to ...199.
        writer = "new" if 100 <= int(values["id"][0][-12:]) < 200 else "legacy"
        writers[writer] += 1
        bad = [c for c, (v, t) in values.items() if not FORMAT[c](v, t)]
        if bad:
            check(f"{db}.db row {values['id'][0]}: format of {bad}", False)
    con.close()
print(f"     rows checked: {writers['legacy']} written by the legacy code, {writers['new']} by the new code")
print("RESULT:", "all checks passed" if not failures else f"{failures} check(s) failed")
sys.exit(1 if failures else 0)
EOF
(cd "$HERE" && sha256sum -c --quiet sample-legacy.db.sha256) && echo "sample-legacy.db unchanged (sha256)"
