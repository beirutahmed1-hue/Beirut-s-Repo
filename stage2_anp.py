"""
============================================================================
LOADING ARM RELIABILITY-ON-DEMAND MODEL
Stage 2 of 3: FUZZY ANP  (DEMATEL-based ANP, i.e. DANP)
============================================================================

Purpose
-------
Take Stage 1's fuzzy total-influence matrix T = (Tl, Tm, Tu) and turn the
DEMATEL influence structure into interdependency-aware CRITERIA WEIGHTS,
following BUILD_BRIEF_for_Claude_Code.md:
  1. Column-normalize T -> the (unweighted/weighted) supermatrix.
  2. Raise the supermatrix to successive powers until it converges (columns
     stabilize / become identical) -> the limit supermatrix.
  3. The stabilized column = the criteria weights (sums to 1).
  4. Roll up sub-criterion weights into cluster weights.
Kept fuzzy through the supermatrix (Tl, Tm, Tu each powered independently,
component-wise -- the same practical approximation Stage 1 already uses for
the fuzzy total-influence matrix); defuzzified (centroid) only at the very
end, per the "defuzzify once, at the end" decision (DEMATEL-ANP-TOPSIS.md
S4.5).

Status
------
FRAMEWORK, driven by Stage 1's placeholder output. Nothing here needs to
change when real expert data replaces Stage 1's placeholders.

A real numerical complication surfaces with the current placeholder network
and is handled explicitly below -- see "Dangling columns / damping".
============================================================================
"""

import numpy as np

from common import CODES, NAME, CLUSTER, CLUSTERS, N, IDX
import stage1_fuzzy_dematel as stage1

# ---------------------------------------------------------------------------
# Config constants
# ---------------------------------------------------------------------------
# PageRank-style damping factor for the limit-supermatrix power iteration.
# See build_weighted_supermatrix()/limit_supermatrix() docstrings for why
# this is needed. 0.85 is the standard eigenvector-centrality/PageRank
# default; kept as a named constant so it can be tuned/reported on.
DAMPING = 0.85
MAX_SQUARINGS = 200
CONVERGENCE_TOL = 1e-10


def build_weighted_supermatrix(T):
    """
    Column-normalize an N x N nonnegative total-influence matrix T into a
    column-stochastic "weighted supermatrix" W (each column sums to 1):
    W[i, j] = criterion i's share of criterion j's total inbound influence,
    i.e. i's relative importance with respect to j.

    Dangling columns / self-loop fix
    ---------------------------------
    A screened DEMATEL network (only "plausible" links get a strength grade)
    can leave some criteria with literally zero total inbound influence --
    direct or indirect. Two distinct ways this happens with the current
    placeholder data:
      - No inbound link at all (AF, UF, OPC are pure drivers with no
        measured causes of their own): all three fuzzy components (l,m,u)
        are zero.
      - A component-specific zero: MC's only inbound link is "VS->MC"
        graded "Low", whose TFN is (0, 0.25, 0.5) -- l=0. Every path into MC
        (direct or indirect) must end on that link, so MC's L-component
        column is exactly zero even though its M/U columns are not. This is
        a legitimate fuzzy-uncertainty fact (the pessimistic reading of
        expert judgment says MC is entirely uninfluenced), not a data
        error -- so which columns are dangling can differ between the l, m,
        u components, and must be handled per-component.
    Either way, a zero column cannot be normalized by division. Left as an
    all-zero column, the supermatrix is no longer column-stochastic and
    repeated squaring collapses the whole matrix to zero (verified
    empirically). The standard "dangling node" treatment (cf. PageRank) is
    applied: such a column becomes a self-loop (W[j, j] = 1) -- criterion j
    is purely self-referential in the propagation step, since nothing in the
    screened network (at that component's confidence level) says otherwise.

    Returns (W, dangling_codes).
    """
    colsum = T.sum(axis=0)
    W = np.zeros_like(T)
    dangling_codes = []
    for j in range(N):
        if colsum[j] < 1e-9:
            W[j, j] = 1.0
            dangling_codes.append(CODES[j])
        else:
            W[:, j] = T[:, j] / colsum[j]
    return W, dangling_codes


