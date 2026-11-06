# Proposal and report

## Proposal (end of round 1: stop and ask)

1. **One sentence:** how many claims out of the total are unique, and how many are stale.
2. **Test table**, one row per case:

   | Test | Claims tested | WITH | WITHOUT | Skill loaded (WITH) | Verdict |
   |---|---|---|---|---|---|

3. **Per file:** keep / trim / delete, with the claim ids to keep.
4. **Stale fixes**, each with its code evidence (`path:line`).
5. **Lines before and after**, with the reference layer as its own row.
6. **Changes outside the docs under test**, such as `CLAUDE.md` pointers. Ask for approval of these separately.

## Final report (after round 2)

Readers want to know how the test worked and why each file was cut. In this order:

1. **Short answer:** the decision and the headline numbers, for example "31/33 vs 30/33, 1,209 -> 122 lines".
2. **Scope note:** which files were under test, which formed the reference layer, and the commit SHA.
3. **Method:** one diagram or 6 numbered steps: inventory, audit, tests, runs, grading, decision.
4. **Claim audit:** counts per class per file.
5. **Every test, precisely:** the full prompt, the claims tested, the pass rule in plain words, pass counts, skill loads, turns, cost.
6. **Round 1 vs round 2:** the 4-cell table from `compare.py`.
7. **Decision per file**, with the reason, for example "the agent tied with a plain run in both rounds".
8. **Limits:**
   - runs per variant
   - trigger misses
   - leaks found and fixed
   - prompts that did not fit the code
   - base moves during the runs
   - the cost change, with its cause
9. **How to reproduce:** the eval folder, the `cases.tsv` columns, and the scripts.

Write it for a reader who was not in the session. Put numbers in tables, not in prose.

## After follow-up changes

Review points and user questions change the docs after the report. After each change, update the PR body, add a short "Updates after review" list to the report, and fix every number it changes (line totals, verdicts, charts).
