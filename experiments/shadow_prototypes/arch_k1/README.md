# ARCH-K1 — Thin deterministic evidence kernel

This isolated shadow arm implements the four frozen Phase 002D-R3 components as project-owned,
deterministic kernels. `kernel.py` is a thin shared-interface adapter; lifecycle, claim support,
reproducibility, and model comparison each enforce their own frozen invariants and emit reason-coded
evidence without writing formal state.

The package does not modify or load the formal Skill, access the hidden vault, execute third-party
code, perform network calls, or declare formal integration. It is removable as one experimental
directory.
