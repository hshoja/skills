# Grading

## Read every fail

For every FAIL:
1. `python3 scripts/grade.py <case> --why` names the missing lookahead and shows whether the fail regex hit.
2. Read the answer around it:
   ```
   python3 -c "import json,sys;print(next(i for i in json.load(open(sys.argv[1])) if i.get('type')=='result')['result'])" out/<case>-<variant>-<n>.json
   ```
3. **If the answer is right**, widen the regex in `make_cases.py`, regenerate `cases.tsv`, and re-grade. Write down each change for the report.
4. **If the answer is wrong**, keep the FAIL and quote one line of it in the report.
5. **If the answer falls into a trap** that a line you plan to drop warns against, mark that line keep.
6. **If the answer stopped to ask a question** about a prompt that does not fit the code, the prompt is wrong. Fix the prompt for the next round, and report the run as "prompt issue", not as a fail.

## What grade.py prints per run

- `skill=[...]`: the skills the run loaded with the Skill tool. In a WITH run, an empty list means the trigger did not fire.
- `LEAK`: a WITHOUT run read a hidden doc (paths are resolved, so `.agents/skills` counts when `.claude` links to it) and the call was not denied. Do not count it. Find out how it got around the deny rules. Reads of user-level `~/.claude/skills` are not leaks.
- `INCOMPLETE`: the run crashed or is still running. `run_case.sh` reruns it.
- `NO-TOOLS`: the run answered from memory with 0 tool calls. A WITHOUT run with no Skill tool does this more often, so a gap made of `NO-TOOLS` runs is a harness effect. Report it apart.
- A denied `Glob` or `Grep` returns "No files found" instead of an error. `grade.py` does not count that as a leak.

## What counts as an effect

- With 3 runs, only a gap of 2 or more runs is an effect (for example 3/3 vs 0-1/3).
- A one-run gap is "weak". Keep the claim only if it is short.
- The WITHOUT side does not change between rounds. If WITHOUT moves a lot from round 1 to round 2, that is the noise level.
- Report cost per run together with turns. A higher WITH cost after a trigger fix is expected, because the skill loads more often.
