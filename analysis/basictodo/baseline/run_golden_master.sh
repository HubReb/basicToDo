#!/usr/bin/env bash
# Starts the backend of the current repository root under <venv> on a fresh
# SQLite database and records the golden master to <out.json>.
# Usage (from the repository root): run_golden_master.sh <venv> <out.json> [server-log]
set -euo pipefail
ENV=$(realpath "$1")
OUT=$(realpath -m "$2")
LOG=${3:-/dev/null}
HERE=$(dirname "$(realpath "$0")")
TMP=$(mktemp -d)

# Logs must not depend on the caller's terminal settings.
unset FORCE_COLOR
export NO_COLOR=1 PY_COLORS=0

# The venv may hold an editable install of a different checkout. Put this
# tree first on the path. provenance.py then records, inside init_db and
# inside the server process, where the app was loaded from, and aborts if
# any of it came from outside this tree.
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

export DATABASE_URL="sqlite:///$TMP/golden_master.db"
if ! "$ENV/bin/python" "$HERE/provenance.py" script "$TMP/provenance-init_db.json" backend/scripts/init_db.py > "$TMP/init_db.log" 2>&1; then
  cat "$TMP/init_db.log" >&2; exit 1
fi
grep '^provenance' "$TMP/init_db.log"

# A fixed port: the 307 redirect's Location header carries it, so a random
# port would make every capture differ.
PORT=${GOLDEN_MASTER_PORT:-18765}
if python3 -c "import socket, sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 0.2)" "$PORT" 2>/dev/null; then
  echo "port $PORT is already in use" >&2; exit 1
fi
"$ENV/bin/python" "$HERE/provenance.py" serve "$TMP/provenance-server.json" -- \
  backend.app.api.api:app --host 127.0.0.1 --port "$PORT" > "$TMP/server.log" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true; wait $PID 2>/dev/null || true; cp "$TMP/server.log" "$LOG" 2>/dev/null || true; rm -rf "$TMP"' EXIT

# Wait until the server accepts connections. The probe opens a TCP socket
# only, so the server sees no HTTP request before the capture starts.
for _ in $(seq 1 100); do
  python3 -c "import socket, sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 0.2)" "$PORT" 2>/dev/null && break
  kill -0 $PID 2>/dev/null || { cat "$TMP/server.log" >&2; exit 1; }
  sleep 0.1
done

grep '^provenance' "$TMP/server.log"
python3 "$HERE/golden_master.py" capture "http://127.0.0.1:$PORT" "$OUT" \
  "$TMP/provenance-server.json" "$TMP/provenance-init_db.json"
