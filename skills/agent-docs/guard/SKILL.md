---
name: agent-docs-guard
description: Use when setting up checks that keep agent docs (AGENTS.md, CLAUDE.md, skills, subagents, Cursor rules) in sync with the code, when docs name files that were moved or deleted, or when a refactor or PR leaves skill text that contradicts the code.
---

# Agent docs guard

Agent docs go stale in two ways:
- **Dead paths:** a doc names a file that was moved or deleted. A script finds these and fails CI.
- **Content drift:** every path still exists, but the text is wrong. Example: a skill says "a limit of 25" and the code now says 50. Only a reviewer finds these, so add a rule to the AI PR review prompt.

This skill installs both into the user's repo. The files are in `templates/`, next to this file.

## Steps

1. **Look at the repo.**
   - Where do scripts live (`tools/`, `scripts/`, `bin/`)? Use that folder instead of `tools/` in every template.
   - Which CI does it use? The workflow template is for GitHub Actions. For other CI, run the same command in a PR job.
   - Where are the agent docs? The script checks `AGENTS.md` / `CLAUDE.md` anywhere, and `.md` / `.mdc` under `DOC_DIRS` (`.claude`, `.agents`, `.cursor`, `.github/instructions`). Add other doc folders to `DOC_DIRS`.
   - Does an AI PR review prompt exist (for example a Claude Code GitHub Action)?
2. **Copy the script** `templates/check-agent-docs.mjs` to the scripts folder. It needs Node 18+ and git, and no packages.
3. **Run it once:** `node <scripts>/check-agent-docs.mjs`. Show the dead paths to the user as a table: doc, path, the likely new file (search the repo for the file name).
   - A path that exists only at run time or on a dev machine (for example `.vscode/settings.json`) goes in `.agent-docs-ignore`, one per line.
   - Fix the rest only after the user agrees. Point the doc at the new file, or update the text around it.
   - Run it again until it prints `0 dead`.
4. **Ask before each of these changes** (AskUserQuestion, multi-select), because they change how the team works:
   - **CI job:** copy `templates/agent-docs-check.yml` to `.github/workflows/`. Fix the script path. Use the Node version the repo already uses.
   - **Review rule:** paste `templates/review-drift-rule.md` into the AI PR review prompt. Change the doc folders and the comment format to match that prompt.
   - **CLAUDE.md rule:** add `templates/claude-md-rule.md` to the root `CLAUDE.md` (or `AGENTS.md`). Fix the script path.
5. **Check the warn mode** on a branch: `node <scripts>/check-agent-docs.mjs --changed origin/<default-branch>`. If the branch changes a file that a doc names, it prints a `::warning`.

## Optional: one-time drift scan

Dead paths are only part of the problem. To find content drift that is already in the docs:
- Send one subagent per skill. Each one lists every concrete claim (name, path, constant, route, command, version) and checks it against the code.
- Re-check each drift yourself before you fix it. Audit agents make mistakes.
- When you fix a doc, make it harder to break the next time:
  - Point to the file and symbol. Do not copy signatures or long code blocks.
  - Do not write exact versions, ports or limits that the code already holds.

To decide whether a doc is needed at all, use the `agent-docs-audit` skill.

## How the script decides

- A **ref** is a backticked relative path with a folder and a known extension, for example `` `src/api/router.ts` ``. Plain text paths are not checked.
- A path next to the doc (for example a skill's `references/x.md`) resolves there first. Otherwise it matches as a suffix of any tracked file, so `api/router.ts` matches `services/billing/api/router.ts`. `/.../` matches any depth.
- **Dead:** no tracked file matches. The script exits with 1.
- **Warn** (`--changed <base>`): the PR changes a file that a doc names and does not change that doc. A ref that matches several files is a convention, not one file, so it does not warn.
- Symlinked docs (for example `AGENTS.md -> CLAUDE.md`) count once, by their real path.
