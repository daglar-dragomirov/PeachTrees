"""run_python: the one tool every PeachTrees agent and the judge get in addition to the task's own tools."""
import os
import shutil
import subprocess
import sys
import tempfile


def run_python(code: str) -> str:
    """Run Python 3 code (standard library only, no network, 10 s limit) and return what it prints; use print()."""
    d = tempfile.mkdtemp(prefix="peachtrees_py_")
    try:
        path = os.path.join(d, "main.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(code))
        cmd = [sys.executable, "-I", path]
        if shutil.which("unshare") and sys.platform.startswith("linux"):
            cmd = ["unshare", "-n", "-r"] + cmd  # no network where user namespaces are available
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=d)
        except subprocess.TimeoutExpired:
            return "[timed out after 10 s]"
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr[-1500:]) if r.stderr else "")
        return out[-3000:] or "(no output; use print())"
    except Exception as e:  # the tool must never crash an agent
        return f"error: {type(e).__name__}: {str(e)[:200]}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
