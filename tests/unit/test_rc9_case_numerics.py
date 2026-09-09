"""Synthetic arithmetic probes of case-specific first-party numerical helpers."""

import ast
import bisect
import math

import pytest


def scalar_helpers(repo_root):
    path = (
        repo_root
        / "evals/results/phase-004c6/CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006/code/check.py"
    )
    tree = ast.parse(path.read_text())
    code = ast.Module(
        body=[
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in {"inverse", "evaluate", "coefficients"}
        ],
        type_ignores=[],
    )
    namespace = {"math": math, "bisect": bisect}
    exec(compile(code, str(path), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("cubic", [False, True])
def test_last_downward_crossing_survives_nonmonotone_relaxation(repo_root, cubic):
    helper = scalar_helpers(repo_root)
    knots = [(0, 12), (1, 9), (2, 11), (3, 8)]
    x = [r[0] for r in knots]
    coefficients = helper["coefficients"](knots, cubic)

    def curve(t):
        return helper["evaluate"](x, coefficients, t)

    def derivative(t):
        j = min(max(0, bisect.bisect_right(x, t) - 1), len(coefficients) - 1)
        a, b, c, _ = coefficients[j]
        z = t - x[j]
        return (3 * a * z + 2 * b) * z + c

    curve.knots, curve.derivative = x, derivative
    t = helper["inverse"](curve, 3, 10)
    assert 2 < t < 3
    assert curve(t) == pytest.approx(10, abs=1e-12)
    if not cubic:
        assert t == pytest.approx(7 / 3)


def test_internal_cubic_turns_are_split_before_last_crossing(repo_root):
    helper = scalar_helpers(repo_root)

    def curve(t):
        return 10 - (t - 0.2) * (t - 0.5) * (t - 0.8)

    curve.knots = [0, 1]
    curve.derivative = lambda t: -3 * t * t + 3 * t - 0.66
    assert helper["inverse"](curve, 1, 10) == pytest.approx(0.8, abs=1e-10)


def test_current_interpolation_retains_last_crossing_of_nonmonotone_curves(repo_root):
    import numpy as np
    from scipy.interpolate import PPoly

    path = (
        repo_root
        / "evals/results/phase-004c6/CUMCM-2016-C-POSTVALIDATION-DEVELOPMENT-006/code/produce.py"
    )
    tree = ast.parse(path.read_text())
    code = ast.Module(
        body=[
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in {"surface", "crossing"}
        ],
        type_ignores=[],
    )
    namespace = {"np": np, "PPoly": PPoly}
    exec(compile(code, str(path), "exec"), namespace)
    points = np.array([12, 9, 11, 8])
    polys = {}
    for current, duration in ((50, 3), (60, 6)):
        x = np.linspace(0, duration, 4)
        polys[current] = PPoly(
            np.vstack([np.zeros(3), np.zeros(3), np.diff(points) / np.diff(x), points[:-1]]), x
        )
    forward, inverse, duration, _ = namespace["surface"](polys, {50: 3, 60: 6}, 55, "BASELINE")
    assert duration == 4.5
    assert inverse(10) == pytest.approx(3.5)
    assert forward(inverse(10) / duration) == pytest.approx(10)
