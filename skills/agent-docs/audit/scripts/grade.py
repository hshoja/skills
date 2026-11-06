"""Grade WITH/WITHOUT runs against cases.tsv.

CLI:  python3 grade.py <case-id> [--why] [--dir EVAL_DIR]
      --why prints, for each FAIL, the (?=...) lookaheads the answer missed and whether the fail regex hit.
Lib:  summarize(eval_dir, case_id) -> {"with": {...}, "without": {...}}   (used by compare.py)
"""
import glob, json, os, re, sys


def load_cases(eval_dir):
    with open(os.path.join(eval_dir, "cases.tsv")) as f:
        return {r[0]: r for r in (line.rstrip("\n").split("\t") for line in f) if r and r[0]}


def lookaheads(pattern):
    """Top-level (?=...) groups, so a FAIL can name the missing fact."""
    out, i = [], pattern.find("(?=")
    while i != -1:
        depth, j = 0, i
        while j < len(pattern):
            if pattern[j] == "\\":
                j += 2
                continue
            if pattern[j] == "[":  # skip a char class: its parens are literal
                j += 2 if pattern[j + 1:j + 2] != "^" else 3
                while j < len(pattern) and pattern[j] != "]":
                    j += 2 if pattern[j] == "\\" else 1
                j += 1
                continue
            depth += pattern[j] == "("
            depth -= pattern[j] == ")"
            if depth == 0 and pattern[j] == ")":
                break
            j += 1
        out.append(pattern[i + 3:j])
        i = pattern.find("(?=", j)
    return out


def hidden_dirs(run_path, agent):
    """Absolute real paths a WITHOUT run must not read, from <run>.json.hidden (written by run_one.sh)."""
    try:
        with open(run_path + ".hidden") as f:
            lines = [l.strip() for l in f if l.strip()]
    except OSError:
        return None, []
    repo, dirs = lines[0], []
    for t in lines[1:]:
        p = t if t.startswith("/") else os.path.join(repo, t)
        dirs += [p, os.path.realpath(p)]
    return repo, sorted(set(dirs))


def touches_hidden(tool_input, run_path, agent):
    """True if a tool call names a path inside a hidden dir (resolved, so .claude -> .agents counts)."""
    repo, dirs = hidden_dirs(run_path, agent)
    if repo is None:  # older runs without a .hidden file: plain substring check
        names = (".claude/agents",) if agent else (".claude/skills", ".claude/agents")
        return any(n in json.dumps(tool_input) for n in names)
    for key in ("file_path", "path", "pattern", "glob"):
        v = tool_input.get(key) if isinstance(tool_input, dict) else None
        if not isinstance(v, str) or not v:
            continue
        p = v if os.path.isabs(v) else os.path.join(repo, v)
        for cand in (os.path.normpath(p), os.path.realpath(p)):
            if any(cand == d or cand.startswith(d + os.sep) for d in dirs):
                return True
    return False


