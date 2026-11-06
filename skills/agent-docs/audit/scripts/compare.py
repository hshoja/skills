"""compare.py <round1-eval-dir> <round2-eval-dir> [--md]

Round 1 = current docs, round 2 = edited docs. Prints, per case:
A = round 1 WITH, B = round 1 WITHOUT, C = round 2 WITH, D = round 2 WITHOUT,
plus skill-loaded counts and cost per WITH run. B vs D shows the noise (the WITHOUT side never sees the docs).
--md prints a markdown table for the report.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import load_cases, summarize  # noqa: E402


def cell(agg, v):
    a = agg.get(v)
    return (f"{a['pass']}/{a['n']}", a) if a else ("-", None)


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    r1, r2, md = argv[1], argv[2], "--md" in argv
    c1, c2 = load_cases(r1), load_cases(r2)
    ids = [c for c in c2 if c in c1]
    only = [c for c in c2 if c not in c1] + [c for c in c1 if c not in c2]
    if only:
        print(f"note: cases in only one round are left out: {', '.join(only)}\n")
    rows, tot = [], {k: [0, 0] for k in "ABCD"}
    cost = {"A": [0.0, 0], "C": [0.0, 0], "B": [0.0, 0], "D": [0.0, 0]}
    for cid in ids:
        s1, s2 = summarize(r1, cid), summarize(r2, cid)
        cells = {}
        for key, agg, v in (("A", s1, "with"), ("B", s1, "without"), ("C", s2, "with"), ("D", s2, "without")):
            text, a = cell(agg, v)
            cells[key] = (text, a)
            if a:
                tot[key][0] += a["pass"]; tot[key][1] += a["n"]
                cost[key][0] += a["cost"]; cost[key][1] += a["n"]
        load = lambda a: f"{a['loaded']}/{a['n']}" if a else "-"
        per = lambda a: f"${a['cost'] / a['n']:.2f}" if a else "-"
        rows.append([cid, cells["A"][0], cells["B"][0], cells["C"][0], cells["D"][0],
                     f"{load(cells['A'][1])} / {load(cells['C'][1])}", f"{per(cells['A'][1])} / {per(cells['C'][1])}"])
    head = ["case", "A old WITH", "B old WITHOUT", "C new WITH", "D new WITHOUT", "skill loaded A / C", "cost/run A / C"]
    total = ["total"] + [f"{tot[k][0]}/{tot[k][1]}" for k in "ABCD"] + ["", ""]
    if md:
        print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
        for r in rows + [total]:
            print("| " + " | ".join(r) + " |")
    else:
        w = [max(len(str(x)) for x in col) for col in zip(head, *rows, total)]
        for r in [head] + rows + [total]:
            print("  ".join(str(x).ljust(n) for x, n in zip(r, w)))
    avg = {k: (v[0] / v[1] if v[1] else 0.0) for k, v in cost.items()}
    if avg["A"] and avg["B"]:
        print(f"\nWITH cost per run: ${avg['A']:.3f} -> ${avg['C']:.3f} ({(avg['C'] / avg['A'] - 1) * 100:+.0f}%). "
              f"WITHOUT drift (noise): ${avg['B']:.3f} -> ${avg['D']:.3f} ({(avg['D'] / avg['B'] - 1) * 100:+.0f}%).")


if __name__ == "__main__":
    main(sys.argv)