def limit_supermatrix(W, damping=DAMPING, max_squarings=MAX_SQUARINGS,
                       tol=CONVERGENCE_TOL):
    """
    Raise the weighted supermatrix to successive powers (by repeated
    squaring) until its columns stabilize / become identical -> the limit
    supermatrix. Returns (weight_vector, n_squarings_used).

    Damping is required, not optional, here
    -----------------------------------------
    Self-loop dangling columns (see build_weighted_supermatrix) make the
    resulting Markov chain reducible: AF/UF/OPC become absorbing states that
    nothing "escapes" once entered, since nothing in the screened network
    points back out of them. Verified empirically on the placeholder data:
    undamped power iteration does NOT converge to identical columns -- each
    starting column instead converges to its OWN distribution over just the
    absorbing states, violating "columns stabilize / become identical" and
    silently zeroing out most of the 15 criteria. Mixing in a small uniform
    teleportation term (the classic PageRank/eigenvector-centrality fix)
    makes the chain irreducible and aperiodic, which guarantees (Perron-
    Frobenius) a UNIQUE stationary distribution reached from any starting
    column. This is a standard, precedented fix for exactly this failure
    mode, not an arbitrary tweak -- but it should be named explicitly if
    asked in a viva, since it is not in the base DANP recipe.
    """
    Wd = damping * W + (1.0 - damping) * (1.0 / N) * np.ones((N, N))

    M = Wd.copy()
    spread = np.inf
    for k in range(1, max_squarings + 1):
        M_next = M @ M
        M_next = M_next / M_next.sum(axis=0, keepdims=True)
        spread = np.abs(M_next - M).max()
        M = M_next
        if spread < tol:
            break
    else:
        raise RuntimeError(
            f"Limit supermatrix did not converge within {max_squarings} "
            f"squarings (last change={spread:.2e}). Check the influence "
            f"data / damping factor.")

    col_spread = (M.max(axis=1) - M.min(axis=1)).max()
    assert col_spread < 1e-6, (
        f"Limit supermatrix columns are not identical (spread={col_spread:.2e}) "
        f"-- convergence check failed; the limit is not well-defined.")

    return M[:, 0], k


def run_anp(Tl, Tm, Tu, damping=DAMPING):
    """
    Fuzzy ANP end to end: for each fuzzy component (Tl, Tm, Tu independently
    -- the component-wise fuzzy approximation, consistent with Stage 1),
    build the weighted supermatrix, power it to the limit, and read off the
    limiting column as that component's weight vector (each sums to 1 by
    construction). Defuzzify by centroid ONLY here, at the end.

    Because sum(wl) = sum(wm) = sum(wu) = 1, their centroid also sums to 1
    exactly -- no renormalization needed.

    Returns (w_crisp, (wl, wm, wu), dangling_codes, n_squarings).
    """
    component_weights = {}
    dangling_by_component = {}
    iters_by_component = {}
    for name, T in (("l", Tl), ("m", Tm), ("u", Tu)):
        W, dangling = build_weighted_supermatrix(T)
        w, k = limit_supermatrix(W, damping=damping)
        component_weights[name] = w
        dangling_by_component[name] = set(dangling)
        iters_by_component[name] = k

    # Dangling sets can legitimately differ between l, m, u (see
    # build_weighted_supermatrix docstring -- a "Low"/"No" grade has l=0, so
    # a criterion's pessimistic-bound column can be structurally zero even
    # when its optimistic-bound column is not). Report the union: any
    # criterion dangling in at least one component got a forced self-loop
    # somewhere and is worth flagging.
    dangling_union = sorted(set().union(*dangling_by_component.values()))

    wl, wm, wu = component_weights["l"], component_weights["m"], component_weights["u"]
    w_crisp = (wl + wm + wu) / 3.0

    assert abs(w_crisp.sum() - 1.0) < 1e-6, (
        f"ANP weights do not sum to 1 (sum={w_crisp.sum():.6f})")
    assert len(w_crisp) == N, f"Expected {N} sub-criteria, got {len(w_crisp)}"

    return w_crisp, (wl, wm, wu), dangling_union, max(iters_by_component.values())


