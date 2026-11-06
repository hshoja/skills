---
name: agent-docs-audit
description: Use when deciding whether to keep, trim, fix or delete agent docs for one area of a repo (Claude Code skills, subagents in .claude/agents, CLAUDE.md or AGENTS.md files), when agent docs feel bloated or stale, or when someone argues that agents do not need skills because they can read the code.
---

# Agent docs audit

Agent docs earn their place only with knowledge that the code and the always-loaded `CLAUDE.md` files do not already give. Prove this claim by claim, with WITH/WITHOUT runs of real tasks. Then propose changes, and edit only after the user approves.

The output is a per-claim keep/drop decision, backed by pass counts, and a before/after re-test that shows nothing broke.

## Step 0: ask the user

First, find the areas yourself (step 1, discovery). Then ask one question set (`AskUserQuestion` in Claude Code, which allows at most 4 options per question):

1. **Scope:** offer the 3 areas with the most doc lines, and "Other" for the rest. An area is a set of skills and agents that a `CLAUDE.md` pointer, an agent's skill list, or a shared directory ties together.
2. **Budget:** each run costs about USD 0.10-0.40.
   - **Triage** (1 run per variant): finds candidates only, and gives no keep/drop verdict.
   - **Standard** (3 runs): the verdict table below applies.
   - **Thorough** (5 runs).
   - Show the estimate: cases x 2 variants x runs x 2 rounds.
3. **Model** for the test runs (default: the mid model, for example `sonnet`).
4. **Deliverable:** a chat summary, or a markdown report file (the user can publish it anywhere).

If the scope has docs that are not skills or agents (`CLAUDE.md`, `AGENTS.md`, a reference file they link), say how they will be tested: **old-vs-new runs** (`scripts/run_versions.sh`, plain runs on the old and the new commit) or **audit only**. Recommend old-vs-new for any file you plan to delete or cut by more than half: an audit-only cut is the first thing a reviewer questions.

## Steps

1. **Scope and baseline** (`references/discovery.md`).
   - Find every doc in the area, including symlinked folders (for example `.claude -> .agents`), nested `.claude/` folders, and nested `SKILL.md` files. Note plugin and user-level skills that show in the WITH catalog.
   - List line counts in 3 groups:
     - **docs under test**
     - **reference layer:** the files that actually load. The root `CLAUDE.md` always loads. A nested `CLAUDE.md` loads only when the agent reads a file in that folder. An `AGENTS.md` loads only through a `CLAUDE.md` symlink or import.
     - **related docs**
   - Run `git log --follow` on real paths, not symlinked ones, to see recent cuts and moves.
   - Create a worktree outside the repo, from the branch the team ships from (ask if `HEAD` is on another branch). Record `git rev-parse HEAD`.
2. **Claim audit (subagents).** Send `references/audit-prompt.md`. If the scope has more than about 600 lines, use one subagent per skill, in parallel. Spot-check every `nowhere` row and 2-3 `stale` rows with your own grep.
3. **Design tests** (`references/test-design.md`). Test `nowhere`/`spread` claims, `code` claims that a stale doc contradicts, and 2-3 claims you plan to drop. Use about one prompt per 3-5 unique claims, with at most 4 per skill. Write all cases before any run, and check each prompt against the current code.
4. **Run round 1** on the current docs: `bash scripts/run_all.sh <runs>` from an eval folder, with `REPO=<worktree>`. Use the same machine and setup for both rounds: user-level `CLAUDE.md`, plugins, hooks and MCP servers load in both variants and differ per machine.
5. **Grade** (`references/grading.md`). Run `python3 scripts/grade.py <case> --why`. Read every fail, and widen a regex only when the answer is right. Write down each change. Do not count a run marked `LEAK` or `INCOMPLETE`. Report runs marked `NO-TOOLS` (answered from memory) apart: a gap they cause is a harness effect, not a doc effect. Check that `HEAD` did not move.
   - Read the fails for traps: when a fail does exactly what a line you plan to drop warns against (for example it builds its own permission check), keep that line.
6. **Check triggers.** If the skill loaded in 0-1 of the WITH runs, the test measured the trigger, not the content. Report it separately. A bad trigger is a fix of its own.
7. **Propose, then stop** (`references/reporting.md`). Give one row per test, the keep/drop/fix/move list per file, the stale fixes, and the lines before and after, with the reference layer included. Ask for approval.
8. **After approval: edit and run round 2.**
   - Edit in the worktree.
   - Re-run every case into a new eval folder.
   - Compare with `python3 scripts/compare.py <round1-dir> <round2-dir>`.
   - Done = no test drops by more than one run, the tests on dropped content still pass, and the slim WITH still beats WITHOUT where it did before.
