"""
============================================================================
LOADING ARM RELIABILITY-ON-DEMAND MODEL  (single-file pipeline)
============================================================================
Pipeline: FMECA (offline) -> Fuzzy DEMATEL -> Fuzzy ANP (DANP) -> TOPSIS
          -> Monte Carlo weight-perturbation robustness.
Output: a 0-100 reliability-on-demand index per loading arm, a ranking, and
replacement-zone assignments.

This is the single-file version of the pipeline (common.py +
stage1_fuzzy_dematel.py + stage2_anp.py + stage3_topsis.py + montecarlo.py
merged together) so the whole thing can be copy-pasted into one notebook
cell or run as one script with no cross-file imports. Running this file
directly (`python loading_arm_model.py`) executes Stage 1 -> 2 -> 3 -> 4 in
sequence and prints/saves the results of each -- it doubles as the
run_pipeline.py orchestrator from the build brief.

Status: FRAMEWORK + PLACEHOLDER DATA throughout (expert judgments in
Stage 1, arm scores in Stage 3). Every placeholder is clearly marked and
isolated so real data can be swapped in without touching the math -- see
BUILD_BRIEF_for_Claude_Code.md and the companion planning docs.
============================================================================
"""

import numpy as np

# ============================================================================
# COMMON  --  criteria hierarchy + TFN linguistic scale (shared by all stages)
# ============================================================================

# 5 clusters, 15 sub-criteria. Codes are used as row/column labels throughout.
SUBCRITERIA = [
    # Cluster 1 - Corrosion / External Integrity
    ("EI",   "External Integrity (corrosion/coating/metal loss)", "Corrosion"),
    ("II",   "Internal Integrity",                                "Corrosion"),
    # Cluster 2 - Mechanical Integrity
    ("SJ",   "Swivel Joint Condition",                            "Mechanical"),
    ("SEAL", "Seal Integrity",                                    "Mechanical"),
    ("HYD",  "Hydraulic/Control System Health",                   "Mechanical"),
    ("ER",   "Emergency Release (QC-DC) Function",                "Mechanical"),
    ("AF",   "Aging",                                             "Mechanical"),
    # Cluster 3 - Operational Performance
    ("OPC",  "Operation Performance Compliance",                  "Operational"),
    ("UF",   "Utilization Frequency",                             "Operational"),
    ("FR",   "Failure Rate",                                      "Operational"),
    # Cluster 4 - Maintenance
    ("MC",   "PM Compliance",                                     "Maintenance"),
    ("MQ",   "Maintenance Execution Quality",                     "Maintenance"),
    # Cluster 5 - Obsolescence & Supportability
    ("SPA",  "Spare Parts Availability",                          "Obsolescence"),
    ("VS",   "Vendor Support",                                    "Obsolescence"),
    ("RE",   "Reverse Engineering",                               "Obsolescence"),
]

CODES = [s[0] for s in SUBCRITERIA]
NAME  = {s[0]: s[1] for s in SUBCRITERIA}
CLUSTER = {s[0]: s[2] for s in SUBCRITERIA}
N = len(CODES)
IDX = {c: i for i, c in enumerate(CODES)}
CLUSTERS = sorted(set(CLUSTER.values()), key=lambda c: [CLUSTER[code] for code in CODES].index(c))

# TFN linguistic scale (normalized [0,1]) -- decided mapping
TFN = {
    "No":       (0.0,  0.0,  0.25),
    "Low":      (0.0,  0.25, 0.50),
    "Medium":   (0.25, 0.50, 0.75),
    "High":     (0.50, 0.75, 1.00),
    "VeryHigh": (0.75, 1.00, 1.00),
}
FUZZY_ZERO = (0.0, 0.0, 0.0)   # screened-out / no-link cells


def centroid(l, m, u):
    """Centroid defuzzification for a TFN: (l+m+u)/3."""
    return (l + m + u) / 3.0


