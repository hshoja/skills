### Agent Docs

When you move, rename or delete a file, or change code that a skill or AGENTS.md describes, update that doc in the same PR.
`node tools/check-agent-docs.mjs` finds dead file paths in skills, agents and AGENTS.md. CI runs it and warns when a PR changes a file a doc names but not the doc.