def grade_run(path, case):
    """One run file -> dict, or None when the run is incomplete."""
    _, agent, _, pre, fre = case
    try:
        with open(path) as f:
            items = json.load(f)
        res = next(i for i in items if i.get("type") == "result")
    except (ValueError, StopIteration, OSError):
        return None
    ans = res.get("result") or ""
    usage = res.get("usage", {})
    tools = [c for i in items if i.get("type") == "assistant"
             for c in i["message"]["content"] if c.get("type") == "tool_use"]
    skills = [c["input"].get("skill") for c in tools if c["name"] == "Skill"]
    touched = {c["id"]: c["name"] for c in tools if touches_hidden(c["input"], path, agent)}
    results = [c for i in items if i.get("type") == "user" and isinstance(i["message"]["content"], list)
               for c in i["message"]["content"] if c.get("type") == "tool_result"]
    # a leak = a call on hidden docs that was NOT denied. A denied Read returns is_error;
    # a denied Glob/Grep returns an empty result instead.
    empty = ("No files found", "No matches found")
    leak = "-without-" in os.path.basename(path) and any(
        r.get("tool_use_id") in touched and not r.get("is_error")
        and not (touched[r["tool_use_id"]] in ("Glob", "Grep") and json.dumps(r.get("content")).strip('"').startswith(empty))
        for r in results)
    passed = bool(re.search(pre, ans, re.S)) and not (fre and re.search(fre, ans, re.S))
    flags = "(?is)" if pre.startswith("(?is)") else ""
    missing = [] if passed else [x[:60] for x in lookaheads(pre) if not re.search(flags + x, ans, re.S)]
    return {
        "file": os.path.basename(path),
        "variant": "with" if "-with-" in os.path.basename(path) else "without",
        "pass": passed, "leak": leak, "skills": skills, "missing": missing, "tool_calls": len(tools),
        "fail_hit": bool(fre and re.search(fre, ans, re.S)),
        "turns": res.get("num_turns", 0), "cost": res.get("total_cost_usd", 0.0),
        "tokens_in": sum(usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
    }


def summarize(eval_dir, case_id, runs=None):
    """Aggregate per variant. LEAK and INCOMPLETE runs are excluded from the counts."""
    case = load_cases(eval_dir)[case_id]
    if runs is None:
        runs = [grade_run(p, case) for p in sorted(glob.glob(os.path.join(eval_dir, "out", f"{case_id}-*-*.json")))]
    agg = {}
    for r in runs:
        if r is None or r["leak"]:
            continue
        a = agg.setdefault(r["variant"], {"n": 0, "pass": 0, "loaded": 0, "notools": 0, "turns": 0, "cost": 0.0, "tokens_in": 0})
        a["n"] += 1; a["pass"] += r["pass"]; a["loaded"] += bool(r["skills"]); a["notools"] += r["tool_calls"] == 0
        a["turns"] += r["turns"]; a["cost"] += r["cost"]; a["tokens_in"] += r["tokens_in"]
    return agg


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    case_id, why = argv[1], "--why" in argv
    eval_dir = argv[argv.index("--dir") + 1] if "--dir" in argv else "."
    cases = load_cases(eval_dir)
    if case_id not in cases:
        sys.exit(f"unknown case {case_id!r}; known: {', '.join(cases)}")
    case = cases[case_id]
    files = sorted(glob.glob(os.path.join(eval_dir, "out", f"{case_id}-*-*.json")))
    if not files:
        sys.exit(f"no runs for {case_id!r} in {os.path.join(eval_dir, 'out')}")
    runs = []
    for path in files:
        r = grade_run(path, case)
        runs.append(r)
        if r is None:
            print(f"{os.path.basename(path):36} INCOMPLETE (crashed or still running; run_case.sh reruns it)")
            continue
        tag = "LEAK" if r["leak"] else ("PASS" if r["pass"] else "FAIL")
        memo = " NO-TOOLS (answered from memory)" if r["tool_calls"] == 0 else ""
        print(f"{r['file']:36} {tag} turns={r['turns']:<3} cost={r['cost']:.3f} in={r['tokens_in'] // 1000}k skill={r['skills']}{memo}")
        if why and not r["pass"]:
            print(f"    missing: {r['missing'] or ['(whole pattern)']}  fail-regex hit: {r['fail_hit']}")
    leaks = sum(1 for r in runs if r and r["leak"])
    for v, a in summarize(eval_dir, case_id, runs).items():
        n = a["n"]
        print(f"{case_id} {v:8} pass={a['pass']}/{n} skill-loaded={a['loaded']}/{n} avg turns={a['turns'] / n:.1f} "
              f"cost=${a['cost'] / n:.3f} in={a['tokens_in'] / n / 1000:.0f}k" + (f" no-tools={a['notools']}/{n}" if a["notools"] else "")
              + (f" (excluded {leaks} LEAK)" if leaks and v == "without" else ""))


if __name__ == "__main__":
    main(sys.argv)
