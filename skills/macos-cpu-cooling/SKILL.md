---
name: macos-cpu-cooling
description: Use when a Mac laptop is hot, fans are loud, CPU is pegged, battery drains fast, or system is sluggish and you need to find and stop the processes responsible.
---

# Cooling a Hot Mac

## Overview

Interactive loop: find CPU hogs one round at a time, identify each one, ask the user what to do with it, act, re-check. Repeat until cool. Never kill anything without asking.

## The Loop

1. **Measure** — run both commands and enrich into a table:

```bash
ps -eo pid,ppid,pcpu,pmem,comm | sort -k3 -rn | head -15
```

Then for each PID above ~20% CPU, fetch the full command:
```bash
ps -p <PID> -o pid,ppid,pcpu,pmem,command
```

2. **Present a rich table to the user** — render as markdown before asking anything:

| PID | CPU% | MEM% | Name | Full Path / Command | PPID | Category | What it does |
|-----|------|------|------|---------------------|------|----------|--------------|
| … | … | … | … | … | … | OS daemon / App / Orphan / Security agent | one-line human description |

- **Category** — classify using Identification Hints below
- **What it does** — plain-English description (e.g. "Spotlight indexing your SSD", "Orphaned webpack watcher from a closed terminal", "Chrome renderer for a heavy tab")
- If unclear, run `lsof -p <PID> | head -20` to see what files it's touching and infer purpose

3. **Ask the user per process** (AskUserQuestion), presenting what you learned. Options depend on type:
   - **Kill** - orphans, stray user processes: `kill <PID>` (escalate to `kill -9` if it survives)
   - **Disable + kill** - launch-agent-managed daemons that respawn: `launchctl disable gui/$(id -u)/<label> && kill <PID>` (find label via `launchctl list | grep -i <name>`)
   - **Stop via its own tooling** - apps with managed lifecycles (VMs, container runtimes, sync clients): use the app's own CLI/menu shutdown, not `kill`; check `<tool> --help` first, subcommand names vary
   - **Pause** - `kill -STOP <PID>` drops it to 0% CPU without losing its progress; `kill -CONT <PID>` resumes. Best for indexers mid-job: killing them restarts the work from scratch
   - **Leave it** - MDM/corporate-managed security agents (can't signal them - "Not privileged"), OS indexing that finishes on its own, work the user knows about
4. **Re-measure** — re-run step 1, rebuild and re-render the table. New hogs often surface once the top one dies — queued work gets its turn.
5. **Repeat** until no process exceeds ~20% at idle or user is satisfied.

## Identification Hints

| Signal | Likely meaning |
|--------|---------------|
| PPID 1 + path under a project's `node_modules`/build dir | Orphaned dev worker - safe to kill |
| Path under `/System/Library/PrivateFrameworks` | OS daemon (indexing, media analysis) - disable via launchctl or wait |
| Path under `/Library/SystemExtensions` | Security/MDM agent - can't stop, wait it out |
| Hypervisor process (qemu, vz, hyperkit) | VM burns CPU even with zero containers/guests running - stop via its app |
| Browser "Helper (Renderer)" | Heavy tab - user closes tabs |

## Digging Deeper

- **What is a daemon actually doing?** `/usr/bin/log show --last 3m --predicate 'process == "<name>"'` - full path required, zsh's `log` builtin shadows it. Log task names reveal the real work (e.g. OCR passes vs photo indexing) and errors like "library is in trash".
- **Root cause beats whack-a-mole**: for daemons chewing on data (photo/media indexers), removing the unused data source ends it permanently; killing the daemon just restarts the job.
- **Privacy-protected paths lie to the shell**: Photos libraries, Mail, Messages data give "Operation not permitted" for `du`/`rm`, and `ls` shows them as *empty when they aren't*. Empty `ls` ≠ deleted. The user must delete via Finder (`open <folder>` to help them there).
- **Trash isn't gone**: daemons keep working on files sitting in the Trash - `lsof` still shows them open. The fix isn't done until the user empties the Trash.

## Temps (optional)

`sudo powermetrics --samplers smc -n 1` - needs sudo from an interactive terminal; suggest the user runs it themselves. Third-party tools (istats, osx-cpu-temp) usually aren't installed.

## Common Mistakes

- `ps aux --sort=-%cpu` - GNU flag, fails on macOS; pipe through `sort -k2 -rn`
- Killing a launch-agent daemon without `launchctl disable` first - it respawns immediately
- Expecting `launchctl disable`/`bootout` to stop SIP-protected OS daemons (paths under `/System/`) - bootout returns "Operation not permitted", disable doesn't prevent on-demand relaunch, and they survive `kill -9` by respawning. Only real options: wait for them to finish, or turn off the OS feature feeding them (e.g. iCloud/Photos sync settings)
- `launchctl kill` on system services - "Not privileged"; plain `kill <PID>` works
- Assuming an idle VM costs nothing - hypervisor overhead is real
- Guessing a tool's shutdown subcommand - check `--help`, names vary per tool
- Acting on a process without asking the user - always confirm per process
