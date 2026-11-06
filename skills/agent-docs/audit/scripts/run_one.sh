#!/usr/bin/env bash
# One run: run_one.sh <case-id> <with|without> <rep>
# Env: REPO (required) = repo or worktree to run in. MODEL (default sonnet).
# Run from the eval folder, which holds cases.tsv; output goes to out/<case>-<variant>-<rep>.json.
set -uo pipefail
: "${REPO:?set REPO to the repo or worktree path}"
ID=$1; V=$2; R=$3; EVAL=$(pwd); mkdir -p "$EVAL/out"
AGENT=$(awk -F'\t' -v id="$ID" '$1==id{print $2}' "$EVAL/cases.tsv")
P=$(awk -F'\t' -v id="$ID" '$1==id{print $3}' "$EVAL/cases.tsv")
[ -z "$P" ] && { echo "unknown case $ID" >&2; exit 1; }
REPO_REAL=$(cd "$REPO" && pwd -P)

# Paths a WITHOUT run must not read: .claude/<dir> and, when .claude or <dir> is a symlink
# (for example .claude -> .agents), the real path too. Deny rules match the path as written,
# so a run could otherwise read .agents/skills/... and get around a .claude/skills rule.
targets() {
  for d in "$@"; do
    printf '%s\n' ".claude/$d"
    real=$(cd "$REPO/.claude/$d" 2>/dev/null && pwd -P) || continue
    case "$real" in
      "$REPO_REAL"/*) printf '%s\n' "${real#"$REPO_REAL"/}" ;;
      *) printf '/%s\n' "$real" ;;   # outside the repo: absolute rule (//path)
    esac
  done | sort -u
}
deny() { while read -r t; do for tool in Read Grep Glob; do
  case "$t" in /*) printf ',%s(/%s/**)' "$tool" "$t" ;; *) printf ',%s(./%s/**)' "$tool" "$t" ;; esac
done; done; }

ON="Read,Grep,Glob,Skill"; OFF="Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch"; EXTRA=(); HIDDEN=""
if [ -n "$AGENT" ]; then
  if [ "$V" = with ]; then EXTRA=(--agent "$AGENT")
  else HIDDEN=$(targets agents); OFF="$OFF,Agent,Task$(printf '%s\n' "$HIDDEN" | deny)"; fi
elif [ "$V" = without ]; then
  # the Agent/Task tool could load an agent body (and its skills) without any Read
  HIDDEN=$(targets skills agents); ON="Read,Grep,Glob"; OFF="Skill,Agent,Task,$OFF$(printf '%s\n' "$HIDDEN" | deny)"
fi

OUT="$EVAL/out/$ID-$V-$R.json"
# hidden paths, for grade.py's leak check
# first line = the repo (relative tool paths resolve against it), then the hidden paths
[ -n "$HIDDEN" ] && { echo "$REPO_REAL"; printf '%s\n' "$HIDDEN"; } > "$OUT.hidden"
# ${EXTRA[@]+...} keeps an empty array safe under set -u on bash 3.2 (macOS default)
(cd "$REPO" && claude -p "$P Answer in chat only. Do not edit or create files." --model "${MODEL:-sonnet}" \
  --output-format json --verbose --allowedTools "$ON" --disallowedTools "$OFF" ${EXTRA[@]+"${EXTRA[@]}"}) > "$OUT" 2> "$OUT.err"
