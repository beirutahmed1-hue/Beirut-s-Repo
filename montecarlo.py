"""
============================================================================
LOADING ARM RELIABILITY-ON-DEMAND MODEL
Stage 4: MONTE CARLO ROBUSTNESS -- Approach 1 (weight-perturbation)
============================================================================

Purpose
-------
Quantify how sensitive the Stage 3 TOPSIS ranking/zones/index are to
uncertainty in the ANP criteria weights (Stage 2), per
"Comparison_of_Monte_Carlo_Approaches (1).md" / BUILD_BRIEF_for_Claude_Code.md:
  - Perturb the ANP weight vector by a +/-15% relative band per criterion,
    renormalize to sum 1, and re-run TOPSIS -- 10,000 times (config
    constants).
  - Report: ranking stability, zone stability, zone-boundary crossings, and
    per-arm score distribution (mean + 5th-95th percentile CI).
Latin Hypercube Sampling is used if scipy is available, else simple random
(not load-bearing to the result -- LHS just gives better coverage per run).

Approach 2 (sparse failure-rate scenario generation) is explicitly
DEFERRED per the companion doc -- a stub/hook is left below, not built.

Status
------
FRAMEWORK, driven by Stages 1-3's placeholder outputs. Nothing here needs
to change when real data replaces the placeholders -- but the specific
robustness numbers below are only as meaningful as that placeholder data.
============================================================================
"""

import numpy as np

from common import N
import stage1_fuzzy_dematel as stage1
import stage2_anp as stage2
import stage3_topsis as stage3

# ---------------------------------------------------------------------------
# Config constants
# ---------------------------------------------------------------------------
PERTURBATION_BAND = 0.15   # +/-15% relative (primary band)
COMPARISON_BANDS = (0.10, 0.15, 0.20)  # brief: also run +/-10% / +/-20%
N_RUNS = 10_000
RANDOM_SEED = 42            # reproducibility for the placeholder run


def _sample_deltas(n_runs, n_dims, band, seed=RANDOM_SEED):
    """
    n_runs x n_dims samples in [-band, band]. Latin Hypercube Sampling if
    scipy is available (better coverage of the perturbation space per run
    than pure random), else simple uniform random. LHS is not load-bearing
    to the conclusions -- either sampling method is valid here.
    """
    try:
        from scipy.stats import qmc
        sampler = qmc.LatinHypercube(d=n_dims, seed=seed)
        unit = sampler.random(n=n_runs)           # in [0, 1)
        print("[Monte Carlo sampling: Latin Hypercube (scipy available)]")
        return (2.0 * unit - 1.0) * band            # -> [-band, band)
    except ImportError:
        print("[Monte Carlo sampling: simple random (scipy not installed) -- "
              "not load-bearing, LHS just gives better per-run coverage]")
        rng = np.random.default_rng(seed)
        return rng.uniform(-band, band, size=(n_runs, n_dims))


def perturb_and_renormalize(w0, deltas):
    """
    w0: (N,) base ANP weights. deltas: (n_runs, N) in [-band, band].
    Returns (n_runs, N) perturbed weight vectors, each renormalized to sum
    to 1 (relative perturbation on a positive base weight with band < 1
    stays strictly positive, so renormalization is always well-defined).
    """
    w_pert = w0[None, :] * (1.0 + deltas)
    assert np.all(w_pert > 0), "Perturbed weight went non-positive -- band too wide."
    return w_pert / w_pert.sum(axis=1, keepdims=True)


def run_monte_carlo(X, w0, band=PERTURBATION_BAND, n_runs=N_RUNS, seed=RANDOM_SEED):
    """
    Runs n_runs perturbed-weight TOPSIS evaluations against the fixed
    decision matrix X. Returns:
      indices: (n_runs, n_arms) reliability index per run per arm
      ranks:   (n_runs, n_arms) each arm's rank (1=best) per run
      zones:   (n_runs, n_arms) each arm's zone per run
    """
    n_arms = X.shape[0]
    deltas = _sample_deltas(n_runs, N, band, seed=seed)
    w_runs = perturb_and_renormalize(w0, deltas)

    indices = np.zeros((n_runs, n_arms))
    ranks = np.zeros((n_runs, n_arms), dtype=int)
    zones = np.zeros((n_runs, n_arms), dtype=int)

    for r in range(n_runs):
        index_r, C_r, S_plus_r, S_minus_r = stage3.topsis(X, w_runs[r])
        indices[r] = index_r
        order = np.argsort(-index_r)
        rank_of_arm = np.empty(n_arms, dtype=int)
        rank_of_arm[order] = np.arange(1, n_arms + 1)
        ranks[r] = rank_of_arm
        zones[r] = [stage3.zone_for_score(s) for s in index_r]

    return indices, ranks, zones


def summarize(indices, ranks, zones, base_zones):
    """Build the four reported summaries (see module docstring)."""
    n_runs, n_arms = indices.shape

    # 1. Ranking stability: % of runs each arm held each rank
    rank_stability = np.zeros((n_arms, n_arms))
    for a in range(n_arms):
        for rk in range(1, n_arms + 1):
            rank_stability[a, rk - 1] = np.mean(ranks[:, a] == rk)

    # 2. Zone stability: % of runs each arm stayed in its BASE zone
    zone_stability = np.array([np.mean(zones[:, a] == base_zones[a]) for a in range(n_arms)])

    # 3. Zone-boundary crossings: full distribution of zones actually visited
    zone_visits = [
        {z: float(np.mean(zones[:, a] == z)) for z in sorted(set(zones[:, a].tolist()))}
        for a in range(n_arms)
    ]

    # 4. Per-arm score distribution: mean + 5th/95th percentile CI
    score_mean = indices.mean(axis=0)
    score_p05 = np.percentile(indices, 5, axis=0)
    score_p95 = np.percentile(indices, 95, axis=0)

    return {
        "rank_stability": rank_stability,
        "zone_stability": zone_stability,
        "zone_visits": zone_visits,
        "score_mean": score_mean,
        "score_p05": score_p05,
        "score_p95": score_p95,
    }


