"""Command line: ``peachtrees replay | report | pick | info``.

``replay``  apply the rules to saved per-item outputs (no model calls) and print the scores and the decision
``report``  print a decision saved with ``PeachTrees.save_fit``
``pick``    the item rule for one input, from answer keys given on the command line
``info``    version and environment
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from . import __version__
from .replay import format_report, load_rows, replay
from .select import FORMS, explain_pick


def _replay(a: argparse.Namespace) -> int:
    rows = load_rows(a.path)
    modes = ["lite", "full"] if a.mode == "both" else [a.mode]
    results = {m: replay(rows, m, a.z, use_checks=not a.no_checks, use_verifier=not a.no_verifier, switch=a.switch,
                         margin=a.margin) for m in modes}
    if a.json:
        print(json.dumps(results if len(modes) > 1 else results[modes[0]], indent=2))
    else:
        print("\n\n".join(format_report(r) for r in results.values()))
    return 0


def _report(a: argparse.Namespace) -> int:
    with open(a.path, encoding="utf-8") as f:
        d = json.load(f)
    if a.json:
        print(json.dumps({k: v for k, v in d.items() if k != "items"}, indent=2, default=str))
        return 0
    print(f"mode          {d.get('mode')}   switch {d.get('switch', 'do_no_harm')}   z {d.get('z')}")
    print(f"use layer     {d.get('use_layer')}   (n {d.get('n')}, gain {d.get('mean_gain', 0):+.4f} "
          f"+- {d.get('se', 0):.4f})")
    if "program_score" in d:
        print(f"program       {d['program_score']:.4f}")
        print(f"peachtrees    {d['peachtrees_score']:.4f}")
    if d.get("oracle_score") is not None:
        print(f"oracle        {d['oracle_score']:.4f}")
    v = d.get("verifier")
    if v:
        print(f"verifier      {'on' if v.get('enabled') else 'off'}   won {v.get('won')} lost {v.get('lost')} "
              f"of {v.get('contested')} contested")
    cost = (d.get("cost") or {}).get("total")
    if cost:
        print(f"cost          ${cost.get('cost_usd', 0):.4f}, {cost.get('calls')} calls, "
              f"{cost.get('prompt_tokens')}+{cost.get('completion_tokens')} tokens")
    return 0


def _pick(a: argparse.Namespace) -> int:
    keys = {f: getattr(a, f) for f in FORMS}
    keys = {f: (None if v in (None, "", "-") else v) for f, v in keys.items()}
    form, reason = explain_pick(keys, None, use_vote=a.mode == "full")
    print(f"{form} ({reason})")
    return 0


def _info(a: argparse.Namespace) -> int:
    import platform
    try:
        import dspy
        dv = dspy.__version__
    except Exception:  # pragma: no cover
        dv = "not installed"
    print(f"peachtrees {__version__}\ndspy {dv}\npython {platform.python_version()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="peachtrees", description="Inference-time answer selection for DSPy programs.")
    p.add_argument("--version", action="version", version=f"peachtrees {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("replay", help="apply the rules to saved per-item outputs")
    r.add_argument("path")
    r.add_argument("--mode", choices=["full", "lite", "both"], default="full")
    r.add_argument("--z", type=float, default=None, help="default: 1.0 (do_no_harm) or 1.645 (non_inferiority)")
    r.add_argument("--switch", choices=["do_no_harm", "non_inferiority"], default="do_no_harm")
    r.add_argument("--margin", type=float, default=0.02, help="non-inferiority margin (score units)")
    r.add_argument("--no-checks", action="store_true", help="ignore saved checker results")
    r.add_argument("--no-verifier", action="store_true", help="ignore saved verifier choices")
    r.add_argument("--json", action="store_true")
    r.set_defaults(fn=_replay)
    rep = sub.add_parser("report", help="print a decision saved with save_fit")
    rep.add_argument("path")
    rep.add_argument("--json", action="store_true")
    rep.set_defaults(fn=_report)
    pk = sub.add_parser("pick", help="the item rule for one input")
    for f in FORMS:
        pk.add_argument(f"--{f}", default=None, help=f"answer key of the {f} form ('-' = no output)")
    pk.add_argument("--mode", choices=["full", "lite"], default="full")
    pk.set_defaults(fn=_pick)
    sub.add_parser("info", help="version and environment").set_defaults(fn=_info)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
