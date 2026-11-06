# Discovery: find the docs and the layers that load

## Find every doc

Work from the repo root, and follow symlinks (`find -L`). Skip `node_modules`, `.git`, and worktree folders inside the repo (`.worktrees/`).

```bash
find -L . \( -name node_modules -o -name .git -o -name .worktrees \) -prune -o \
  \( -name SKILL.md -o -path '*/.claude/agents/*.md' -o -name CLAUDE.md -o -name AGENTS.md \) -print
ls -la .claude CLAUDE.md AGENTS.md 2>/dev/null     # symlinks? (e.g. .claude -> .agents, CLAUDE.md -> AGENTS.md)
```

Also note the skills that come from outside the repo. These are user-level skills (`~/.claude/skills`) and plugin skills. They show in the WITH catalog, and they can overlap with the docs under test.

## Which files load (the reference layer)

| File | Loads in Claude Code |
|---|---|
| root `CLAUDE.md` (or the file it links or imports) | always |
| user `~/.claude/CLAUDE.md` | always, on that machine only |
| nested `<dir>/CLAUDE.md` | only when the agent reads a file under `<dir>` |
| `AGENTS.md` | only if a `CLAUDE.md` is a symlink to it or imports it (`@AGENTS.md`) |
| skills | the description is always in the catalog; the body loads only when triggered |
| agents | only when called (`--agent`, the Agent tool, or the user) |

A nested `AGENTS.md` with no `CLAUDE.md` next to it never loads in Claude Code. Report that as a finding.

## Group into areas

An area is the skills and agents that belong together:
- **pointers:** a `CLAUDE.md` line that says "load skill X" or "use agent Y"
- **agent skill lists:** the `skills:` frontmatter, or body text such as "load these skills: ..."
- **paths:** the skill's description or examples name the same directory

When there are more than 3 areas, offer the 3 with the most lines in step 0, plus "Other".

## History

- `git log --follow -- <real path>`: use the real path, because a path through a symlink returns nothing.
- Note when a doc was moved (renames hide older history) or cut recently. A large recent cut changes what counts as "already known".

## Worktree

- Create it outside the repo (for example `../<repo>-wt-audit`), so that its `CLAUDE.md` files do not show up in searches of the main checkout.
- Base it on the branch the team ships from. If the user's `HEAD` is on a release branch, ask which one to audit.
