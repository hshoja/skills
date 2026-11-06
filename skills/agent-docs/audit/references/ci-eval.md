# Optional: CI regression eval

An audit answers a one-time question: is this doc needed at all? CI answers a different question: did this edit break what the doc teaches? For that, you need only the WITH side.

## Shape

- **Trigger:** a pull request that changes the skill directory, or the `CLAUDE.md` lines that point to it.
- **Runs:** each kept case, WITH only, 3 runs. The case passes at 2/3 or more. Store the minimum per case in a small expected-results file.
- **Output:** a PR comment with per-case pass rate, skill-loaded count and average cost. Report only, at first. Make it blocking only after a few weeks of stable results.
- **Auth:** a Claude Code OAuth token or API key as a repository secret. Skip forks, which get no secrets.
- **Cost:** about cases x 3 x $0.25 per triggering PR.

## Upkeep

- Prompts go stale when the code changes, for example a renamed route. Phrase prompts by task, and update them in the same PR as the code change.
- Re-run the full WITH/WITHOUT audit when the skill grows a lot. CI does not tell you whether new content is needed.
