"""B2: how predictive are the label-free verification signals found in the saved outputs?
(NATURAL PLAN constraint validity, LCB public-test evidence in the agents' trajectories, 'assembled changed the draft',
form errors). Pooled over PARETO+FIT+DEV per cell; no model calls."""
import sys, os
sys.path.insert(0, "/tmp/fable_out")
from fa_lib2 import *


def tab(rows, label):
    n = len(rows)
    if not n:
        return f"{label}: n=0"
    return f"{label}: n={n} acc={sum(rows)/n:.3f}"


print("== NATURAL PLAN: P(correct | checker verdict), per form, all roles pooled")
for c in CELLS:
    if c["ds"] != "natplan":
        continue
    for task in ("trip", "meeting"):
        line = f"{cid(c)} {task}:"
        for f in FORMS:
            ok, bad, unk = [], [], []
            for role in ("PARETO", "FIT", "DEV"):
                for it in c["roles"][role]:
                    ft = it["ft"]
                    if ft.get("task") != task or f not in it["alive"]:
                        continue
                    v = ft["valid"].get(f)
                    if task == "trip":
                        (ok if v == 1 else bad if v == 0 else unk).append(it["s"][f])
                    else:
                        vs = [ft["valid"][g] for g in it["alive"]]
                        (ok if v == max(vs) and v == int(v) else bad).append(it["s"][f])
            line += f" | {f[0]}: {tab(ok, 'valid')} {tab(bad, 'invalid')} {tab(unk, 'unk')}"
        print(line)

print("\n== LCB: P(correct | last public-test result seen in the agent's own trajectory)")
for c in CELLS:
    if c["ds"] != "lcb":
        continue
    line = cid(c) + ":"
    for f in ("liquid", "assembled"):
        d = {1: [], 0: [], None: []}
        for role in ("PARETO", "FIT", "DEV"):
            for it in c["roles"][role]:
                if f in it["alive"]:
                    d[it["ft"].get("pub", {}).get(f)].append(it["s"][f])
        line += f" | {f}: {tab(d[1], 'pass')} {tab(d[0], 'fail')} {tab(d[None], 'none')}"
    print(line)

print("\n== assembled changed its draft? accuracy of assembled / rigid by 'changed' (DEV)")
agg = {0: [0, 0, 0], 1: [0, 0, 0]}
for c in CELLS:
    if c["name"] == "u8j":
        continue
    dev = c["roles"]["DEV"]
    line = f"{cid(c):16s}"
    for ch in (0, 1):
        its = [it for it in dev if it["ft"].get("changed") == ch]
        if its:
            a, r = mean(it["s"]["assembled"] for it in its), mean(it["s"]["rigid"] for it in its)
            line += f" | changed={ch}: share {len(its)/len(dev):.2f} asm {a:.3f} rigid {r:.3f}"
            if c["opt"] != "gepa1":
                agg[ch][0] += len(its) / len(dev); agg[ch][1] += a * len(its) / len(dev); agg[ch][2] += r * len(its) / len(dev)
    print(line)
for ch in (0, 1):
    t = agg[ch]
    print(f"macro changed={ch}: share {t[0]/35:.3f} asm {t[1]/t[0]:.3f} rigid {t[2]/t[0]:.3f}")

print("\n== form errors (no output) on DEV: share per form, and the error texts")
import glob, json, collections
LR = "/root/.local/share/openresearch/local-runs/"
for c in CELLS:
    if c["name"] == "u8j":
        continue
    dev = c["roles"]["DEV"]
    dead = {f: sum(1 for it in dev if f not in it["alive"]) / len(dev) for f in FORMS}
    if max(dead.values()) >= 0.03:
        print(f"{cid(c):16s} dead share " + " ".join(f"{f[0]}={dead[f]:.2f}" for f in FORMS))
for name, run in (("ptmc", "2b7cf7ca"), ("ptsc", "eaaee5df"), ("ptsa", "53d9b7c6"), ("ptth", "05b62d8b"), ("ptnp", "723fdbec"), ("ptma", "373ebb35"), ("pt1l", "e74667a4")):
    w = glob.glob(LR + run + f"*/repo/runs/fieldsuite-v04-{name}/worker")[0]
    for f in FORMS:
        cnt = collections.Counter()
        for l in open(w + f"/eval-selu-DEV-{f}.jsonl"):
            x = json.loads(l)
            if x.get("error"):
                cnt[str(x["error"])[:110]] += 1
            elif not x.get("trajectory"):
                cnt["(no trajectory, no error)"] += 1
        if cnt:
            print(name, f, dict(cnt.most_common(4)))
print(open("/tmp/fable_out/bird_exec.py.log").read()[-60:])

