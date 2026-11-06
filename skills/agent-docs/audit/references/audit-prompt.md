# Claim-audit subagent prompt

Send this to a general-purpose subagent. Fill in the `<...>` slots. It is read-only.

```
Read-only audit. Do not edit any file. Repo: <worktree path> at commit <sha>.

Goal: decide, claim by claim, what to keep in these agent docs:
- <docs under test: ONE skill (its SKILL.md and references/*.md) and the agents that load it.
   For a large scope, send one copy of this prompt per skill, in parallel.>

Reference layer (loads in every session, so a claim already there is not needed elsewhere):
- <root CLAUDE.md / AGENTS.md, nested CLAUDE.md for the area; note symlinks such as AGENTS.md -> CLAUDE.md>

A claim that is already in the reference layer, or plainly visible in a nearby file (a source, README, script or
config file in the directory the claim is about, or one an agent would open first for that task), does not need
to be in the docs under test. A claim that exists only in the docs is their real value.

For EVERY concrete claim (a fact, path, command, rule, port, pattern, convention, naming rule; skip generic
prose), output one row:
| id | file:line | claim (short) | where else (path:line, or "none") | class | verdict |
- id: <skill>/S1.. for SKILL.md, <skill>/<ref-file>/1.. for references, <agent>/A1.. for agents (unique across skills).
- class:
  claudemd  - already in the reference layer
  code      - one nearby source/config/README file shows it
  spread    - true, but only by combining 3+ files
  generic   - standard knowledge of the language/framework that any model has
  nowhere   - only in the docs under test
  dup       - the same claim in two docs under test (agent AND skill, or two skills)
  stale     - the code contradicts it: give the evidence path:line, and the counts split by file type,
              folder and app; if the rule holds in a subset, name the subset (scope it, do not drop it)
- verdict: drop | keep | fix | move-to-claudemd | move-to-contributor-docs (rules about writing the docs, not the code)
Router skills: a SKILL.md row that only points to its own reference file is not "dup"; class it by what the
reference says, and test the reference content.
Verify each claim in the code (grep/read). Do not trust the doc text.
For each rule, also check that it holds in EVERY directory the doc's trigger covers. A rule that one
service breaks is stale for that service: report it.

Then give:
1. Counts per class per file.
2. For every nowhere or spread claim, and for 2-3 claims you mark drop: one test prompt (a realistic task,
   phrased as a task and not as a quiz; it must fit the current code; the harness appends the read-only
   instruction, so do not add it), a PASS regex and a FAIL regex (Python re, matched with re.S on the answer). Use one
   (?=.*X) lookahead per required fact. Be tolerant of quotes, casing and snake/camel case. Group related
   claims in one prompt. Aim for 6-10 prompts.
3. For each agent: which parts of its body are not in any skill (these are lost if the agent is deleted).
4. Pointers: every line in the reference layer that tells the reader to load these docs. Quote it.

Output markdown only, no preamble. Keep claim text short.
Write your output to <file> early and update it after each doc, so a dropped connection loses little work.
```

## Reading the result

- Sum `nowhere` and `spread` per file. A file with 0 is a delete candidate even before any test.
- Re-check each `nowhere` claim with one grep of your own. Audit agents miss files.
- Check 2-3 `stale` rows yourself.
- The reference layer is not under test, because it loads in both variants. To test it, run a third variant in a temporary copy of the repo without that file.
