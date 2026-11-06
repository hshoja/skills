# Skills

Personal agent skills.

## Install (Claude Code)

```bash
claude plugin marketplace add hshoja/skills
claude plugin install hshoja-skills@hshoja
```

## Skills

- [macos-disk-cleanup](skills/macos-disk-cleanup/SKILL.md) - full macOS disk audit. Scans all major dirs, including hidden dot dirs, and outputs a prioritized cleanup table with exact commands.
- [macos-cpu-cooling](skills/macos-cpu-cooling/SKILL.md) - interactive CPU hog hunt. Shows a process table (PID, CPU%, MEM%, category, plain-English description), asks what to do per process, and repeats until the Mac is cool.
