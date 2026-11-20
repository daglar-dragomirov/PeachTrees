"""PeachTrees: an optimizer-agnostic, never-worse layer on top of an optimized DSPy program.

The optimized program (from GEPA, MIPROv2, SIMBA, ...) stays as one of three forms; a ReAct reviewer of its draft and a
ReAct agent are added, and a label-free rule picks one output per input. A task-level non-inferiority test on labeled
selection data switches the layer off where it does not help, so the program is never replaced by something worse on
that data.
"""
from .core import PeachTrees
from .forms import Assembled, Liquid, run_python
from .select import FORMS, non_inferior, paired_stats, pick, text_key

__all__ = ["PeachTrees", "Assembled", "Liquid", "run_python", "FORMS", "pick", "non_inferior", "paired_stats",
           "text_key"]
__version__ = "1.0.1"
