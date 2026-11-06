#!/usr/bin/env bash
# run_case.sh <case-id> [reps=3]: runs WITH and WITHOUT in parallel, skips runs that already finished, then grades.
# Env: REPO (required), MODEL (default sonnet). Run from the eval folder.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); ID=$1; REPS=${2:-3}
done_ok() { python3 -I - "$1" <<'PY'
import json,sys
try:
    r = next(i for i in json.load(open(sys.argv[1])) if i.get("type") == "result")
    sys.exit(0 if r.get("result") and not r.get("is_error") else 1)
except Exception:
    sys.exit(1)
PY
}
for v in with without; do for r in $(seq 1 "$REPS"); do
  done_ok "out/$ID-$v-$r.json" || bash "$HERE/run_one.sh" "$ID" "$v" "$r" &
done; done; wait
python3 -I "$HERE/grade.py" "$ID"
