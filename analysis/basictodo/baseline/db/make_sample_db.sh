#!/usr/bin/env bash
# Builds the Phase 4 sample database with the code of the current repository
# root under <venv>: a fresh SQLite file, the schema from init_db.py, rows
# written through the HTTP API (make_sample_db.py). Meant for the legacy code
# (a2d59f1) on the legacy lock.
# Usage (from the root of the tree to run): make_sample_db.sh <venv> <out-dir>
set -euo pipefail
ENV=$(realpath "$1")
OUT=$(realpath -m "$2")
HERE=$(dirname "$(realpath "$0")")
BASELINE=$(dirname "$HERE")
TMP=$(mktemp -d)
mkdir -p "$OUT"

# Logs must not depend on the caller's terminal settings.
unset FORCE_COLOR
export NO_COLOR=1 PY_COLORS=0

# The tree being run stays untouched: no bytecode written into it.
export PYTHONDONTWRITEBYTECODE=1

# The venv may hold an editable install of a different checkout. Put this
# tree first; provenance.py records what each process loaded and aborts if
# any of it came from outside this tree.
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

# Local time five hours ahead of UTC and without DST, independent of the
# machine: created_at (server-local) and updated_at (the database's UTC
# clock) stay visibly apart.
export TZ=Etc/GMT-5

export DATABASE_URL="sqlite:///$TMP/sample.db"
if ! "$ENV/bin/python" "$BASELINE/provenance.py" script "$OUT/provenance-init_db.json" \
  backend/scripts/init_db.py > "$TMP/init_db.log" 2>&1; then
  cat "$TMP/init_db.log" >&2; exit 1
fi
grep '^provenance' "$TMP/init_db.log"

PORT=${SAMPLE_DB_PORT:-18766}
if python3 -c "import socket, sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 0.2)" "$PORT" 2>/dev/null; then
  echo "port $PORT is already in use" >&2; exit 1
fi
"$ENV/bin/python" "$BASELINE/provenance.py" serve "$OUT/provenance-server.json" -- \
  backend.app.api.api:app --host 127.0.0.1 --port "$PORT" > "$TMP/server.log" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true; wait $PID 2>/dev/null || true; rm -rf "$TMP"' EXIT

for _ in $(seq 1 100); do
  python3 -c "import socket, sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 0.2)" "$PORT" 2>/dev/null && break
  kill -0 $PID 2>/dev/null || { cat "$TMP/server.log" >&2; exit 1; }
  sleep 0.1
done
grep '^provenance' "$TMP/server.log"

python3 "$HERE/make_sample_db.py" populate "http://127.0.0.1:$PORT" "$OUT/sample-legacy.requests.json"

# Stop the server before copying, so the file is complete and closed.
kill $PID; wait $PID 2>/dev/null || true
python3 "$HERE/make_sample_db.py" describe "$TMP/sample.db" "$OUT"
