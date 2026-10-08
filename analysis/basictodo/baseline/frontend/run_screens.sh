#!/usr/bin/env bash
# Serves frontend/dist with a fixed static server (Python stdlib) on port
# 5173, starts the backend of this tree on port 8000 with a fresh SQLite
# database, and captures the persona-flow screens with the fixed runner.
# Usage (from the repository root, after `npm run build`):
#   run_screens.sh <backend-venv> <out-dir> <runner-dir> <node-bin-dir>
# The frontend bundle calls http://localhost:8000, and the backend allows
# only the origin http://localhost:5173, hence the fixed ports.
set -euo pipefail
VENV=$(realpath "$1")
OUT=$(realpath -m "$2")
RUNNER=$(realpath "$3")
NODE_BIN=$(realpath "$4")
HERE=$(dirname "$(realpath "$0")")
TMP=$(mktemp -d)
unset FORCE_COLOR
export NO_COLOR=1

[[ -f frontend/dist/index.html ]] || { echo "frontend/dist is missing; run npm run build first" >&2; exit 1; }
for port in 8000 5173; do
  if python3 -c "import socket, sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 0.2)" "$port" 2> /dev/null; then
    echo "port $port is already in use" >&2; exit 1
  fi
done
mkdir -p "$OUT"
(cd frontend/dist && find . -type f | LC_ALL=C sort | xargs sha256sum) > "$OUT/dist.sha256"
RUNNER_LOCK_SHA=$(sha256sum "$RUNNER/package-lock.json" | cut -d' ' -f1)

export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export DATABASE_URL="sqlite:///$TMP/screens.db"
"$VENV/bin/python" "$HERE/../provenance.py" script "$OUT/provenance-init_db.json" backend/scripts/init_db.py > "$TMP/init_db.log" 2>&1 \
  || { cat "$TMP/init_db.log" >&2; exit 1; }
"$VENV/bin/python" "$HERE/../provenance.py" serve "$OUT/provenance-server.json" -- \
  backend.app.api.api:app --host 127.0.0.1 --port 8000 > "$TMP/backend.log" 2>&1 &
BACKEND=$!
python3 -m http.server 5173 --bind 127.0.0.1 --directory frontend/dist > "$TMP/static.log" 2>&1 &
STATIC=$!
trap 'kill $BACKEND $STATIC 2> /dev/null || true; wait $BACKEND $STATIC 2> /dev/null || true; rm -rf "$TMP"' EXIT

for port in 8000 5173; do
  for _ in $(seq 1 100); do
    python3 -c "import socket, sys; socket.create_connection(('127.0.0.1', int(sys.argv[1])), 0.2)" "$port" 2> /dev/null && break
    sleep 0.1
  done
done
grep '^provenance' "$TMP/backend.log"

"$NODE_BIN/node" "$HERE/capture_screens.mjs" "$RUNNER" "$OUT" "$OUT/dist.sha256" "$RUNNER_LOCK_SHA"
