"""C1: a universal, label-free agreement table learned WITHOUT DEV.
Item pattern = the equality structure of four answers: A (assembled), D (assembled's draft = a sample of the program),
R (the program's own output, an independent sample), L (liquid agent), after liveness / checker filtering.
On PARETO+FIT pooled over all cells (leave-one-dataset-out), estimate P(correct) of choosing A, R, L per pattern; the
table maps each pattern to the form with the best pooled accuracy (default A when support is small or the edge is not
clear). Then: policy TAB on DEV (post hoc), NI rule with prior TAB."""
import json, math, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2

USE_V = len(sys.argv) > 1 and sys.argv[1] == "V"


def pattern4(it):
    ft = it.get("ft")
    if not ft:
        return "NOFEAT"
    alive = vf_alive(it) if USE_V else it["alive"]
    k = ft["k"]
    vals = {"A": k.get("assembled") if "assembled" in alive else None,
            "D": ft.get("draft_k") if "assembled" in it["alive"] else None,
            "R": k.get("rigid") if "rigid" in alive else None,
            "L": k.get("liquid") if "liquid" in alive else None}
    groups, dead = [], []
    for name in ("A", "D", "R", "L"):
        v = vals[name]
        if v is None:
            if name != "D":
                dead.append(name)
            continue
        for g in groups:
            if g[0] == v:
                g[1].append(name)
                break
        else:
            groups.append([v, [name]])
    s = "|".join("=".join(g[1]) for g in groups)
    if "D" not in s:
        s += "/noD"
    return s + ("/dead:" + "".join(dead) if dead else "")


FORM = {"A": "assembled", "R": "rigid", "L": "liquid"}


def learn(cells, min_n=25, z=1.0):
    """pattern -> form letter, from PARETO+FIT of `cells` (macro-weighted by item)."""
    st = {}
    for c in cells:
        for it in items_of(c, ("PARETO", "FIT")):
            p = pattern4(it)
            a = st.setdefault(p, {"n": 0, "A": 0.0, "R": 0.0, "L": 0.0, "dA_R": [], "dA_L": []})
            a["n"] += 1
            for x in "ARL":
                a[x] += it["s"][FORM[x]]
            a["dA_R"].append(it["s"]["rigid"] - it["s"]["assembled"])
            a["dA_L"].append(it["s"]["liquid"] - it["s"]["assembled"])
    table = {}
    for p, a in st.items():
        choice = "A"
        if "dead" in p and "A" in p.split("/dead:")[-1]:
            choice = "R" if "R" not in p.split("/dead:")[-1] else "L"
        if a["n"] >= min_n:
            best, bz = None, 0.0
            for x, key in (("R", "dA_R"), ("L", "dA_L")):
                d = a[key]
                m = sum(d) / len(d)
                sd = math.sqrt(sum((v - m) ** 2 for v in d) / max(1, len(d) - 1))
                se = sd / math.sqrt(len(d)) if sd > 0 else 1e-9
                if m > 0 and m / se > max(z, bz):
                    best, bz = x, m / se
            if best:
                choice = best
        table[p] = choice
    return table, st


def tab_form(it, table):
    p = pattern4(it)
    x = table.get(p)
    alive = vf_alive(it) if USE_V else it["alive"]
    if x is None:
        return live(it, "assembled", alive)
    f = FORM[x]
    return f if f in it["alive"] else live(it, "assembled", alive)


# the pooled table (all cells), for display
table, st = learn(MAIN)
print("pattern (A=reviewer, D=its draft, R=program, L=agent) | n(P+F) | acc A R L | choice     [pooled over 36 cells, PARETO+FIT only]")
for p, a in sorted(st.items(), key=lambda x: -x[1]["n"]):
    if a["n"] >= 15:
        print(f"  {p:28s} {a['n']:5d} | {a['A']/a['n']:.3f} {a['R']/a['n']:.3f} {a['L']/a['n']:.3f} | {table[p]}")
# the same statistics on DEV (never used to build the table) for a sanity look
sd = {}
for c in MAIN:
    for it in c["roles"]["DEV"]:
        a = sd.setdefault(pattern4(it), [0, 0.0, 0.0, 0.0])
        a[0] += 1
        for i, x in enumerate("ARL"):
            a[i + 1] += it["s"][FORM[x]]
print("\nDEV check of the same patterns (not used for the table):")
for p, a in sorted(sd.items(), key=lambda x: -x[1][0]):
    if a[0] >= 15:
        print(f"  {p:28s} {a[0]:5d} | {a[1]/a[0]:.3f} {a[2]/a[0]:.3f} {a[3]/a[0]:.3f} | table: {table.get(p)}")

# LODO: the table for dataset X is learned from the PARETO+FIT of all OTHER datasets (so it is task-agnostic)
res = {}
for mode in ("lodo", "pooled"):
    for c in CELLS:
        t = learn([x for x in MAIN if x["ds"] != c["ds"]])[0] if mode == "lodo" else table
        for role in ("PARETO", "FIT", "DEV"):
            for it in c["roles"][role]:
                it["tab_" + mode] = tab_form(it, t)

_psc = fa_lib2.psc


def psc2(it, name):
    if name.startswith("TAB:"):
        return it["s"][it["tab_" + name[4:]]]
    return _psc(it, name)


fa_lib2.psc = psc2
for mode in ("lodo", "pooled"):
    summarize({cid(c): "TAB:" + mode for c in MAIN}, f"always TAB ({mode} table)")
    for z1 in (0.5, 1.0, 1.28):
        sel = {}
        for c in CELLS:
            m, se = fa_lib2.pstats(items_of(c, ("PARETO", "FIT")), "TAB:" + mode, "rigid")
            sel[cid(c)] = ("TAB:" + mode) if m + z1 * se >= 0 else "rigid"
        summarize(sel, f"NI prior=TAB({mode}) z1={z1}")
        if z1 == 1.0:
            keep = dict(sel)
            print("     per cell:", " ".join(f"{k.split(':')[0][0]}:{k.split(':')[1][:5]}={100*fa_lib2.dev_delta(c, keep[k]):+.1f}" for c in MAIN for k in [cid(c)]))
px = "V" if USE_V else ""
for prior in (px + "SV:assembled", px + "assembled+"):
    summarize({cid(c): ni_choice(c, prior, 1.0) for c in MAIN}, f"NI prior={prior} z1=1.0 (reference)")
json.dump({"table": table, "stats": {p: {k: (v if not isinstance(v, list) else None) for k, v in a.items()} for p, a in st.items()}},
          open(f"/tmp/fable_out/c1_table{'_V' if USE_V else ''}.json", "w"))

