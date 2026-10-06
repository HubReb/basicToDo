#!/usr/bin/env bash
# Runs super-linter locally (Podman) with exactly the env of the workflow's
# super-linter step, read from .github/workflows/super-linter.yml of the
# current tree. Only DEFAULT_BRANCH's expression `${{ github.base_ref ||
# 'main' }}` is replaced by <base-branch>, the value it takes on a PR into
# that branch, and GITHUB_TOKEN is left out. With VALIDATE_ALL_CODEBASE=false
# super-linter lints the files changed in commits since <base-branch>, so
# uncommitted changes are not linted. The run uses a fresh clone of HEAD, so
# ignored local files (node_modules, dist, caches) are absent, as in CI.
# Usage (from the repository root): run_superlinter.sh <base-branch> <log-file> [image]
set -uo pipefail
BASE=$1
LOG=$(realpath -m "$2")
IMAGE=${3:-ghcr.io/super-linter/super-linter@sha256:496fe2e10c487771d42eede90cacfc767324db5ac9ddc9f3b2f490afa0a1db73}
ENVFILE=$(mktemp)
CLONE=$(mktemp -d)
trap 'rm -rf "$ENVFILE" "$CLONE"' EXIT

git rev-parse --verify --quiet "$BASE" > /dev/null || { echo "branch $BASE not found locally" >&2; exit 2; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || echo "note: uncommitted changes are not linted" >&2

python3 - "$BASE" > "$ENVFILE" <<'EOF'
import sys, yaml
wf = yaml.safe_load(open(".github/workflows/super-linter.yml"))
steps = [s for job in wf["jobs"].values() for s in job["steps"] if "super-linter" in str(s.get("uses", ""))]
assert len(steps) == 1, "expected one super-linter step"
for key, value in steps[0].get("env", {}).items():
    if key == "GITHUB_TOKEN":
        continue
    # GitHub Actions passes YAML booleans as the strings "true"/"false".
    value = str(value).lower() if isinstance(value, bool) else str(value)
    if "github.base_ref" in value:
        value = sys.argv[1]
    print(f"{key}={value}")
EOF
{ echo "image: $IMAGE"; echo "env from workflow:"; sed 's/^/  /' "$ENVFILE"; } > "$LOG"

# A clean clone of HEAD with the base branch available locally, like the CI
# checkout (fetch-depth: 0).
git clone --quiet --no-hardlinks "$PWD" "$CLONE/repo"
git -C "$CLONE/repo" checkout --quiet --detach "$(git rev-parse HEAD)"
git -C "$CLONE/repo" branch --quiet "$BASE" "origin/$BASE" 2> /dev/null \
  || git -C "$CLONE/repo" branch --quiet "$BASE" "$(git rev-parse "$BASE")"
echo "linted commit: $(git rev-parse --short HEAD) against $BASE ($(git rev-parse --short "$BASE"))" >> "$LOG"

podman run --rm --env-file "$ENVFILE" -e RUN_LOCAL=true -e LOG_LEVEL=INFO \
  -v "$CLONE/repo":/tmp/lint:Z "$IMAGE" >> "$LOG" 2>&1
STATUS=$?
echo "super-linter exit $STATUS" | tee -a "$LOG"
grep -a -E "\[(ERROR|FATAL)\]" "$LOG" | sed -E 's/\x1b\[[0-9;]*m//g' | head -n 40
exit $STATUS
