"""Deterministic Phase 002D-R2A authorization validation surfaces."""

from .dependency_graph import build_dependency_graph, verify_dependency_graph
from .evidence_freeze import build_input_freeze, verify_input_freeze

__all__ = [
    "build_dependency_graph",
    "build_input_freeze",
    "verify_dependency_graph",
    "verify_input_freeze",
]
