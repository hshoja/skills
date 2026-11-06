# agent-docs-audit

A Claude Code skill that answers one question with evidence: **does this skill, subagent or CLAUDE.md actually help, or does the agent do just as well by reading the code?**

It audits agent docs claim by claim, then runs real tasks WITH and WITHOUT them and grades the answers. It proposes what to keep, trim, fix or delete, and after you approve, it re-tests the slim version to show nothing broke.

## Why

Agent docs grow and go stale. Some teammates say models read the code, so skills are not needed. Both sides are partly right:

- A fact that every nearby file shows (for example "all controllers use `validate()`") adds nothing.
- A rule that the code does not show (for example "write the integration test first and cover 401/403/404") can change the result. In one audit it was 3/3 with the skill vs 0/3 without.
- A good trigger matters as much as the content. One task went from 1/3 to 3/3 only because the rewritten description made the skill load.

## What it does

0. Asks you for the scope, budget, model and deliverable.
1. Maps the area to its docs, and keeps the always-loaded `CLAUDE.md` files as a reference layer.
2. Sends a subagent to list every claim and to find where else each one lives: `claudemd`, `code`, `spread`, `generic`, `nowhere`, `dup` or `stale`.
3. Writes task prompts only for the claims that only the docs know, plus a few for claims it plans to drop.
4. Runs each prompt WITH and WITHOUT the docs (3 runs each, by default). WITHOUT cannot load the docs in any way: no Skill tool, no Agent tool, and no reads of the doc folders or their symlinked real paths.
5. Grades by regex, then checks every fail by hand.
6. Proposes changes, and stops for your approval.
7. Edits, re-runs everything, and prints an old vs new, WITH vs WITHOUT table.

For docs that load in every session (`CLAUDE.md`, `AGENTS.md`), WITH/WITHOUT does not apply. `scripts/run_versions.sh` runs the same tasks on the old and the new commit instead.

## Install

```bash
claude plugin marketplace add hshoja/skills
claude plugin install agent-docs@hshoja
```

Or install only this skill:

```bash
git clone --depth 1 https://github.com/hshoja/skills /tmp/hshoja-skills
cp -r /tmp/hshoja-skills/skills/agent-docs/audit ~/.claude/skills/agent-docs-audit
```

Then, in any repo, ask Claude Code: *"audit the agent docs for the payments service"*, or *"run agent-docs-audit on the frontend skills"*.

Requirements: the `claude` CLI on PATH, `git`, `python3` (3.9+), and `bash`.

## Cost

Each test run costs about $0.10-0.40. A standard audit (11 cases x 2 variants x 3 runs, twice) is about 130 runs, or $15-40. A triage pass (1 run per variant) costs about a third of that, but it only ranks candidates and gives no verdict.

## Scripts

Run them from an eval folder outside the repo. `SKILL` is this skill's folder (in the plugin, under `~/.claude/plugins/`):

```bash
cp $SKILL/scripts/make_cases.py .   # edit CASES, then:
python3 make_cases.py
REPO=~/src/app-worktree bash $SKILL/scripts/run_all.sh 3
python3 $SKILL/scripts/grade.py <case> --why
python3 $SKILL/scripts/compare.py ../round1 ../round2 --md
```

## Limits

- Read-only answers. The agent cannot run tests, so it gets no feedback from them.
- Only large, consistent gaps count. A one-run gap out of 3 is noise.
- The reference layer (`CLAUDE.md`) is not under test, because it loads in both variants.

## License

MIT
