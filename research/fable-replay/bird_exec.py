"""Label-free verification signal for BIRD, computed offline (no model calls): execute every saved form's SQL (and the
assembled form's draft) read-only on the task database; record ok / rows / result-set hash. Never executes or reads gold SQL."""
import glob, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
LR = "/root/.local/share/openresearch/local-runs/"
DBDIR = "/root/projects/rider-4d/.external/newdata-src-v1/bird/minidev/minidev/MINIDEV/dev_databases"
ROLES = "/root/projects/rider-4d/.external/fieldsuite-bird-data-v1/roles-v1"
EXEC = r'''
import hashlib, json, resource, sqlite3, sys
resource.setrlimit(resource.RLIMIT_AS, (4 << 30, 4 << 30))
db, sql = sys.argv[1], sys.stdin.read()
try:
    con = sqlite3.connect("file:" + db + "?mode=ro&immutable=1", uri=True)
    rows = con.execute(sql).fetchall()
    keys = sorted(set(repr(r) for r in rows))
    allnull = all(all(v is None for v in r) for r in rows) if rows else False
    print(json.dumps({"ok": True, "n": len(rows), "h": hashlib.sha256("\n".join(keys).encode()).hexdigest(), "ncol": len(rows[0]) if rows else 0, "allnull": allnull}))
except Exception as e:
    print(json.dumps({"ok": False, "error": (type(e).__name__ + ": " + str(e))[:200]}))
'''


def bird_sql(text):
    s = str(text or "")
    blocks = re.findall(r"```(?:sql|sqlite)?\s*\n?(.*?)```", s, flags=re.S | re.I)
    s = blocks[-1] if blocks else s
    return re.sub(r"^\s*sql\s*:\s*", "", s.strip(), flags=re.I).strip()


def run(db, sql):
    if not sql:
        return {"ok": False, "error": "no SQL"}
    try:
        r = subprocess.run(["nice", "-n", "15", sys.executable, "-I", "-c", EXEC, db], input=sql, capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {"ok": False, "error": "crash " + r.stderr[-120:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}


dbid = {}
for role in ("FIT", "PARETO", "DEV"):  # never TEST
    for l in open(f"{ROLES}/{role}.jsonl"):
        r = json.loads(l)
        dbid[str(r["id"])] = r["db_id"]
jobs = []
for name in ("ptbr", "ptmbr", "ptsbr"):
    w = [p for p in glob.glob(LR + f"*/repo/runs/fieldsuite-v04-{name}/worker") if os.path.exists(p + "/picks-DEV.jsonl")][0]
    for role in ("PARETO", "FIT", "DEV"):
        for f in ("rigid", "liquid", "assembled"):
            for l in open(w + f"/eval-selu-{role}-{f}.jsonl"):
                x = json.loads(l)
                uid = x["uid"]
                key = uid if uid in dbid else uid.split(":", 1)[-1]
                tr = x.get("trajectory") or {}
                jobs.append((name, role, f, uid, dbid.get(key), bird_sql(tr.get("answer") if tr else x.get("answer"))))
                if f == "assembled" and tr.get("draft"):
                    jobs.append((name, role, "draft", uid, dbid.get(key), bird_sql(tr.get("draft"))))
print("jobs", len(jobs), "missing db", sum(1 for j in jobs if not j[4]), flush=True)


def one(j):
    name, role, f, uid, db, sql = j
    res = run(f"{DBDIR}/{db}/{db}.sqlite", sql) if db else {"ok": False, "error": "no db"}
    return {"name": name, "role": role, "form": f, "uid": uid, **res}


out = []
with ThreadPoolExecutor(3) as pool:
    for i, r in enumerate(pool.map(one, jobs)):
        out.append(r)
        if i % 300 == 0:
            print(i, flush=True)
json.dump(out, open("/tmp/fable_out/bird_exec.json", "w"))
print("DONE", len(out), "ok", sum(1 for r in out if r.get("ok")), flush=True)

