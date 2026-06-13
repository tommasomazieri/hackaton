"""
MOCK RUN — full pipeline walkthrough
=====================================
Set your DC inputs below, then run:

    python src/model/mock.py

Every intermediate and final DataFrame is printed to stdout.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, _PROJECT_ROOT)

from src.model import load_filter, compute, rank  # noqa: E402


def _section(title: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}\n  {title}\n{bar}")


def _show(label: str, df) -> None:
    print(f"\n--- {label} ---")
    print(f"shape : {df.shape}")
    print(f"index : {df.index.name}")
    print(f"cols  : {list(df.columns)}")
    print(df.to_string(max_rows=40, max_cols=10))


if __name__ == "__main__":
    # ------------------------------------------------------------------ #
    #  USER INPUTS — edit these before running                            #
    # ------------------------------------------------------------------ #
    DC_CAPACITY_MW = 50.0        # required generation headroom (MW)
    DC_SURFACE_M2  = 20_000.0    # datacenter footprint (m²)
    #   for km²: DC_SURFACE_M2 = your_km2_value * 1e6
    # ------------------------------------------------------------------ #

    # ── Stage 1: load & filter ─────────────────────────────────────────
    _section("STAGE 1 — load_filter")
    scores, metadata = load_filter.run(
        dc_capacity_mw=DC_CAPACITY_MW,
        dc_surface_m2=DC_SURFACE_M2,
    )
    _show("metadata  (x / y / country)", metadata)
    _show("scores    (raw, post-gate)", scores)

    # ── Stage 2: compute scores ────────────────────────────────────────
    _section("STAGE 2 — compute")
    scored = compute.run(
        df=scores,
        dc_capacity_mw=DC_CAPACITY_MW,
        dc_surface_m2=DC_SURFACE_M2,
    )
    _show("scored    (4 model scores)", scored)

    # ── Stage 3: rank ──────────────────────────────────────────────────
    _section("STAGE 3 — rank")
    results = rank.run(df=scored, metadata=metadata)

    _show("gross     (raw 4 scores)", results["gross"])
    _show("pareto    (max-normalised [0,1])", results["pareto"])
    _show("balance   (L2 norm, best first)", results["balance"])
    _show("metadata  (aligned survivor nodes)", results["metadata"])

    # ── Quick sanity checks ────────────────────────────────────────────
    _section("SANITY CHECKS")
    bal = results["balance"]
    par = results["pareto"]

    ok = True
    checks = {
        "balance_score in [0, 2]": bal["balance_score"].between(0, 2).all(),
        "pareto values in [0, 1]": (par >= 0).all().all() and (par <= 1.0001).all().all(),
        "no capacity_mw in outputs": all(
            "capacity_mw" not in df.columns for df in results.values()
        ),
        "index is node_id everywhere": all(
            df.index.name == "node_id" for df in results.values()
        ),
        "balance index subset of metadata": bal.index.isin(results["metadata"].index).all(),
    }
    for desc, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {desc}")
        if not passed:
            ok = False

    print(f"\n{'All checks passed.' if ok else 'Some checks FAILED — see above.'}")