# ============================================================================
# STAGE 1 of 4: FUZZY DEMATEL
# ============================================================================
# Take expert influence judgments among the criteria/sub-criteria (as
# linguistic grades), convert them to Triangular Fuzzy Numbers (TFNs), and
# run fuzzy DEMATEL to produce the fuzzy total-influence matrix T and each
# factor's prominence (D+R) / relation (D-R) / cause-effect classification.
#
# STATUS: FRAMEWORK + PLACEHOLDER DATA. Experts are not yet available. The
# influence judgments below are SYNTHETIC placeholders so the pipeline runs
# end-to-end today. Replace RAW_JUDGMENTS (and the screening set) with real
# expert input later; nothing else needs to change.
# ============================================================================

# Screening: set of plausible DIRECTED links (A influences B) -> "A->B".
# Only these get a strength grade; every other directed pair = fuzzy zero.
PLAUSIBLE_LINKS = {
    # Aging drives condition and obsolescence (headline cause factor)
    "AF->EI", "AF->II", "AF->SJ", "AF->SEAL", "AF->HYD", "AF->FR",
    "AF->SPA", "AF->VS", "AF->RE",
    # Corrosion effects
    "EI->II", "EI->FR", "II->FR",
    # Mechanical internal links
    "SJ->SEAL", "SEAL->SJ", "SJ->FR", "SEAL->FR", "HYD->FR", "HYD->ER",
    "SJ->ER",
    # Operational
    "UF->SJ", "UF->SEAL", "UF->HYD", "UF->FR", "OPC->EI", "OPC->II",
    # Maintenance drives condition
    "MC->SEAL", "MC->SJ", "MC->HYD", "MC->EI", "MQ->SEAL", "MQ->HYD",
    "MC->FR", "MQ->FR",
    # Obsolescence internal links
    "SPA->RE", "VS->SPA", "VS->MQ", "VS->MC",
}

# Strength grades for the plausible links (SYNTHETIC placeholder). Must
# cover every link in PLAUSIBLE_LINKS exactly (enforced by an assertion in
# build_direct_matrix) -- no silent default grade.
RAW_JUDGMENTS = {
    "AF->EI": "High", "AF->II": "High", "AF->SJ": "High", "AF->SEAL": "High",
    "AF->HYD": "Medium", "AF->FR": "VeryHigh", "AF->SPA": "High",
    "AF->VS": "Medium", "AF->RE": "Medium",
    "EI->II": "Medium", "EI->FR": "High", "II->FR": "Medium",
    "SJ->SEAL": "High", "SEAL->SJ": "Low", "SJ->FR": "High",
    "SEAL->FR": "High", "HYD->FR": "High", "HYD->ER": "High", "SJ->ER": "Medium",
    "UF->SJ": "High", "UF->SEAL": "High", "UF->HYD": "Medium", "UF->FR": "Medium",
    "OPC->EI": "Medium", "OPC->II": "Medium",
    "MC->SEAL": "High", "MC->SJ": "Medium", "MC->HYD": "Medium", "MC->EI": "Medium",
    "MQ->SEAL": "High", "MQ->HYD": "High", "MC->FR": "Medium", "MQ->FR": "Medium",
    "SPA->RE": "High", "VS->SPA": "High", "VS->MQ": "Medium", "VS->MC": "Low",
}


def build_direct_matrix():
    """Build the fuzzy direct-influence matrix as three N x N arrays (l, m, u)."""
    # Guard the screening<->strength handoff: a judgment for a link that was
    # screened out, or a plausible link missing its judgment, is a data-entry
    # error once real expert input replaces the placeholders -- fail loudly
    # instead of silently dropping/defaulting it.
    judged_not_plausible = set(RAW_JUDGMENTS) - PLAUSIBLE_LINKS
    assert not judged_not_plausible, (
        f"RAW_JUDGMENTS has grades for links not in PLAUSIBLE_LINKS "
        f"(screened out but judged): {judged_not_plausible}")
    plausible_not_judged = PLAUSIBLE_LINKS - set(RAW_JUDGMENTS)
    assert not plausible_not_judged, (
        f"PLAUSIBLE_LINKS has links with no strength grade in RAW_JUDGMENTS "
        f"(would silently default to 'Medium'): {plausible_not_judged}")

    L = np.zeros((N, N)); M = np.zeros((N, N)); U = np.zeros((N, N))
    for link in PLAUSIBLE_LINKS:
        a, b = link.split("->")
        i, j = IDX[a], IDX[b]
        l, m, u = TFN[RAW_JUDGMENTS[link]]
        L[i, j], M[i, j], U[i, j] = l, m, u
    return L, M, U


