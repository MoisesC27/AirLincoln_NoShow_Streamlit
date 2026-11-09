"""Pruebas de consistencia de los cálculos. Ejecutar: python -m pytest -q"""
import numpy as np
import pandas as pd
import pytest

from core.catalog import TARGET
from core.data import prepare, wilson
from core.model import confusion, train_all
from core.overbooking import betabinom_pmf, simulate
from core.quality import gate, run_checks


@pytest.fixture(scope="module")
def ctx():
    df, info = prepare()
    return df, info, train_all(df)


def test_dataset(ctx):
    df, info, _ = ctx
    assert info.rows == 10_000 and df[TARGET].sum() == 998
    assert df.attrs["bom_rows"] == 4


def test_no_shared_ids(ctx):
    df, _, _ = ctx
    s = df.groupby("part").Customer_ID.apply(set)
    assert not (s["train"] & s["valid"]) and not (s["train"] & s["test"]) and not (s["valid"] & s["test"])


def test_confusion_sums(ctx):
    df, _, tm = ctx
    p = tm.probs[tm.selected]
    for part in ("valid", "test"):
        m = df.part == part
        for t in (0.1, 0.3, 0.5, 0.8):
            c = confusion(df.loc[m, TARGET], p[m], t)
            assert c["vp"] + c["fp"] + c["fn"] + c["vn"] == m.sum()
            assert c["vp"] + c["fn"] == df.loc[m, TARGET].sum()


def test_betabinom_pmf_sums_to_one():
    assert abs(betabinom_pmf(250, 0.15 * 185, 0.85 * 185).sum() - 1) < 1e-9


def test_simulation_matches_monte_carlo():
    rate, n, cap = 0.16, 185, 180
    r = simulate(rate, n, cap, 2500, 9000)
    k = int(r.best.extra); B = cap + k
    rng = np.random.default_rng(0)
    q = rng.beta(rate * n, (1 - rate) * n, 200_000)
    N = rng.binomial(B, q)
    assert abs((N < k).mean() - r.best.p_negar) < 0.01
    assert abs(np.maximum(0, k - N).mean() - r.best.negados) < 0.02


def test_constraint_respected():
    r = simulate(0.16, 185, 180, 2500, 9000, max_deny_prob=0.05)
    assert r.best.p_negar <= 0.05 + 1e-12


def test_wilson():
    lo, hi = wilson(50, 500)
    assert lo < 0.1 < hi


def test_gate_not_blocked(ctx):
    df, _, tm = ctx
    status, _ = gate(run_checks(df, tm.metrics, tm.selected))
    assert status in ("Aceptado", "Aceptado con observaciones")
