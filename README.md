# Skills

Personal agent skills, grouped by topic under `skills/<group>/<skill>`. Each group is one plugin.

## Install (Claude Code)

Each group is its own plugin. Add the marketplace once, then install only the groups you need:

```bash
claude plugin marketplace add hshoja/skills
claude plugin install agent-docs@hshoja
claude plugin install macos@hshoja
```

One skill only: copy its folder into `~/.claude/skills/<skill-name>`. Example for `agent-docs-audit`:

```bash
git clone --depth 1 https://github.com/hshoja/skills /tmp/hshoja-skills
cp -r /tmp/hshoja-skills/skills/agent-docs/audit ~/.claude/skills/agent-docs-audit
```

## Agent docs (`agent-docs` plugin)

- [agent-docs-audit](skills/agent-docs/audit/SKILL.md) - checks if a skill, subagent or CLAUDE.md really helps. Runs real tasks WITH and WITHOUT the docs, grades the answers, and proposes what to keep, trim, fix or delete.
- [agent-docs-guard](skills/agent-docs/guard/SKILL.md) - keeps agent docs in sync with the code. Installs a CI check that fails on dead file paths in docs and warns when a PR changes a file a doc names, plus a drift rule for your AI PR review prompt.

## macOS (`macos` plugin)

- [macos-disk-cleanup](skills/macos/disk-cleanup/SKILL.md) - full macOS disk audit. Scans all major dirs, including hidden dot dirs, and outputs a prioritized cleanup table with exact commands.
- [macos-cpu-cooling](skills/macos/cpu-cooling/SKILL.md) - interactive CPU hog hunt. Shows a process table (PID, CPU%, MEM%, category, plain-English description), asks what to do per process, and repeats until the Mac is cool.
