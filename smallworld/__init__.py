"""
Small-World Services - Microservice Topology Optimizer

A library/tool that extracts microservice dependency graphs, computes network metrics,
and suggests "shortcut" points to optimize service topology using Small-World Network theory.
"""

__version__ = "0.1.0"
__author__ = "Small-World Services Team"

from smallworld.core.graph_builder import GraphBuilder
from smallworld.core.metrics import MetricsCalculator
from smallworld.core.shortcut_optimizer import ShortcutOptimizer

__all__ = [
    "GraphBuilder",
    "MetricsCalculator",
    "ShortcutOptimizer",
    "__version__",
]