# ---------------------------------------------------------------------------
# Approach 2 stub (DEFERRED -- see "Comparison_of_Monte_Carlo_Approaches (1).md")
# ---------------------------------------------------------------------------
def run_approach2_failure_rate_scenarios(*args, **kwargs):
    """
    STUB -- not built. Approach 2 (sparse-data failure-rate scenario
    generation) is explicitly deferred until real historical failure
    records exist (~5 per arm, per the companion doc) and an FR-sensitivity
    check on real data justifies the effort (FR is only ~14% of Stage 2's
    placeholder weight, so it may not be worth the modelling cost -- but
    that can only be checked with real data). If/when built: bootstrap or
    Bayesian updating of a generic prior (e.g. OREDA-type), NEVER a raw
    Weibull fit to ~5 points. This hook is where it plugs in: it would
    perturb the FR sub-criterion's per-arm score (not the weights) before
    each TOPSIS call, stacking with Approach 1 rather than replacing it.
    """
    raise NotImplementedError(
        "Approach 2 is deferred -- see 'Comparison_of_Monte_Carlo_Approaches (1).md'. "
        "No real failure records are available yet to build this on.")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def report(summary, base_index, base_ranks, base_zones, band, n_runs):
    arms = stage3.ARMS
    print("=" * 92)
    print(f"STAGE 4 - MONTE CARLO (Approach 1: weight-perturbation, +/-{band*100:.0f}%, "
          f"{n_runs:,} runs)")
    print("=" * 92)

    order = np.argsort(-base_index)
    print(f"\n{'Arm':<10}{'Base idx':>10}{'Base rank':>11}{'Base zone':>11}"
          f"{'Mean idx':>10}{'5th pct':>10}{'95th pct':>10}{'Zone stab.':>12}")
    print("-" * 92)
    for i in order:
        print(f"{arms[i]:<10}{base_index[i]:>10.2f}{base_ranks[i]:>11}{base_zones[i]:>11}"
              f"{summary['score_mean'][i]:>10.2f}{summary['score_p05'][i]:>10.2f}"
              f"{summary['score_p95'][i]:>10.2f}{100*summary['zone_stability'][i]:>11.1f}%")
    print("-" * 92)

    print("\nRanking stability (% of runs each arm held each rank, 1=best):")
    header = "".join(f"{'R'+str(r):>8}" for r in range(1, len(arms) + 1))
    print(f"{'Arm':<10}{header}")
    for i in order:
        row = "".join(f"{100*summary['rank_stability'][i, r]:>7.1f}%" for r in range(len(arms)))
        print(f"{arms[i]:<10}{row}")

    print("\nZone-boundary crossings per arm (all zones visited under perturbation):")
    for i in order:
        visits = summary["zone_visits"][i]
        parts = ", ".join(f"Z{z}: {100*p:.1f}%" for z, p in sorted(visits.items()))
        flag = "" if len(visits) == 1 else "  <-- crosses zone boundaries under perturbation"
        print(f"  {arms[i]:<10}{parts}{flag}")


def report_band_comparison(band_results):
    """Short cross-band summary, per the brief's ask to also run +/-10%/+/-20%
    to show conclusions aren't an artifact of the single +/-15% choice."""
    print("\n" + "=" * 92)
    print("Cross-band comparison (does the +/-15% conclusion hold at +/-10% / +/-20%?)")
    print("=" * 92)
    arms = stage3.ARMS
    print(f"{'Arm':<10}" + "".join(f"{'+/-'+str(int(b*100))+'%':>14}" for b in band_results))
    for i in range(len(arms)):
        row = "".join(f"{100*band_results[b]['zone_stability'][i]:>13.1f}%" for b in band_results)
        print(f"{arms[i]:<10}{row}   (zone stability)")


def main():
    L, M, U = stage1.build_direct_matrix()
    (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation = stage1.fuzzy_dematel(L, M, U)
    w0, (wl, wm, wu), dangling_codes, n_squarings = stage2.run_anp(Tl, Tm, Tu)

    X = stage3.build_decision_matrix()
    base_index, base_C, base_Splus, base_Sminus = stage3.topsis(X, w0)
    order = np.argsort(-base_index)
    base_ranks = np.empty(len(base_index), dtype=int)
    base_ranks[order] = np.arange(1, len(base_index) + 1)
    base_zones = np.array([stage3.zone_for_score(s) for s in base_index])

    band_results = {}
    for band in COMPARISON_BANDS:
        indices, ranks, zones = run_monte_carlo(X, w0, band=band)
        band_results[band] = summarize(indices, ranks, zones, base_zones)

    report(band_results[PERTURBATION_BAND], base_index, base_ranks, base_zones,
           PERTURBATION_BAND, N_RUNS)
    report_band_comparison(band_results)

    summary = band_results[PERTURBATION_BAND]
    np.savez("stage4_outputs.npz",
             arms=np.array(stage3.ARMS),
             base_index=base_index, base_ranks=base_ranks, base_zones=base_zones,
             score_mean=summary["score_mean"], score_p05=summary["score_p05"],
             score_p95=summary["score_p95"], zone_stability=summary["zone_stability"],
             rank_stability=summary["rank_stability"])
    print("\n[Saved stage4_outputs.npz (Monte Carlo robustness summary, +/-15% band).]")


if __name__ == "__main__":
    main()