def fuzzy_dematel(L, M, U):
    """
    Component-wise fuzzy DEMATEL (NOT the CFCS method -- CFCS defuzzifies
    before building the total-influence matrix, which would violate the
    "defuzzify once, at the end" decision for this project; see
    DEMATEL-ANP-TOPSIS.md S4.5). Here l, m, u are each normalized and carried
    through T = N(I-N)^-1 as separate matrices, using one shared scale factor
    so the TFN shape (l<=m<=u) is preserved throughout.
    Returns fuzzy T (Tl,Tm,Tu) and, for reporting only, the crisp D+R, D-R
    from a centroid of T.
    """
    # --- Normalization factor: largest row/column sum across the matrices ---
    # s = 1/max(row sums, col sums) of the upper-bound matrix U (L and M are
    # dominated by U elementwise, so U alone determines the factor).
    def norm_factor(X):
        row_sums = X.sum(axis=1)
        col_sums = X.sum(axis=0)
        return max(row_sums.max(), col_sums.max())

    # A small safety margin (1%) keeps the normalized matrix strictly below
    # the s=1/max(...) boundary, where the max row/col sum would land at
    # exactly 1.0 and (I-N) could be singular or ill-conditioned. Harmless
    # with the current sparse placeholder data (spectral radius << 1) but
    # protects against denser/stronger real expert judgments later.
    s = 1.0 / (max(norm_factor(L), norm_factor(M), norm_factor(U)) * 1.01)
    Nl, Nm, Nu = L * s, M * s, U * s

    I = np.eye(N)

    # --- Total-influence matrix  T = N (I - N)^-1  (per component) ---
    # Fuzzy inversion is approximated component-wise (standard practical method).
    for name, Nx in (("L", Nl), ("M", Nm), ("U", Nu)):
        cond = np.linalg.cond(I - Nx)
        assert cond < 1e8, (
            f"(I - N_{name}) is ill-conditioned (cond={cond:.3e}); the "
            f"total-influence matrix would be numerically unreliable. "
            f"Check for near-singular influence data.")

    Tl = Nl @ np.linalg.inv(I - Nl)
    Tm = Nm @ np.linalg.inv(I - Nm)
    Tu = Nu @ np.linalg.inv(I - Nu)

    # --- Defuzzify T (centroid) for D+R / D-R analysis ---
    Tcrisp = (Tl + Tm + Tu) / 3.0

    D = Tcrisp.sum(axis=1)   # row sums = influence GIVEN (dispatcher)
    R = Tcrisp.sum(axis=0)   # col sums = influence RECEIVED (receiver)

    prominence = D + R       # D+R : how central the factor is
    relation   = D - R       # D-R : >0 net cause, <0 net effect

    return (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation


def report_stage1_dematel(D, R, prominence, relation):
    print("=" * 74)
    print("STAGE 1 - FUZZY DEMATEL  (synthetic placeholder data)")
    print("=" * 74)
    print(f"{'Code':<6}{'Cluster':<14}{'D (give)':>9}{'R (recv)':>9}"
          f"{'D+R':>8}{'D-R':>8}  Role")
    print("-" * 74)
    order = np.argsort(-prominence)  # most prominent first
    for i in order:
        role = "CAUSE" if relation[i] > 0 else "effect"
        print(f"{CODES[i]:<6}{CLUSTER[CODES[i]]:<14}"
              f"{D[i]:>9.3f}{R[i]:>9.3f}{prominence[i]:>8.3f}"
              f"{relation[i]:>8.3f}  {role}")
    print("-" * 74)

    causes = [CODES[i] for i in range(N) if relation[i] > 0]
    effects = [CODES[i] for i in range(N) if relation[i] <= 0]
    print(f"\nNet CAUSES  (drivers,  D-R > 0): {', '.join(causes)}")
    print(f"Net EFFECTS (receivers, D-R <=0): {', '.join(effects)}")

    # Acceptance check (BUILD_BRIEF_for_Claude_Code.md): AF must be the
    # dominant cause, FR the dominant effect. This is only guaranteed for the
    # current synthetic placeholder data -- check it live rather than
    # narrating it, so a future data change that breaks it is caught, not
    # papered over with reassuring text.
    top_cause = CODES[int(np.argmax(relation))]
    dominant_effect = CODES[int(np.argmin(relation))]
    print(f"\nDominant cause factor (highest D-R): {top_cause} "
          f"({NAME[top_cause]})")
    if top_cause == "AF":
        print("  -> AF (Aging) is the dominant cause, as expected: validates "
              "its placement\n     under Mechanical with DEMATEL cross-effects.")
    else:
        print(f"  -> WARNING: expected AF (Aging) to be the dominant cause; "
              f"got {top_cause}. Acceptance check FAILED -- investigate the "
              f"influence data before proceeding to Stage 2.")

    fr_i = IDX["FR"]
    print(f"\nFailure Rate (FR) relation D-R = {relation[fr_i]:+.3f} "
          f"-> {'CAUSE' if relation[fr_i] > 0 else 'net EFFECT'}")
    if dominant_effect == "FR":
        print("  -> FR is the dominant net effect, as expected (sensible-"
              "behavior check).")
    else:
        print(f"  -> WARNING: expected FR to be the dominant net effect; "
              f"got {dominant_effect}. Acceptance check FAILED -- investigate "
              f"the influence data before proceeding to Stage 2.")


# ============================================================================
# STAGE 2 of 4: FUZZY ANP  (DEMATEL-based ANP, i.e. DANP)
# ============================================================================
# Take Stage 1's fuzzy total-influence matrix T = (Tl, Tm, Tu) and turn the
# DEMATEL influence structure into interdependency-aware CRITERIA WEIGHTS:
#   1. Column-normalize T -> the weighted supermatrix.
#   2. Raise the supermatrix to successive powers until it converges
#      (columns stabilize / become identical) -> the limit supermatrix.
#   3. The stabilized column = the criteria weights (sums to 1).
#   4. Roll up sub-criterion weights into cluster weights.
# Kept fuzzy through the supermatrix (Tl, Tm, Tu each powered independently,
# component-wise); defuzzified (centroid) only at the very end, per the
# "defuzzify once, at the end" decision (DEMATEL-ANP-TOPSIS.md S4.5).
# ============================================================================

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


def report_stage2_anp(w_crisp, fuzzy_components, dangling_codes, n_squarings):
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


# ============================================================================
# STAGE 3 of 4: TOPSIS
# ============================================================================
# Rank the loading arms by reliability-on-demand, using Stage 2's ANP
# criteria weights and each arm's per-sub-criterion condition score:
#   1. Decision matrix: rows = arms, cols = 15 sub-criteria, entries in
#      {0, 3.33, 6.67, 10} (higher = better; cost-type quantities already
#      inverted at the scoring stage).
#   2. Vector-normalize each column.
#   3. Weight by the ANP weights.
#   4. Ideal best/worst = column max/min (all criteria benefit-type).
#   5. Separation distances S+, S- from ideal best/worst.
#   6. Closeness C_i = S-_i / (S+_i + S-_i) in [0,1] -> x100 = 0-100
#      reliability-on-demand index.
#   7. Rank by the index; map to 5 replacement zones by FIXED score-band
#      thresholds (config constant, not statistical/rank-based).
# Runs entirely on CRISP numbers -- the fuzzy/crisp boundary is at the end
# of ANP (Stage 2), not here.
#
# STATUS: FRAMEWORK + PLACEHOLDER ARM DATA. This project's planning docs
# reference Alarfaj (2023)'s real per-arm scores for the 8 shared criteria,
# but that source report is not available in this repo. ARM_SCORES below is
# therefore SYNTHETIC placeholder data for all 15 sub-criteria (not just the
# 7 added ones) so the pipeline runs end-to-end today -- replace with real
# inspection/expert data later; nothing else needs to change. Zone
# thresholds are provisional placeholders too.
# ============================================================================

# Score-band zone thresholds (PROVISIONAL -- calibrate to the real TOPSIS
# score distribution once real data exists). Fixed, not statistical/
# rank-based: an arm's zone depends only on its own score, not on the other
# arms in the batch.
ZONE_THRESHOLDS = {1: 80, 2: 60, 3: 40, 4: 20}  # score >= threshold -> that zone; else zone 5

ZONE_RISK = {1: "Very low", 2: "Low", 3: "Mid", 4: "High", 5: "Very high"}
ZONE_ACTION = {
    1: "No action required",
    2: "No action required",
    3: "Expand/improve inspection; RCA on low-scoring criteria; develop & monitor action plan",
    4: "Plan replacement at next shutdown; use only when demand is high and no alternative",
    5: "Take out of service immediately; replace",
}

ARMS = ["LA-403", "LA-410", "LA-409", "LA-402", "LA-303", "LA-312"]

# Each arm: sub-criterion code -> score in {0, 3.33, 6.67, 10} (higher=better).
# Spans a deliberately wide condition range (near-new to end-of-life) so the
# placeholder pipeline exercises all 5 zones, not just the middle ones.
ARM_SCORES = {
    "LA-403": {  # near-new, well-supported
        "EI": 10, "II": 10, "SJ": 10, "SEAL": 10, "HYD": 10, "ER": 10,
        "AF": 10, "OPC": 10, "UF": 6.67, "FR": 10,
        "MC": 10, "MQ": 10,
        "SPA": 10, "VS": 10, "RE": 6.67,
    },
    "LA-410": {  # good condition, moderate use
        "EI": 6.67, "II": 6.67, "SJ": 6.67, "SEAL": 6.67, "HYD": 6.67, "ER": 10,
        "AF": 6.67, "OPC": 10, "UF": 3.33, "FR": 6.67,
        "MC": 6.67, "MQ": 6.67,
        "SPA": 6.67, "VS": 6.67, "RE": 6.67,
    },
    "LA-409": {  # aging, degraded, poor supportability
        "EI": 3.33, "II": 3.33, "SJ": 0, "SEAL": 3.33, "HYD": 3.33, "ER": 3.33,
        "AF": 0, "OPC": 6.67, "UF": 0, "FR": 0,
        "MC": 3.33, "MQ": 3.33,
        "SPA": 3.33, "VS": 0, "RE": 3.33,
    },
    "LA-402": {  # solid mid-life, well maintained
        "EI": 6.67, "II": 10, "SJ": 6.67, "SEAL": 10, "HYD": 6.67, "ER": 6.67,
        "AF": 6.67, "OPC": 6.67, "UF": 6.67, "FR": 6.67,
        "MC": 10, "MQ": 6.67,
        "SPA": 6.67, "VS": 10, "RE": 10,
    },
    "LA-303": {  # mid-poor, obsolescence-driven risk
        "EI": 3.33, "II": 6.67, "SJ": 3.33, "SEAL": 3.33, "HYD": 6.67, "ER": 6.67,
        "AF": 3.33, "OPC": 3.33, "UF": 3.33, "FR": 3.33,
        "MC": 3.33, "MQ": 3.33,
        "SPA": 0, "VS": 0, "RE": 0,
    },
    "LA-312": {  # end-of-life, replace-now candidate
        "EI": 0, "II": 0, "SJ": 0, "SEAL": 0, "HYD": 3.33, "ER": 0,
        "AF": 0, "OPC": 3.33, "UF": 0, "FR": 0,
        "MC": 0, "MQ": 3.33,
        "SPA": 0, "VS": 0, "RE": 0,
    },
}

VALID_SCORES = {0, 3.33, 6.67, 10}


def build_decision_matrix():
    """Assemble the arms x sub-criteria decision matrix X, in CODES order."""
    for arm in ARMS:
        missing = set(CODES) - set(ARM_SCORES[arm])
        extra = set(ARM_SCORES[arm]) - set(CODES)
        assert not missing, f"{arm} is missing scores for: {missing}"
        assert not extra, f"{arm} has scores for unknown sub-criteria: {extra}"
        bad = {c: v for c, v in ARM_SCORES[arm].items() if v not in VALID_SCORES}
        assert not bad, f"{arm} has scores outside {{0, 3.33, 6.67, 10}}: {bad}"

    X = np.array([[ARM_SCORES[arm][code] for code in CODES] for arm in ARMS], dtype=float)
    return X


def topsis(X, w):
    """
    Crisp TOPSIS. X: arms x criteria decision matrix. w: ANP weight vector
    (sums to 1, all-benefit orientation already baked into X's scoring).
    Returns (index_0_100, C, S_plus, S_minus).
    """
    col_norm = np.sqrt((X ** 2).sum(axis=0))
    assert np.all(col_norm > 0), (
        "A criterion is scored 0 for every arm -- vector normalization "
        "(division by column norm) is undefined for that column.")
    R = X / col_norm                      # vector normalization
    V = R * w                             # weighted normalized matrix

    A_plus = V.max(axis=0)                # ideal best (all criteria benefit-type)
    A_minus = V.min(axis=0)               # ideal worst

    S_plus = np.sqrt(((V - A_plus) ** 2).sum(axis=1))
    S_minus = np.sqrt(((V - A_minus) ** 2).sum(axis=1))

    denom = S_plus + S_minus
    # denom==0 only if every arm is simultaneously the ideal best AND worst
    # on every criterion, i.e. all arms score identically everywhere.
    if np.any(denom <= 1e-12):
        print("WARNING: at least one arm has S+ + S- == 0 (ties the ideal "
              "best and worst); closeness set to 0.5 for that arm.")
    C = np.where(denom > 1e-12, S_minus / denom, 0.5)

    index = C * 100.0
    assert np.all((index >= -1e-9) & (index <= 100 + 1e-9)), (
        f"Reliability index outside [0, 100]: {index}")
    return index, C, S_plus, S_minus


def zone_for_score(score):
    """Fixed score-band zone assignment (absolute, not rank-based)."""
    if score >= ZONE_THRESHOLDS[1]:
        return 1
    if score >= ZONE_THRESHOLDS[2]:
        return 2
    if score >= ZONE_THRESHOLDS[3]:
        return 3
    if score >= ZONE_THRESHOLDS[4]:
        return 4
    return 5


def report_stage3_topsis(index, w):
    print("=" * 88)
    print("STAGE 3 - TOPSIS  (ANP weights from Stage 2; SYNTHETIC placeholder arm data)")
    print("=" * 88)
    order = np.argsort(-index)
    print(f"{'Rank':<6}{'Arm':<10}{'Index (0-100)':>15}{'Zone':>6}{'Risk':>12}   Action")
    print("-" * 88)
    for rank, i in enumerate(order, start=1):
        arm = ARMS[i]
        zone = zone_for_score(index[i])
        print(f"{rank:<6}{arm:<10}{index[i]:>15.2f}{zone:>6}{ZONE_RISK[zone]:>12}   "
              f"{ZONE_ACTION[zone]}")
    print("-" * 88)

    print(f"\nZone thresholds (provisional, config constant): {ZONE_THRESHOLDS}")
    print("[Reminder: score-band, fixed thresholds -- an arm's zone does not "
          "depend on which other arms are in the batch.]")

    print("\nTop 5 criteria driving the ANP weights used here:")
    top5 = np.argsort(-w)[:5]
    for i in top5:
        print(f"  {CODES[i]:<6}{NAME[CODES[i]]:<45}{100*w[i]:>6.2f}%")

    # Acceptance checks (BUILD_BRIEF_for_Claude_Code.md): 0-100 index, full
    # ranking of the 6 arms, zone assignments.
    assert len(index) == len(ARMS)
    assert np.all((index >= 0) & (index <= 100))
    print(f"\n[Acceptance check OK: {len(ARMS)}-arm ranking produced, index in [0,100], "
          f"zones assigned.]")


# ============================================================================
# STAGE 4 of 4: MONTE CARLO ROBUSTNESS -- Approach 1 (weight-perturbation)
# ============================================================================
# Quantify how sensitive the Stage 3 TOPSIS ranking/zones/index are to
# uncertainty in the ANP criteria weights (Stage 2):
#   - Perturb the ANP weight vector by a +/-15% relative band per criterion,
#     renormalize to sum 1, and re-run TOPSIS -- 10,000 times (config
#     constants).
#   - Report: ranking stability, zone stability, zone-boundary crossings,
#     and per-arm score distribution (mean + 5th-95th percentile CI).
# Latin Hypercube Sampling is used if scipy is available, else simple random
# (not load-bearing to the result).
#
# Approach 2 (sparse failure-rate scenario generation) is explicitly
# DEFERRED per the companion doc -- a stub/hook is left below, not built.
# ============================================================================

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
        index_r, C_r, S_plus_r, S_minus_r = topsis(X, w_runs[r])
        indices[r] = index_r
        order = np.argsort(-index_r)
        rank_of_arm = np.empty(n_arms, dtype=int)
        rank_of_arm[order] = np.arange(1, n_arms + 1)
        ranks[r] = rank_of_arm
        zones[r] = [zone_for_score(s) for s in index_r]

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


def report_stage4_montecarlo(summary, base_index, base_ranks, base_zones, band, n_runs):
    print("=" * 92)
    print(f"STAGE 4 - MONTE CARLO (Approach 1: weight-perturbation, +/-{band*100:.0f}%, "
          f"{n_runs:,} runs)")
    print("=" * 92)

    order = np.argsort(-base_index)
    print(f"\n{'Arm':<10}{'Base idx':>10}{'Base rank':>11}{'Base zone':>11}"
          f"{'Mean idx':>10}{'5th pct':>10}{'95th pct':>10}{'Zone stab.':>12}")
    print("-" * 92)
    for i in order:
        print(f"{ARMS[i]:<10}{base_index[i]:>10.2f}{base_ranks[i]:>11}{base_zones[i]:>11}"
              f"{summary['score_mean'][i]:>10.2f}{summary['score_p05'][i]:>10.2f}"
              f"{summary['score_p95'][i]:>10.2f}{100*summary['zone_stability'][i]:>11.1f}%")
    print("-" * 92)

    print("\nRanking stability (% of runs each arm held each rank, 1=best):")
    header = "".join(f"{'R'+str(r):>8}" for r in range(1, len(ARMS) + 1))
    print(f"{'Arm':<10}{header}")
    for i in order:
        row = "".join(f"{100*summary['rank_stability'][i, r]:>7.1f}%" for r in range(len(ARMS)))
        print(f"{ARMS[i]:<10}{row}")

    print("\nZone-boundary crossings per arm (all zones visited under perturbation):")
    for i in order:
        visits = summary["zone_visits"][i]
        parts = ", ".join(f"Z{z}: {100*p:.1f}%" for z, p in sorted(visits.items()))
        flag = "" if len(visits) == 1 else "  <-- crosses zone boundaries under perturbation"
        print(f"  {ARMS[i]:<10}{parts}{flag}")


def report_band_comparison(band_results):
    """Short cross-band summary, per the brief's ask to also run +/-10%/+/-20%
    to show conclusions aren't an artifact of the single +/-15% choice."""
    print("\n" + "=" * 92)
    print("Cross-band comparison (does the +/-15% conclusion hold at +/-10% / +/-20%?)")
    print("=" * 92)
    print(f"{'Arm':<10}" + "".join(f"{'+/-'+str(int(b*100))+'%':>14}" for b in band_results))
    for i in range(len(ARMS)):
        row = "".join(f"{100*band_results[b]['zone_stability'][i]:>13.1f}%" for b in band_results)
        print(f"{ARMS[i]:<10}{row}   (zone stability)")


# ============================================================================
# PIPELINE ORCHESTRATION -- runs Stage 1 -> 2 -> 3 -> 4 end to end
# ============================================================================

def main():
    # ---- Stage 1: Fuzzy DEMATEL ----
    L, M, U = build_direct_matrix()
    (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation = fuzzy_dematel(L, M, U)
    report_stage1_dematel(D, R, prominence, relation)
    np.savez("stage1_outputs.npz",
             codes=np.array(CODES), Tl=Tl, Tm=Tm, Tu=Tu,
             T_crisp=Tcrisp, D=D, R=R, prominence=prominence, relation=relation)
    print("\n[Saved stage1_outputs.npz (fuzzy Tl/Tm/Tu + crisp T).]\n")

    # ---- Stage 2: Fuzzy ANP (DANP) ----
    w0, (wl, wm, wu), dangling_codes, n_squarings = run_anp(Tl, Tm, Tu)
    report_stage2_anp(w0, (wl, wm, wu), dangling_codes, n_squarings)
    np.savez("stage2_outputs.npz",
             codes=np.array(CODES), w=w0, wl=wl, wm=wm, wu=wu,
             dangling_codes=np.array(dangling_codes))
    print("\n[Saved stage2_outputs.npz (ANP criteria weights).]\n")

    # ---- Stage 3: TOPSIS ----
    X = build_decision_matrix()
    base_index, base_C, base_Splus, base_Sminus = topsis(X, w0)
    report_stage3_topsis(base_index, w0)
    order = np.argsort(-base_index)
    base_ranks = np.empty(len(base_index), dtype=int)
    base_ranks[order] = np.arange(1, len(base_index) + 1)
    base_zones = np.array([zone_for_score(s) for s in base_index])
    np.savez("stage3_outputs.npz",
             arms=np.array(ARMS), codes=np.array(CODES),
             decision_matrix=X, weights=w0,
             index=base_index, C=base_C, S_plus=base_Splus, S_minus=base_Sminus,
             ranking=np.array(ARMS)[order], zones=base_zones)
    print("\n[Saved stage3_outputs.npz (ranking, index, zones).]\n")

    # ---- Stage 4: Monte Carlo (Approach 1) ----
    band_results = {}
    for band in COMPARISON_BANDS:
        indices, ranks, zones = run_monte_carlo(X, w0, band=band)
        band_results[band] = summarize(indices, ranks, zones, base_zones)

    report_stage4_montecarlo(band_results[PERTURBATION_BAND], base_index, base_ranks,
                              base_zones, PERTURBATION_BAND, N_RUNS)
    report_band_comparison(band_results)

    summary = band_results[PERTURBATION_BAND]
    np.savez("stage4_outputs.npz",
             arms=np.array(ARMS),
             base_index=base_index, base_ranks=base_ranks, base_zones=base_zones,
             score_mean=summary["score_mean"], score_p05=summary["score_p05"],
             score_p95=summary["score_p95"], zone_stability=summary["zone_stability"],
             rank_stability=summary["rank_stability"])
    print("\n[Saved stage4_outputs.npz (Monte Carlo robustness summary, +/-15% band).]")


if __name__ == "__main__":
    main()
