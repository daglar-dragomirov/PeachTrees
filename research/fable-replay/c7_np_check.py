"""C7: unit check of the NATURAL PLAN statement-only validator: the dataset's own reference plans (PARETO/FIT/DEV rows,
never TEST) must pass it. Used only to test the checker, not for any selection."""
import json, re, sys, importlib.util
spec = importlib.util.spec_from_file_location("feat", "/tmp/fable_out/features_np_only.py")
src = open("/tmp/fable_out/features.py").read()
cut = src.index("nprows = {}")
open("/tmp/fable_out/features_np_only.py", "w").write(src[:cut].replace("from fa_lib import CELLS", ""))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ok = bad = unk = 0
mok = mbad = 0
for role in ("FIT", "PARETO", "DEV"):
    for l in open(f"/root/projects/rider-4d/.external/fieldsuite-natplan-data-v1/roles-v1/{role}.jsonl"):
        r = json.loads(l)
        if r["task"] == "trip":
            v = m.trip_valid(r["prompt"], r["golden"])
            ok += v == 1
            bad += v == 0
            unk += v is None
            if v != 1 and bad + unk <= 3:
                print("trip reference not validated:", r["id"], v)
        else:
            n, clean = m.meet_valid(r["golden_steps"], r["constraints"], r["dist_matrix"])
            mok += clean == 1
            mbad += clean != 1
print(f"trip reference plans: valid {ok}, invalid {bad}, parser failed {unk}")
print(f"meeting reference plans: clean {mok}, not clean {mbad}")

