#!/usr/bin/env bash
# run_all.sh [reps=3] [case-id-regex=.]: runs every matching case (WITH and WITHOUT), JOBS cases at a time,
# then a second pass that retries runs that failed (network errors), then grades.
# Env: REPO (required), MODEL (default sonnet), JOBS (default 4). Run from the eval folder.
set -uo pipefail
: "${REPO:?set REPO to the repo or worktree path}"
HERE=$(cd "$(dirname "$0")" && pwd); REPS=${1:-3}; FILTER=${2:-.}; JOBS=${JOBS:-4}
[ -f cases.tsv ] || { echo "no cases.tsv here: run from the eval folder (python3 make_cases.py)" >&2; exit 1; }
command -v claude >/dev/null || { echo "claude CLI not on PATH" >&2; exit 1; }
mkdir -p out
SHA=$(git -C "$REPO" rev-parse HEAD)
{ echo "REPO $REPO at $SHA"; echo "claude $(claude --version 2>/dev/null)"; echo "MODEL ${MODEL:-sonnet}"; } | tee base.txt
CASES=$(cut -f1 cases.tsv | grep -E "$FILTER")
for pass in 1 2; do
  echo "$CASES" | xargs -P "$JOBS" -I{} bash "$HERE/run_case.sh" {} "$REPS" > "out/run-pass$pass.log" 2>&1
done
NOW=$(git -C "$REPO" rev-parse HEAD)
[ "$NOW" != "$SHA" ] && echo "WARNING: $REPO moved from $SHA to $NOW during the runs. Rerun the affected runs." >&2
for c in $CASES; do python3 "$HERE/grade.py" "$c" | tail -2; done | tee out/summary.txt
