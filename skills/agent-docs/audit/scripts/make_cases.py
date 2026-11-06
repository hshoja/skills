"""Copy this file into your eval folder, edit CASES, run it: python3 make_cases.py -> cases.tsv

Each case: (id, agent, prompt, pass_regex, fail_regex)
- agent "" = skill case (WITH = Skill tool on, WITHOUT = off and skill files unreadable)
- agent "<name>" = agent case (WITH = claude --agent <name>, WITHOUT = plain run)
- one (?=.*X) lookahead per required fact; start with (?is); keep the fail regex aimed at the wrong answer only.
See references/test-design.md.
"""
CASES = [
    # Example skill case: the migration flow of a service that gates startup on a schema version.
    ("migrate", "",
     "Add a nullable archived_at column to the orders table in the billing service. "
     "List every file I must change and every command I must run, in order, so the service starts and tests pass.",
     r"(?is)^(?=.*db_generate)(?=.*db_migrate)(?=.*expected_?version)",
     r""),
    # Example agent case: reuse a skill prompt, run with --agent.
    ("agent-migrate", "billing-agent",
     "Add a nullable archived_at column to the orders table in the billing service. "
     "List every file I must change and every command I must run, in order, so the service starts and tests pass.",
     r"(?is)^(?=.*db_generate)(?=.*db_migrate)(?=.*expected_?version)",
     r""),
]

if __name__ == "__main__":
    import re
    with open("cases.tsv", "w") as f:
        for row in CASES:
            assert len(row) == 5, row[0]
            assert not any("\t" in x or "\n" in x for x in row), f"tab or newline in case {row[0]}"
            for pat in row[3:]:
                if pat:
                    re.compile(pat)
            f.write("\t".join(row) + "\n")
    print(f"{len(CASES)} cases -> cases.tsv")
