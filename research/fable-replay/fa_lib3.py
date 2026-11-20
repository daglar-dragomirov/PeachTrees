"""Fable analysis library 3: verification-filtered policies and the shared-draft lazy policy.
A deterministic, label-free checker (when the task has one) removes forms whose output fails it BEFORE the vote /
default: NATURAL PLAN (constraints of the statement), LCB (public tests, here only as recorded in the agents'
trajectories), BIRD (the query must execute; optional: non-empty result)."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib2 import *
import fa_lib2

OPT = {"bird_empty": False}  # True: also drop queries returning no rows / only NULLs


def vf_alive(it):
    alive = list(it["alive"])
    ft = it.get("ft") or {}
    keep = alive
    if "valid" in ft:  # natplan
        v = {f: ft["valid"].get(f) for f in alive}
        if ft.get("task") == "trip":
            keep = [f for f in alive if v[f] != 0]
        else:
            mx = max((x for x in v.values() if x is not None), default=None)
            keep = [f for f in alive if v[f] is None or v[f] == mx]
    elif "pub" in ft:  # lcb
        keep = [f for f in alive if ft["pub"].get(f) != 0]
    elif "exec" in ft and OPT["bird_empty"]:
        keep = [f for f in alive if not (ft["exec"].get(f, {}).get("n") == 0 or ft["exec"].get(f, {}).get("allnull"))]
    return keep or alive


def svd(it, alive):
    """Shared-draft lazy policy: the reviewer's answer; if the reviewer CHANGED the draft and the independent agent
    reproduces the draft, the draft wins 2:1 (returned through the agent's identical answer); if the reviewer has no
    (valid) output, the draft (= the program's output), else the agent."""
    ft = it.get("ft") or {}
    A, L, R = "assembled", "liquid", "rigid"
    if A not in alive:
        return R if R in alive else (L if L in alive else (A if A in it["alive"] else R))
    if ft.get("changed") == 1 and L in alive and ft["k"].get(L) is not None and ft["k"][L] == ft.get("draft_k"):
        return L
    return A


def svd_needs_liquid(it, alive):
    ft = it.get("ft") or {}
    if "assembled" not in alive:
        return "rigid" not in alive
    return ft.get("changed") == 1


_pol = fa_lib2.pol


def pol(it, name):
    """Adds 'SVD' and 'V<policy>' names (the same policy after the verification filter)."""
    if name == "SVD":
        return svd(it, it["alive"])
    if name.startswith("V"):
        base = name[1:]
        alive = vf_alive(it)
        if base == "SVD":
            return svd(it, alive)
        if base.endswith("+"):
            return live(it, base[:-1], alive)
        if base.startswith("SV:"):
            return sv(it, base[3:], alive)
        raise KeyError(name)
    return _pol(it, name)


def psc(it, name):
    if name == "oracle":
        return max(it["s"][f] for f in FORMS)
    return it["s"][pol(it, name)]


fa_lib2.pol = pol
fa_lib2.psc = psc


def ni_choice(c, prior, z1=1.0, roles=("PARETO", "FIT")):
    """The NI rule: the prior policy unless it is worse than rigid on the selection data beyond noise."""
    m, se = fa_lib2.pstats(items_of(c, roles), prior, "rigid")
    return prior if m + z1 * se >= 0 else "rigid"

# ---- speed: cache the verification filter and every policy's choice per item
_vf_raw = vf_alive


def vf_alive(it):
    v = it.get("_va")
    if v is None:
        v = it["_va"] = _vf_raw(it)
    return v


_pol_raw = pol


def pol(it, name):
    pc = it.get("_pc")
    if pc is None:
        pc = it["_pc"] = {}
    r = pc.get(name)
    if r is None:
        r = pc[name] = _pol_raw(it, name)
    return r


def reset_cache():
    for c in CELLS:
        for items in c["roles"].values():
            for it in items:
                it.pop("_va", None)
                it.pop("_pc", None)


def psc(it, name):
    if name == "oracle":
        return max(it["s"][f] for f in FORMS)
    return it["s"][pol(it, name)]


fa_lib2.pol = pol
fa_lib2.psc = psc

