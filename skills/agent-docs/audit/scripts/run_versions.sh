#!/usr/bin/env bash
# run_versions.sh [reps=5] [case-id-regex=.]: old-vs-new mode for docs that load in every session
# (CLAUDE.md, AGENTS.md, files they link). Runs every matching case as a plain session in the OLD
# and the NEW checkout, then grades both. Results go to old/out and new/out under the eval folder.
# Env: REPO_OLD, REPO_NEW (required: two worktrees, e.g. the base commit and the edited branch),
# MODEL (default sonnet). Run from the eval folder, which holds cases.tsv.
set -uo pipefail
: "${REPO_OLD:?set REPO_OLD to the checkout with the old docs}"
: "${REPO_NEW:?set REPO_NEW to the checkout with the new docs}"
HERE=$(cd "$(dirname "$0")" && pwd); REPS=${1:-5}; FILTER=${2:-.}; EVAL=$(pwd)
[ -f cases.tsv ] || { echo "no cases.tsv here: run from the eval folder" >&2; exit 1; }
CASES=$(cut -f1 cases.tsv | grep -E "$FILTER")
done_ok() { python3 -I -c "import json,sys;r=next(i for i in json.load(open(sys.argv[1])) if i.get('type')=='result');sys.exit(0 if r.get('result') and not r.get('is_error') else 1)" "$1" 2>/dev/null; }
for pass in 1 2; do   # pass 2 reruns crashed runs (network errors)
  for side in old new; do
    [ $side = old ] && R=$REPO_OLD || R=$REPO_NEW
    mkdir -p "$EVAL/$side" && cp cases.tsv "$EVAL/$side/"
    for c in $CASES; do for r in $(seq 1 "$REPS"); do
      done_ok "$EVAL/$side/out/$c-with-$r.json" || (cd "$EVAL/$side" && REPO=$R bash "$HERE/run_one.sh" "$c" with "$r") &
    done; done
  done; wait
done
for side in old new; do
  echo "== $side ($(git -C "$([ $side = old ] && echo "$REPO_OLD" || echo "$REPO_NEW")" rev-parse --short HEAD))"
  for c in $CASES; do python3 -I "$HERE/grade.py" "$c" --dir "$EVAL/$side" | tail -1; done
done | tee "$EVAL/versions-summary.txt"
