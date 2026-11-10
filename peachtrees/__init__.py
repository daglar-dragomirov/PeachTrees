"""PeachTrees: a never-worse layer over the program produced by any prompt optimizer."""
from .core import PeachTrees, wrap
from .selection import calibrate_threshold, choose_default, gate

__version__ = "0.1.0"
__all__ = ["PeachTrees", "wrap", "choose_default", "calibrate_threshold", "gate", "__version__"]
