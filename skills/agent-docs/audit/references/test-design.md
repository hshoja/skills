# Test design

## Case file

`cases.tsv` holds one line per case, with 5 tab-separated columns. No tabs or newlines inside a field.

```
id <TAB> agent <TAB> prompt <TAB> pass_regex <TAB> fail_regex
```

- **Skill case** (`agent` empty): WITH = `Skill` tool on. WITHOUT = `Skill` and `Agent`/`Task` tools off, and `.claude/skills` and `.claude/agents` unreadable, including their real paths when `.claude` is a symlink.
- **Agent case** (`agent` = an agent name): WITH = `claude --agent <name>`. WITHOUT = a plain run with the `Agent`/`Task` tools off and `.claude/agents` unreadable. Skills stay on in both, so the test measures only the agent body.
- `run_one.sh` appends " Answer in chat only. Do not edit or create files." to the prompt.
- PASS = `pass_regex` matches and `fail_regex` (if not empty) does not.

Do not hand-edit the TSV. Copy `scripts/make_cases.py` into the eval folder, edit the list, and run it.

## Prompts

- **A real task, not a quiz.** "Add a column to the orders table and list every file and command" tests whether the agent knows the migration flow. "What is the migration flow?" tests recall only.
- **One prompt per group of related claims.** Typical size: 6-10 skill prompts, plus 3 agent prompts that reuse skill prompts.
- **Add 2-3 prompts for claims you will drop.** If WITHOUT passes them, dropping them is safe.
- **Fit the current code.** A prompt that names a path or route the code does not use makes good runs stop and ask, and then they fail. Prefer the task ("an endpoint that returns a user's report summary") over a hard-coded path.
- **One fact per required condition.** If a prompt needs 6 facts and the regex wants all 6, an answer that misses one unimportant fact fails. Require only the facts the docs teach.

## Regexes

- One `(?=.*X)` lookahead per required fact, so `grade.py --why` can name the missing one.
- Make lookaheads independent: one fact's words must not satisfy another lookahead. For example, `(?=.*per[- ]?replica)` plus a tag check that also accepts "per" passes on the pattern name alone.
- Start with `(?is)` (case-insensitive, `.` matches newlines).
- Allow variants:
  - quoting: `\"?schema2\"?\.`
  - naming: `(refreshTokenEncrypted|refresh_token_encrypted)`
  - phrasing: `(test[- ]?first|written\s+first|before\s+the\s+code)`
- A fail regex must hit only the wrong answer, not a sentence that explains why it is wrong. For example, `FROM user\.roles` also hits "without quotes, FROM user.roles fails". Anchor it to code: ```` ```sql\s*SELECT[^`]*FROM user\.roles ````.
- Accept several phrasings of one behavior: `(re-?read|read\s+back|GET[^.\n]{0,80}returns|row\.\w+\s*===)`.

## Old-vs-new cases

For docs that load in every session (`CLAUDE.md`, `AGENTS.md`) or a reference file they link, WITH/WITHOUT does not apply. Make two worktrees (the base commit and the edited branch) and run `scripts/run_versions.sh`. Write prompts the same way: a task where the old or the new text should change the answer. Link the same `node_modules` into both, so the agent can read package types on both sides.

## Size and cost

- Runs per round = cases x 2 variants x reps. Two rounds (before and after the edit) double it.
- Each run costs about $0.10-0.40 and takes 0.5-5 minutes. `JOBS=4` runs 4 cases at a time, which is 8-24 processes.
- With 1 run per variant (triage), only rank candidates. Verdicts need 3 or more runs.