def cluster_weight_rollup(w):
    """Sum sub-criterion weights within each cluster -> cluster weights."""
    rollup = {c: 0.0 for c in CLUSTERS}
    for i, code in enumerate(CODES):
        rollup[CLUSTER[code]] += w[i]
    return rollup


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def report(w_crisp, fuzzy_components, dangling_codes, n_squarings):
    wl, wm, wu = fuzzy_components
    print("=" * 74)
    print("STAGE 2 - FUZZY ANP (DANP)  (driven by Stage 1 placeholder data)")
    print("=" * 74)
    print(f"Damping factor: {DAMPING}  |  converged after {n_squarings} squaring(s)")
    if dangling_codes:
        print(f"\nDangling columns (zero inbound influence in the screened "
              f"network): {', '.join(dangling_codes)}")
        print("  -> WARNING: these criteria receive no direct or indirect "
              "influence from any\n     other screened criterion, so their "
              "supermatrix column is a forced self-loop.\n     With this "
              "SYNTHETIC placeholder network they end up dominating the "
              "global\n     weights below (see totals) -- an artifact of "
              "the placeholder screening set,\n     not a methodological "
              "conclusion. Expected to change once real expert screening\n"
              "     routes at least some influence into these criteria.")

    print(f"\n{'Code':<6}{'Cluster':<14}{'w_l':>8}{'w_m':>8}{'w_u':>8}"
          f"{'w (crisp)':>11}{'weight %':>10}")
    print("-" * 74)
    order = np.argsort(-w_crisp)
    for i in order:
        c = CODES[i]
        print(f"{c:<6}{CLUSTER[c]:<14}{wl[i]:>8.4f}{wm[i]:>8.4f}{wu[i]:>8.4f}"
              f"{w_crisp[i]:>11.4f}{100*w_crisp[i]:>9.2f}%")
    print("-" * 74)
    print(f"{'TOTAL':<20}{'':>8}{'':>8}{'':>8}{w_crisp.sum():>11.4f}"
          f"{100*w_crisp.sum():>9.2f}%")

    print("\nCluster weights (sum of member sub-criteria):")
    rollup = cluster_weight_rollup(w_crisp)
    for cluster, weight in sorted(rollup.items(), key=lambda kv: -kv[1]):
        print(f"  {cluster:<14}{weight:>8.4f}  ({100*weight:.2f}%)")

    # Acceptance checks (BUILD_BRIEF_for_Claude_Code.md): weights sum to 1,
    # all 15 sub-criteria present.
    assert abs(w_crisp.sum() - 1.0) < 1e-6
    assert len(w_crisp) == N
    print(f"\n[Acceptance check OK: {N} sub-criteria present, weights sum to "
          f"{w_crisp.sum():.6f}]")


def main():
    L, M, U = stage1.build_direct_matrix()
    (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation = stage1.fuzzy_dematel(L, M, U)

    w_crisp, (wl, wm, wu), dangling_codes, n_squarings = run_anp(Tl, Tm, Tu)
    report(w_crisp, (wl, wm, wu), dangling_codes, n_squarings)

    np.savez("stage2_outputs.npz",
             codes=np.array(CODES),
             w=w_crisp, wl=wl, wm=wm, wu=wu,
             dangling_codes=np.array(dangling_codes))
    print("\n[Saved stage2_outputs.npz (ANP criteria weights) for Stage 3 (TOPSIS).]")


if __name__ == "__main__":
    main()
