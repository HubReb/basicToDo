#!/usr/bin/env bash
# Runs the frontend gates the way frontend.yml and e2e.yml do, on a chosen
# Node. Usage (from the repository root):
#   run_frontend_suite.sh <node-bin-dir> <outdir> [backend-venv]
# With a backend venv, Playwright e2e runs as well; its webServer starts the
# backend from this tree through `uv run` on that venv, without syncing it.
set -uo pipefail
NODE_BIN=$(realpath "$1")
OUT=$(realpath -m "$2")
VENV=${3:+$(realpath "$3")}
HERE=$(dirname "$(realpath "$0")")
mkdir -p "$OUT"

# Logs must not depend on the caller's terminal settings.
unset FORCE_COLOR
export NO_COLOR=1
export PATH="$NODE_BIN:$PATH"

{ echo "node $(node -v)"; echo "npm $(npm -v)"; } > "$OUT/versions.txt"

cd frontend || exit 1
rm -rf node_modules dist
npm ci --no-audit --no-fund > "$OUT/npm-ci.log" 2>&1
echo "npm ci exit $?" >> "$OUT/npm-ci.log"
npm ls --depth=0 > "$OUT/npm-ls.txt" 2>&1

npx vitest run --reporter=default --reporter=junit --outputFile.junit="$OUT/vitest-junit.xml" \
  > "$OUT/vitest.log" 2>&1
echo "vitest exit $?" >> "$OUT/vitest.log"

npm run build > "$OUT/build.log" 2>&1
echo "build exit $?" >> "$OUT/build.log"
if [[ -d dist ]]; then
  (cd dist && find . -type f | LC_ALL=C sort | xargs sha256sum) > "$OUT/dist.sha256"
  (cd dist && find . -type f | LC_ALL=C sort | xargs wc -c) > "$OUT/dist.sizes"
fi

npm run lint > "$OUT/lint.log" 2>&1
echo "lint exit $?" >> "$OUT/lint.log"

npm audit --json > "$OUT/audit.json" 2> /dev/null
python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["metadata"]["vulnerabilities"])' \
  "$OUT/audit.json" > "$OUT/audit.summary"

if [[ -n "$VENV" ]]; then
  rm -f ../test.db
  CI=true UV_PYTHON=3.13 UV_PROJECT_ENVIRONMENT="$VENV" UV_NO_SYNC=1 \
    PLAYWRIGHT_JSON_OUTPUT_NAME="$OUT/e2e.json" \
    npx playwright test --reporter=list,json > "$OUT/e2e.log" 2>&1
  echo "e2e exit $?" >> "$OUT/e2e.log"
  rm -rf "$OUT/playwright-report" "$OUT/test-results"
  mv playwright-report test-results "$OUT/" 2> /dev/null
  rm -f ../test.db
fi
cd ..

python3 "$HERE/../junit_table.py" "$OUT/vitest-junit.xml" > "$OUT/vitest.tsv" 2> /dev/null
cat "$OUT/versions.txt"
tail -n 1 "$OUT/npm-ci.log"
grep -E "Tests +[0-9]+" "$OUT/vitest.log"; tail -n 1 "$OUT/vitest.log"
grep -E "dist/" "$OUT/build.log"; tail -n 1 "$OUT/build.log"
tail -n 1 "$OUT/lint.log"
echo "npm audit $(cat "$OUT/audit.summary")"
if [[ -n "$VENV" ]]; then grep -E "passed|failed|flaky" "$OUT/e2e.log" | tail -n 2; tail -n 1 "$OUT/e2e.log"; fi
