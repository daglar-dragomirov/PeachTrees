"""Task adapters: answer keys, label-free checkers, per-item tools and verifier evidence for common task types.

A :class:`Task` bundles them; pass it as ``PeachTrees(program, task=tasks.math())``. Explicit ``answer_key`` /
``checker`` / ``tools`` arguments of ``PeachTrees`` take precedence. Nothing here reads a label: keys and checkers see
only the inputs and the candidate output, so they are usable at inference time.

=================  ==================================================================  =============================
preset             answer key                                                          checker / tools
=================  ==================================================================  =============================
``math()``         the final number / expression (``\\boxed{}``, fractions, 1,000)      ``run_python`` (always on)
``choice()``       the option letter                                                   -
``sql(db_for)``    the query's result set (order-insensitive)                          the query runs; ``run_sql``
``code(tests_for)`` behaviour on the statement's public-test inputs                     passes the public tests;
                                                                                       ``run_public_tests``,
                                                                                       ``run_program``
``plan(validate)`` normalised text                                                     your constraint validator
=================  ==================================================================  =============================
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Any, Callable, Hashable, Mapping, Sequence

from .context import item_tool
from .select import text_key

Key = Callable[[Any], "Hashable | None"]
Checker = Callable[[Mapping[str, Any], Any], "bool | None"]
Evidence = Callable[[Mapping[str, Any], Any], str]


@dataclass(frozen=True)
class Task:
    """What PeachTrees needs to know about a task type. Every part is optional."""
    answer_key: Key | None = None
    checker: Checker | None = None
    tools: tuple[Callable, ...] = ()
    evidence: Evidence | None = None
    verify: bool = False          # whether the verifier is worth trying on this task type (fit still decides)
    notes: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def with_(self, **kw: Any) -> Task:
        return replace(self, **kw)


def _out(pred: Any, field_name: str | None) -> Any:
    if field_name is not None:
        return getattr(pred, field_name, None)
    if isinstance(pred, str):
        return pred
    store = getattr(pred, "_store", None)
    if isinstance(store, Mapping):
        vals = [v for k, v in store.items() if k not in ("reasoning", "draft", "draft_prediction")]
        return vals[0] if len(vals) == 1 else None
    return pred


# ====================================================================== generic keys
def exact_key(field_name: str | None = None) -> Key:
    """Whitespace-collapsed, case-folded text."""
    def key(pred):
        v = _out(pred, field_name)
        return None if v in (None, "") else " ".join(str(v).split()).casefold()
    return key


def normalized_key(field_name: str | None = None) -> Key:
    """The default PeachTrees key: no punctuation, no articles, case-folded."""
    def key(pred):
        v = _out(pred, field_name)
        return None if v in (None, "") else (text_key(v) or None)
    return key


def set_key(field_name: str | None = None, sep: str = r"[,;\n]") -> Key:
    """Order-insensitive list of items (e.g. a set of document titles)."""
    def key(pred):
        v = _out(pred, field_name)
        if v in (None, ""):
            return None
        items = v if isinstance(v, (list, tuple, set)) else re.split(sep, str(v))
        s = frozenset(t for t in (text_key(x) for x in items) if t)
        return s or None
    return key


def json_key(field_name: str | None = None) -> Key:
    """Canonical JSON (sorted keys); falls back to normalised text when the output is not JSON."""
    def key(pred):
        v = _out(pred, field_name)
        if v in (None, ""):
            return None
        try:
            obj = json.loads(v) if isinstance(v, str) else v
            return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return text_key(v) or None
    return key


# ====================================================================== math
_BOXED = re.compile(r"\\boxed\s*\{")


def _last_boxed(s: str) -> str | None:
    starts = [m.end() for m in _BOXED.finditer(s)]
    if not starts:
        return None
    i, depth, j = starts[-1], 1, starts[-1]
    while j < len(s) and depth:
        depth += {"{": 1, "}": -1}.get(s[j], 0)
        j += 1
    return s[i:j - 1] if depth == 0 else s[i:]


def canonical_number(text: Any) -> str | None:
    """'1,000' -> '1000', '3.50' -> '7/2', '\\frac{6}{4}' -> '3/2', '-0' -> '0'; None if not a plain number."""
    s = str(text).strip().strip("$").strip()
    s = re.sub(r"\\left|\\right|\\[,;! ]|\\text\{[^}]*\}|\\mathrm\{[^}]*\}|\^\{?\\circ\}?|°|%$", "", s)
    s = re.sub(r"\\[dt]?frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = s.replace(" ", "").rstrip(".")
    if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    m = re.fullmatch(r"\(?([-+]?\d+(?:\.\d+)?)\)?(?:/\(?([-+]?\d+(?:\.\d+)?)\)?)?", s)
    if not m:
        return None
    try:
        v = Fraction(m.group(1)) / (Fraction(m.group(2)) if m.group(2) else 1)
    except (ZeroDivisionError, ValueError):
        return None
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def math_answer(text: Any) -> str | None:
    """The final answer of a math solution: the last \\boxed{}, else 'answer is X', else the last line / number."""
    s = str(text or "").strip()
    if not s:
        return None
    b = _last_boxed(s)
    if b is not None:
        return b.strip()
    m = re.findall(r"(?:final answer|answer)\s*(?:is|:|=)\s*\$?([^\n$]+)", s, flags=re.I)
    if m:
        return m[-1].strip().rstrip(".")
    if len(s) <= 40:
        return s
    nums = re.findall(r"-?\d[\d,]*(?:\.\d+)?(?:/\d+)?", s)
    return nums[-1] if nums else None


def math_key(field_name: str | None = None) -> Key:
    """Numbers compare by value (exact rationals); other answers by normalised LaTeX-free text."""
    def key(pred):
        a = math_answer(_out(pred, field_name))
        if a in (None, ""):
            return None
        n = canonical_number(a)
        if n is not None:
            return n
        t = re.sub(r"\\left|\\right|\\!|\\,|\s|\$", "", a).rstrip(".").lower()
        return t or None
    return key


def math(field_name: str | None = None) -> Task:
    return Task(answer_key=math_key(field_name), verify=True,
                notes="Answers compare by value; the verifier substitutes candidates back into the conditions.")


# ====================================================================== multiple choice
def choice_key(letters: str = "ABCDEFGHIJ", field_name: str | None = None) -> Key:
    """The option letter: 'B', '(B)', 'B.', 'B) text', 'Answer: B', 'the answer is (B)'."""
    L = re.escape(letters)

    def key(pred):
        s = str(_out(pred, field_name) or "").strip()
        if not s:
            return None
        for pat in (rf"^\W*\(?([{L}])\)?(?:[.:)\s]|$)", rf"(?:answer|option|choice)\s*(?:is|:)?\s*\(?([{L}])\)?\b",
                    rf"\\boxed\{{\s*\(?([{L}])\)?\s*\}}"):
            m = re.search(pat, s, flags=re.I)
            if m and m.group(1).upper() in letters:
                return m.group(1).upper()
        return None
    return key


def choice(letters: str = "ABCD", field_name: str | None = None) -> Task:
    return Task(answer_key=choice_key(letters, field_name), verify=True)


# ====================================================================== SQL (SQLite)
_WRITE = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex)\b", re.I)


def extract_sql(text: Any) -> str:
    s = str(text or "").strip()
    m = re.findall(r"```(?:sql|sqlite)?\s*\n?(.*?)```", s, flags=re.S | re.I)
    if m:
        s = m[-1].strip()
    return s.strip().rstrip(";").strip()


class SQLiteDB:
    """Read-only, row-limited, time-limited execution against SQLite files (as in BIRD / Spider)."""

    def __init__(self, max_rows: int = 50, timeout: float = 30.0, cache: bool = True):
        self.max_rows, self.timeout, self.cache = max_rows, timeout, cache
        self._memo: dict[tuple[str, str], tuple[list[str], list[tuple]] | Exception] = {}
        self._lock = threading.Lock()

    def execute(self, path: str, query: str, limit: int | None = None) -> tuple[list[str], list[tuple]]:
        """(column names, rows). Raises on a non-read-only statement, an SQL error or the time limit."""
        q = extract_sql(query)
        if not q:
            raise ValueError("empty query")
        if not re.match(r"^\s*(with|select|values)\b", q, re.I) or _WRITE.search(re.sub(r"'[^']*'", "''", q)):
            raise PermissionError("only read-only SELECT / WITH queries are allowed")
        memo_key = (str(path), q)
        if self.cache:
            with self._lock:
                hit = self._memo.get(memo_key)
            if isinstance(hit, Exception):
                raise hit
            if hit is not None:
                cols, rows = hit
                return cols, rows if limit is None else rows[:limit]
        try:
            cols, rows = self._run(str(path), q)
        except Exception as e:
            if self.cache:
                with self._lock:
                    self._memo[memo_key] = e
            raise
        if self.cache:
            with self._lock:
                self._memo[memo_key] = (cols, rows)
        return cols, rows if limit is None else rows[:limit]

    def _run(self, path: str, q: str) -> tuple[list[str], list[tuple]]:
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
        deadline = time.monotonic() + self.timeout
        con.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10_000)
        try:
            cur = con.execute(q)
            cols = [d[0] for d in (cur.description or [])]
            rows = cur.fetchall()
            return cols, [tuple(r) for r in rows]
        except sqlite3.OperationalError as e:
            if "interrupted" in str(e):
                raise TimeoutError(f"query exceeded {self.timeout:.0f} s") from None
            raise
        finally:
            con.close()


def _cell(v: Any) -> Any:
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, bytes):
        return v.hex()
    return v


def result_set(rows: Sequence[Sequence[Any]]) -> frozenset:
    return frozenset(tuple(_cell(c) for c in r) for r in rows)


def _table(cols: Sequence[str], rows: Sequence[Sequence[Any]], n: int) -> str:
    head = " | ".join(map(str, cols))
    body = "\n".join(" | ".join(str(c)[:60] for c in r) for r in rows[:n])
    more = f"\n... ({len(rows)} rows)" if len(rows) > n else f"\n({len(rows)} rows)"
    return (head + "\n" + body + more).strip()


def sql(db_for: Callable[[Mapping[str, Any]], str], field_name: str | None = None, db: SQLiteDB | None = None,
        show_rows: int = 10) -> Task:
    """Text-to-SQL over SQLite files. ``db_for(inputs)`` returns the database path of an item.

    key       the result set of the predicted query (two queries that return the same rows agree)
    checker   the query runs without an error
    tool      ``run_sql(query)`` for the agents and the verifier, read-only, row-limited
    evidence  columns, row count and first rows of each candidate's result, for the verifier
    """
    ex = db or SQLiteDB()

    def key(pred):
        q = extract_sql(_out(pred, field_name))
        if not q:
            return None
        try:
            from .context import current_inputs
            return result_set(ex.execute(db_for(current_inputs()), q)[1])
        except Exception:
            return None

    def checker(inputs, pred):
        q = extract_sql(_out(pred, field_name))
        if not q:
            return False
        try:
            ex.execute(db_for(inputs), q)
            return True
        except Exception:
            return False

    def run_sql(inputs, query: str) -> str:
        """Run a read-only SQL query (SELECT / WITH) on this question's SQLite database and return the first rows."""
        cols, rows = ex.execute(db_for(inputs), query)
        return _table(cols, rows, ex.max_rows)

    def evidence(inputs, pred):
        q = extract_sql(_out(pred, field_name))
        try:
            cols, rows = ex.execute(db_for(inputs), q)
        except Exception as e:
            return f"the query fails: {type(e).__name__}: {str(e)[:200]}"
        flag = " (EMPTY RESULT)" if not rows else ""
        return f"{len(rows)} rows{flag}; columns {cols}; first rows:\n" + _table(cols, rows, show_rows)

    return Task(answer_key=key, checker=checker, tools=(item_tool(run_sql, name="run_sql"),), evidence=evidence,
                verify=True, notes="Result-set agreement; the verifier runs auxiliary queries on disputed literals.",
                extras={"db": ex})