9. **Scope check and pointers, before you commit.**
   - Every kept rule must be true in every directory its trigger covers. Example: a rule "never return error JSON" that one service breaks at 17 call sites is false. Limit it to the service where it holds, or delete it.
   - Before you drop a "stale" rule, split its counts by file type, folder and app. A rule that fails overall often holds in a subset ("use `undefined`, not `null`" holds in props, not in API types; "`function` declarations" holds in client modules, not in components). Scope it to that subset, and ask the user which convention the team wants for new code.
   - A claim the tests said to drop stays dropped in every layer. Do not move it into `CLAUDE.md`: that loads it into every session.
   - Links meant for people (Storybook, dashboards, wikis) go to a README, not to agent docs. Before you remove one, check that it exists somewhere people look.
   - Run the repo's dead-path check after deletes: a deleted file can expose an old broken link that matched it by suffix.
   - Update every reference-layer line that points to a changed skill or a deleted agent (for example "use the `@x-backend` agent").
   - Delete an agent that only points to skills. If you keep it for routing, list its skills in `skills: [a, b]` frontmatter instead of body text.
10. **Sync the deliverables after every change.** Each follow-up fix (review points, user questions) changes the numbers: update the PR body, the report and the line totals in the same turn.
11. **Optional: a CI guard.** See `references/ci-eval.md`: WITH-only runs on PRs that change the skill, posted as a report.

## Verdict per claim (standard budget or higher)

| Result (3+ runs per variant) | Verdict |
|---|---|
| WITH clearly beats WITHOUT (3/3 vs 0-1/3) | keep |
| WITH beats WITHOUT by one run | keep if short, mark weak |
| tie, WITH >= 20% cheaper on 2+ tests | keep, trimmed to what saved time |
| tie, claim is in code or the reference layer | drop |
| WITH fails because the doc is wrong | fix or drop |
| claim is about writing docs, not the code | move to contributor docs |
| agent ties with the plain run | delete the agent, or keep only `skills:` frontmatter |

## Common mistakes

- **Trusting the regex:** often half of the first "fails" are grader errors, such as quoted names, snake_case vs camelCase, or "written first" vs "test first".
- **Hiding only the `Skill` tool:** a WITHOUT run then reads `SKILL.md` directly, through `Read`, through a symlinked real path (`.agents/skills/...`), or through the `Agent` tool. `run_one.sh` denies all three. `grade.py` resolves paths and marks any undenied read as `LEAK`.
- **Claiming the skill caused an answer** without checking `skill=[...]`.
- **Reading WITH cost alone:** with the `Skill` tool on, the skill catalog adds about 10k prompt tokens before any skill loads, and a better trigger loads the skill more often. Judge cost against the WITHOUT drift between rounds, which shows the noise.
- **A moving base:** an editor's auto-pull can fast-forward the worktree mid-test. `run_all.sh` warns when this happens.
- **Prompts that clash with the code** (a path the service does not use) make good runs stop and ask. Describe the task, not hard-coded paths.
- **Calling a one-run gap an effect,** or giving verdicts from a triage budget.
- **Leaving the reference layer out of the totals,** which makes the cut look bigger than it is.
- **Deleting a doc on audit alone.** A 498-line UI reference looked redundant in the audit. The old-vs-new test then showed it was worse than 5 short rules (2/15 vs 15/15). Test before you claim it.
- **Dropping a scoped convention as stale,** or moving a dropped claim into `CLAUDE.md` (see step 9).
- **Slimming a pass-through agent instead of deleting it.** If it ties with the plain run and nothing routes to it, delete it.

## Files

- `references/discovery.md`: how to find docs and the layers that load.
- `references/audit-prompt.md`: the claim-audit subagent prompt.
- `references/test-design.md`: the case format, prompt rules, and regex rules.
- `references/grading.md`: the hand-check routine and leak rules.
- `references/reporting.md`: the proposal and report templates.
- `references/ci-eval.md`: the optional regression eval in CI.
- `scripts/make_cases.py`: a case list template that writes `cases.tsv`.
- `scripts/run_one.sh`, `run_case.sh`, `run_all.sh`: the runners. They need `REPO`, and optional `MODEL` and `JOBS`.
- `scripts/run_versions.sh`: old-vs-new mode for docs that load in every session. It needs `REPO_OLD` and `REPO_NEW`.
- `scripts/grade.py`, `scripts/compare.py`: grading, and the round 1 vs round 2 table.

Run the scripts from an eval folder outside the repo (a scratch or temp directory). Example: `REPO=~/src/app-wt bash <skill-dir>/scripts/run_all.sh 3`, where `<skill-dir>` is this skill's base directory.
