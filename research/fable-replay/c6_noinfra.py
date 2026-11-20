"""C6: the gain on the rows without any infrastructure failure (all three forms returned a parsable output) - a proxy
for 'every arm retried on parse failures'. Compared with the gain on all rows (failed rows score 0)."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
PRIOR = "VSV:assembled"
a_all, a_clean, r_all, r_clean = [], [], [], []
for c in MAIN:
    dev = c["roles"]["DEV"]
    p = ni_choice(c, PRIOR, 1.0)
    clean = [it for it in dev if c["name"] == "u8j" or all(it["ft"]["alive"].get(f) for f in FORMS)]
    g_all = mean(psc(it, p) - it["s"]["rigid"] for it in dev)
    g_clean = mean(psc(it, p) - it["s"]["rigid"] for it in clean)
    rep_all = mean(reported(c, it) - it["s"]["rigid"] for it in dev)
    rep_clean = mean(reported(c, it) - it["s"]["rigid"] for it in clean)
    a_all.append(g_all); a_clean.append(g_clean); r_all.append(rep_all); r_clean.append(rep_clean)
    if len(clean) < 0.97 * len(dev):
        print(f"{cid(c):16s} clean rows {len(clean)}/{len(dev)} | 1.0-full gain all rows {100*g_all:+5.1f}, clean rows {100*g_clean:+5.1f} | reported all {100*rep_all:+5.1f}, clean {100*rep_clean:+5.1f}")
print(f"macro 36 cells: 1.0-full all rows {100*mean(a_all):+.2f}, clean rows {100*mean(a_clean):+.2f} | reported all rows {100*mean(r_all):+.2f}, clean rows {100*mean(r_clean):+.2f}")
for o in ("gepa", "mipro", "simba"):
    idx = [i for i, c in enumerate(MAIN) if c["opt"] == o]
    print(o, f"1.0-full all {100*mean(a_all[i] for i in idx):+.2f} clean {100*mean(a_clean[i] for i in idx):+.2f} | reported all {100*mean(r_all[i] for i in idx):+.2f} clean {100*mean(r_clean[i] for i in idx):+.2f}")