# ====================================================================== code (stdin / stdout programs)
def extract_code(text: Any, language: str = "python") -> str:
    s = str(text or "")
    blocks = re.findall(rf"```(?:{language}|py|python3)?\s*\n(.*?)```", s, flags=re.S | re.I)
    return (max(blocks, key=len) if blocks else s).strip()


def run_program(code: str, stdin: str = "", timeout: float = 6.0) -> tuple[str, str, int | None]:
    """Run a Python program in a fresh subprocess (isolated mode, temp dir). Returns (stdout, stderr, returncode);
    returncode None means it timed out. This is not a sandbox: run untrusted code in an isolated environment."""
    d = tempfile.mkdtemp(prefix="peachtrees_code_")
    try:
        p = os.path.join(d, "main.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(code)
        r = subprocess.run([sys.executable, "-I", p], input=stdin, capture_output=True, text=True, timeout=timeout,
                           cwd=d)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return out, "timeout", None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def same_output(a: str, b: str) -> bool:
    """Output comparison as in competitive programming judges: tokens equal, numbers within 1e-6."""
    ta, tb = str(a).split(), str(b).split()
    if len(ta) != len(tb):
        return False
    for x, y in zip(ta, tb):
        if x == y:
            continue
        try:
            if abs(float(x) - float(y)) > 1e-6 * max(1.0, abs(float(y))):
                return False
        except ValueError:
            return False
    return True


Tests = Sequence[tuple[str, str]]


def run_tests(code: str, tests: Tests, timeout: float = 6.0) -> list[dict[str, Any]]:
    out = []
    for stdin, expected in tests:
        o, e, rc = run_program(code, stdin, timeout)
        out.append({"ok": rc == 0 and same_output(o, expected), "rc": rc, "stdout": o[-500:], "stderr": e[-300:],
                    "expected": str(expected)[-500:]})
    return out


def code(tests_for: Callable[[Mapping[str, Any]], Tests], field_name: str | None = None, timeout: float = 6.0,
         probe_inputs: Callable[[Mapping[str, Any]], Sequence[str]] | None = None) -> Task:
    """Stdin/stdout programming problems with public tests from the statement (as in LiveCodeBench, Codeforces).

    key       the program's behaviour (stdout per input) on the public-test inputs and optional extra probe inputs:
              programs that behave the same agree, whatever their text (execution-based agreement)
    checker   the program passes every public test
    tools     ``run_public_tests(code)`` and ``run_program(code, stdin)``
    evidence  per-test pass / fail of each candidate, for the verifier
    """
    def inputs_of(inputs) -> list[str]:
        xs = [t[0] for t in tests_for(inputs)]
        if probe_inputs is not None:
            xs += list(probe_inputs(inputs))
        return xs

    memo: dict[tuple[str, str], tuple[str, str, int | None]] = {}
    lock = threading.Lock()

    def run(src, stdin):
        k = (src, stdin)
        with lock:
            if k in memo:
                return memo[k]
        r = run_program(src, stdin, timeout)
        with lock:
            memo[k] = r
        return r

    def key(pred):
        src = extract_code(_out(pred, field_name))
        if not src:
            return None
        from .context import current_inputs
        try:
            xs = inputs_of(current_inputs())
        except Exception:
            return text_key(src) or None
        if not xs:
            return text_key(src) or None
        sig = []
        for x in xs:
            o, _, rc = run(src, x)
            sig.append(" ".join(o.split()) if rc == 0 else f"<rc={rc}>")
        return tuple(sig)

    def checker(inputs, pred):
        src = extract_code(_out(pred, field_name))
        tests = list(tests_for(inputs))
        if not src or not tests:
            return None
        for stdin, expected in tests:
            o, _, rc = run(src, stdin)
            if rc != 0 or not same_output(o, expected):
                return False
        return True

    def run_public_tests(inputs, program: str) -> str:
        """Run a complete Python program on the problem's public tests from the statement; report pass / fail."""
        res = run_tests(extract_code(program), list(tests_for(inputs)), timeout)
        lines = [f"test {i + 1}: {'PASS' if r['ok'] else 'FAIL'}"
                 + ("" if r["ok"] else f" (rc={r['rc']}) got: {r['stdout'][:200]!r} expected: {r['expected'][:200]!r}"
                    + (f" stderr: {r['stderr'][:200]!r}" if r["stderr"] else ""))
                 for i, r in enumerate(res)]
        return "\n".join(lines) or "(no public tests)"

    def run_program_tool(inputs, program: str, stdin: str = "") -> str:
        """Run a complete Python program on a given stdin and return its stdout (and stderr if any)."""
        o, e, rc = run_program(extract_code(program), stdin, timeout)
        return (o[-2000:] or "(no output)") + (f"\n[rc={rc}] {e[-500:]}" if rc != 0 else "")

    def evidence(inputs, pred):
        res = run_tests(extract_code(_out(pred, field_name)), list(tests_for(inputs)), timeout)
        return ", ".join(f"public test {i + 1} {'pass' if r['ok'] else 'FAIL'}" for i, r in enumerate(res)) or "-"

    return Task(answer_key=key, checker=checker,
                tools=(item_tool(run_public_tests, name="run_public_tests"),
                       item_tool(run_program_tool, name="run_program")),
                evidence=evidence, verify=True,
                notes="Behavioural agreement on test inputs; the verifier runs candidates on edge cases.")


# ====================================================================== planning / constrained generation
def plan(validate: Callable[[Mapping[str, Any], Any], bool | None], field_name: str | None = None,
         key: Key | None = None) -> Task:
    """Tasks whose constraints are stated in the input (calendars, trips, schedules): ``validate(inputs, output)``
    checks the stated constraints, never a label."""
    def checker(inputs, pred):
        return validate(inputs, _out(pred, field_name))
    return Task(answer_key=key or normalized_key(field_name), checker=checker,
                notes="Forms that violate a stated constraint are dropped before the vote.")


def free_text(field_name: str | None = None) -> Task:
    """Long free-form outputs (summaries, rewrites): forms almost never agree, so ``mode='lite'`` is the right mode."""
    return Task(answer_key=normalized_key(field_name), notes="Use mode='lite'; the vote has nothing to do here.")


PRESETS: dict[str, Callable[..., Task]] = {"math": math, "choice": choice, "sql": sql, "code": code, "plan": plan,
                                           "free_text": free_text}
