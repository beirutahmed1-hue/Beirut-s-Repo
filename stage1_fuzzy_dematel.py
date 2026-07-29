"""
============================================================================
LOADING ARM RELIABILITY-ON-DEMAND MODEL
Stage 1 of 3: FUZZY DEMATEL
============================================================================

Purpose
-------
Take expert influence judgments among the criteria/sub-criteria (as linguistic
grades), convert them to Triangular Fuzzy Numbers (TFNs), and run fuzzy DEMATEL
to produce:
  - the fuzzy total-influence matrix T
  - each factor's prominence (D+R) and relation (D-R)
  - its cause/effect classification
This structure feeds Stage 2 (fuzzy ANP -> weights).

Status
------
FRAMEWORK + PLACEHOLDER DATA. Experts are not yet available. The influence
judgments below are SYNTHETIC placeholders so the pipeline runs end-to-end
today. Replace `RAW_JUDGMENTS` (and the screening set) with real expert input
later; nothing else needs to change.

Design decisions embedded here (see DEMATEL-ANP companion doc):
  - Fuzzy-only DANP, Triangular Fuzzy Numbers.
  - 5-grade linguistic scale on normalized [0,1]:
        No (0,0,.25) Low (0,.25,.5) Medium (.25,.5,.75)
        High (.5,.75,1) VeryHigh (.75,1,1)
  - Screened sub-criterion level: only "plausible" links get a strength grade;
    all other (directional) links are fixed at fuzzy zero.
  - Directionality matters: A->B is separate from B->A.
============================================================================
"""

import numpy as np

# ---------------------------------------------------------------------------
# 1. CRITERIA HIERARCHY  (5 clusters, 15 sub-criteria)
#    Codes are used as row/column labels throughout.
# ---------------------------------------------------------------------------
# Each sub-criterion: (code, full name, cluster)
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

# ---------------------------------------------------------------------------
# 2. TFN LINGUISTIC SCALE  (normalized [0,1])  -- decided mapping
# ---------------------------------------------------------------------------
TFN = {
    "No":       (0.0,  0.0,  0.25),
    "Low":      (0.0,  0.25, 0.50),
    "Medium":   (0.25, 0.50, 0.75),
    "High":     (0.50, 0.75, 1.00),
    "VeryHigh": (0.75, 1.00, 1.00),
}
FUZZY_ZERO = (0.0, 0.0, 0.0)   # screened-out / no-link cells

# ---------------------------------------------------------------------------
# 3. EXPERT INPUT  (SYNTHETIC PLACEHOLDER -- replace later)
# ---------------------------------------------------------------------------
# Screening: set of plausible DIRECTED links (A influences B) -> "A->B".
# Only these get a strength grade; every other directed pair = fuzzy zero.
# This placeholder set encodes physically sensible links (within-cluster +
# sensible cross-cluster), with aging (AF) deliberately influencing many.
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

# Strength grades for the plausible links (SYNTHETIC placeholder).
# Must cover every link in PLAUSIBLE_LINKS exactly (enforced by an assertion
# in build_direct_matrix) -- no silent default grade.
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


# ---------------------------------------------------------------------------
# 4. FUZZY DEMATEL COMPUTATION
# ---------------------------------------------------------------------------
def fuzzy_dematel(L, M, U):
    """
    Component-wise fuzzy DEMATEL (NOT the CFCS method -- CFCS defuzzifies
    before building the total-influence matrix, which would violate the
    "defuzzify once, at the end" decision for this project; see
    DEMATEL-ANP-TOPSIS.md S4.5). Here l, m, u are each normalized and carried
    through T = N(I-N)^-1 as separate matrices, using one shared scale factor
    so the TFN shape (l<=m<=u) is preserved throughout.
    Returns fuzzy T (Tl,Tm,Tu) and, for reporting only, the crisp D+R, D-R
    from a centroid of T (see the note on T_crisp in main()).
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


# ---------------------------------------------------------------------------
# 5. REPORTING
# ---------------------------------------------------------------------------
def report(D, R, prominence, relation):
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


def main():
    L, M, U = build_direct_matrix()
    (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation = fuzzy_dematel(L, M, U)
    report(D, R, prominence, relation)

    # Save both the fuzzy total-influence matrix (Tl, Tm, Tu) and its crisp
    # centroid for Stage 2. DESIGN DECISION (see DEMATEL-ANP-TOPSIS.md S4.5):
    # defuzzify once, at the very end, after fuzzy ANP -- not here. Tl/Tm/Tu
    # are therefore the authoritative handoff to Stage 2, which should run a
    # fuzzy supermatrix and only take the centroid of the *final* weights.
    # T_crisp is also saved for convenience/debugging (e.g. the D+R/D-R
    # report above), but Stage 2 must NOT treat it as the primary input --
    # doing so would collapse to a crisp-ANP fallback and discard the
    # uncertainty that is the whole point of going fuzzy.
    np.savez("stage1_outputs.npz",
             codes=np.array(CODES),
             Tl=Tl, Tm=Tm, Tu=Tu,
             T_crisp=Tcrisp, D=D, R=R,
             prominence=prominence, relation=relation)
    print("\n[Saved stage1_outputs.npz (fuzzy Tl/Tm/Tu + crisp T) for Stage 2 (fuzzy ANP).]")


if __name__ == "__main__":
    main()
