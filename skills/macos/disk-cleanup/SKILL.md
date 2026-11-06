---
name: macos-disk-cleanup
description: Use when macOS disk is full, running low on space, or user wants to audit disk usage. Scans home dir, hidden dot dirs, Application Support, Caches, Developer tools, and Applications, then outputs a prioritized table with exact cleanup commands.
---

# macOS Disk Cleanup Analysis

Run all scans in parallel, then synthesize into one sorted table with cleanup commands. Never delete anything without asking: the user picks which rows to clean.

## Scan Commands (run in parallel)

```bash
# 1. Actual disk usage (use Data volume, not /)
df -h /System/Volumes/Data

# 2. Top-level home (visible dirs)
du -sh /Users/$USER/* 2>/dev/null | sort -rh | head -20

# 3. Hidden dot dirs - frequently the biggest surprise, never skip
du -sh /Users/$USER/.* 2>/dev/null | sort -rh | head -25

# 4. Library subdirs
du -sh /Users/$USER/Library/* 2>/dev/null | sort -rh | head -15

# 5. Application Support
du -sh "/Users/$USER/Library/Application Support"/* 2>/dev/null | sort -rh | head -20

# 6. Caches
du -sh /Users/$USER/Library/Caches/* 2>/dev/null | sort -rh | head -15

# 7. Developer tools
du -sh /Users/$USER/Library/Developer/* 2>/dev/null | sort -rh

# 8. Installed apps
du -sh /System/Volumes/Data/Applications/* 2>/dev/null | sort -rh | head -15

# 9. Docker
docker system df 2>/dev/null

# 10. Trash, Downloads, sandboxed app data
du -sh ~/.Trash ~/Downloads 2>/dev/null
du -sh ~/Library/Containers/* ~/Library/Group\ Containers/* 2>/dev/null | sort -rh | head -10

# 11. iOS/iPadOS device backups
du -sh ~/Library/Application\ Support/MobileSync/Backup 2>/dev/null

# 12. Local Time Machine snapshots and purgeable space
tmutil listlocalsnapshots / 2>/dev/null
diskutil info /System/Volumes/Data | grep -iE 'free|purgeable'
```

## Output Format

Present as one table sorted by size descending:

| Location | Size | Safe? | Cleanup Command |
|----------|------|-------|-----------------|
| ~/.lmstudio | 46 GB | Yes if unused | `rm -rf ~/.lmstudio/models` |
| ... | | | |

## Clean Up

1. Ask which rows to clean (AskUserQuestion, multi-select). Put "Always safe" rows first.
2. Run only the commands for the chosen rows.
3. Re-run `df -h /System/Volumes/Data` and report what was freed, e.g. "Freed 38 GB (412 GB -> 374 GB used)".

## Safety Reference

**Always safe - auto-rebuilds:**
| Path | Command |
|------|---------|
| `~/Library/Caches/JetBrains` | `rm -rf ~/Library/Caches/JetBrains` |
| `~/Library/Developer/Xcode/DerivedData` | `rm -rf ~/Library/Developer/Xcode/DerivedData` |
| `~/Library/Developer/CoreSimulator` (stale) | `xcrun simctl delete unavailable` |
| `~/.gradle/caches` | `rm -rf ~/.gradle/caches` |
| `~/.npm` | `npm cache clean --force` |
| `~/Library/Caches/Yarn` | `yarn cache clean` |
| `~/Library/Caches/Coursier` | `rm -rf ~/Library/Caches/Coursier` |
| Homebrew | `brew cleanup --prune=all` |
| Docker images and build cache | `docker system prune -a` |
| pnpm store | `pnpm store prune` |
| Local Time Machine snapshots | `tmutil thinlocalsnapshots / 999999999999 4` (backups on the external disk stay) |

**Safe if app not actively used:**
- `~/.lmstudio` - LM Studio AI model weights (can be 10-50GB+)
- `~/Library/Application Support/rancher-desktop` - VM image
- `~/Library/Android` / `~/.android` - Android SDK
- `~/Library/Caches/ms-playwright` - Playwright browsers

**Re-syncs from cloud (safe to delete):**
- `~/Library/Application Support/Notion`
- `~/Library/Application Support/Slack` (partially)

**Do not delete without checking:**
- `~/Library/Application Support/Claude` - app state
- `~/.bun`, `~/.rustup`, `~/.dvm` - language toolchains (need reinstall)
- `~/Library/Developer/Xcode/iOS DeviceSupport` - check which iOS versions still needed
- Docker volumes (`docker system prune --volumes`) - hold container data such as local databases; list them first with `docker volume ls`
- `~/Library/Application Support/MobileSync/Backup` - only copy of a device backup unless it is also in iCloud
- `~/Downloads` - user files; show the biggest ones (`du -sh ~/Downloads/* | sort -rh | head`) and let the user pick
- `~/.Trash` - emptying it is permanent; the user empties it from Finder

## Key Pitfalls

- `df -h /` shows APFS volume, not actual disk use - always use `/System/Volumes/Data`
- Hidden dot dirs (`.lmstudio`, `.local`, `.android`) are invisible to `du -sh ~/*` - always run the `.*` scan separately
- Xcode iOS DeviceSupport and CoreSimulator together often exceed 15GB - always check both
- Without Full Disk Access for the terminal, `du` reports protected folders (Mail, Photos, Messages, some Containers) as small or gives "Operation not permitted". Say so in the table instead of reporting a wrong size
- "Purgeable" space and local snapshots show as used in `df` but macOS frees them on demand - report them on their own row
