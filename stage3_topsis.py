"""
============================================================================
LOADING ARM RELIABILITY-ON-DEMAND MODEL
Stage 3 of 3: TOPSIS
============================================================================

Purpose
-------
Rank the loading arms by reliability-on-demand, using Stage 2's ANP criteria
weights and each arm's per-sub-criterion condition score, per
BUILD_BRIEF_for_Claude_Code.md / DEMATEL-ANP-TOPSIS.md S4A:
  1. Decision matrix: rows = arms, cols = 15 sub-criteria, entries in
     {0, 3.33, 6.67, 10} (higher = better; cost-type quantities are already
     inverted at the scoring stage -- see Criteria_and_Subcriteria_Specification.md).
  2. Vector-normalize each column.
  3. Weight by the ANP weights (from Stage 2).
  4. Ideal best/worst = column max/min (all criteria benefit-type).
  5. Separation distances S+, S- from ideal best/worst.
  6. Closeness C_i = S-_i / (S+_i + S-_i) in [0,1] -> x100 = 0-100
     reliability-on-demand index.
  7. Rank by the index; map to 5 replacement zones by FIXED score-band
     thresholds (config constant, not statistical/rank-based).
Runs entirely on CRISP numbers -- the fuzzy/crisp boundary is at the end of
ANP (Stage 2), not here (DEMATEL-ANP-TOPSIS.md S4.5/S4A).

Status
------
FRAMEWORK + PLACEHOLDER ARM DATA. This project's planning docs reference
Alarfaj (2023)'s real per-arm scores for the 8 shared criteria, but that
source report is not available in this repo. ARM_SCORES below is therefore
SYNTHETIC placeholder data for all 15 sub-criteria (not just the 7 added
ones) so the pipeline runs end-to-end today -- replace with real inspection/
expert data later; nothing else needs to change. Zone thresholds are
provisional placeholders too (see Config constants).
============================================================================
"""

import numpy as np

from common import CODES, NAME, N, IDX
import stage1_fuzzy_dematel as stage1
import stage2_anp as stage2

# ---------------------------------------------------------------------------
# Config constants
# ---------------------------------------------------------------------------
# Score-band zone thresholds (PROVISIONAL -- calibrate to the real TOPSIS
# score distribution once real data exists; see DEMATEL-ANP-TOPSIS.md S4A/4B).
# Fixed, not statistical/rank-based: an arm's zone depends only on its own
# score, not on the other arms in the batch.
ZONE_THRESHOLDS = {1: 80, 2: 60, 3: 40, 4: 20}  # score >= threshold -> that zone; else zone 5

ZONE_RISK = {1: "Very low", 2: "Low", 3: "Mid", 4: "High", 5: "Very high"}
ZONE_ACTION = {
    1: "No action required",
    2: "No action required",
    3: "Expand/improve inspection; RCA on low-scoring criteria; develop & monitor action plan",
    4: "Plan replacement at next shutdown; use only when demand is high and no alternative",
    5: "Take out of service immediately; replace",
}

# ---------------------------------------------------------------------------
# Arm data  (SYNTHETIC PLACEHOLDER -- replace with real Alarfaj/inspection data)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def report(index, w):
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


def main():
    L, M, U = stage1.build_direct_matrix()
    (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation = stage1.fuzzy_dematel(L, M, U)
    w, (wl, wm, wu), dangling_codes, n_squarings = stage2.run_anp(Tl, Tm, Tu)

    X = build_decision_matrix()
    index, C, S_plus, S_minus = topsis(X, w)
    report(index, w)

    order = np.argsort(-index)
    np.savez("stage3_outputs.npz",
             arms=np.array(ARMS), codes=np.array(CODES),
             decision_matrix=X, weights=w,
             index=index, C=C, S_plus=S_plus, S_minus=S_minus,
             ranking=np.array(ARMS)[order],
             zones=np.array([zone_for_score(s) for s in index]))
    print("\n[Saved stage3_outputs.npz (ranking, index, zones) for Monte Carlo.]")


if __name__ == "__main__":
    main()
