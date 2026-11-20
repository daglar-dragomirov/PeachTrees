import json
R = "/root/projects/rider-4d/.external/fieldsuite-natplan-data-v1/roles-v1"
rows = [json.loads(l) for l in open(R + "/PARETO.jsonl")]
print(len(rows), list(rows[0].keys()))
seen = set()
for r in rows:
    if r["task"] in seen:
        continue
    seen.add(r["task"])
    print("=== task", r["task"], "id", r["id"])
    p = r["prompt"]
    print("prompt len", len(p))
    print("PROMPT TAIL:", p[-1500:])
    for k in r:
        if k not in ("prompt",):
            print("  ", k, ":", json.dumps(r[k])[:500])
import collections
print(collections.Counter(r["task"] for r in rows))
print(open("/tmp/fable_out/bird_exec.py.log").read()[-300:])

