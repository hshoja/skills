Agent docs drift: agents follow AGENTS.md, CLAUDE.md and every doc under `.claude/` (skills, subagents), so a doc this PR makes wrong is a bug.
- Take the names this PR changes or removes (files, exported functions, classes, routes, constants and their values, config keys) and grep those docs for them.
- Flag a doc only when its text contradicts the new code, and skip docs this PR already edits. Example: a skill says 'a limit of 25 entries' and the PR sets the limit to 50.
- Post it as a warning comment on the code line that makes the doc wrong; quote the doc as `path:line` plus the exact sentence, and say what it should say now. No comment for docs that are merely incomplete.
