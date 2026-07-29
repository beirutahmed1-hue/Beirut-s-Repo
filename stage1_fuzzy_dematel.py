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
# Any plausible link not listed here defaults to "Medium".
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
    L = np.zeros((N, N)); M = np.zeros((N, N)); U = np.zeros((N, N))
    for link in PLAUSIBLE_LINKS:
        a, b = link.split("->")
        i, j = IDX[a], IDX[b]
        grade = RAW_JUDGMENTS.get(link, "Medium")
        l, m, u = TFN[grade]
        L[i, j], M[i, j], U[i, j] = l, m, u
    return L, M, U


# ---------------------------------------------------------------------------
# 4. FUZZY DEMATEL COMPUTATION
# ---------------------------------------------------------------------------
def fuzzy_dematel(L, M, U):
    """
    Standard fuzzy DEMATEL on triangular components.
    Each of l,m,u is normalized and processed; the CFCS/normalization here uses
    the common approach of normalizing by the largest row-sum of the upper
    bound (r), which keeps the three matrices consistently scaled.
    Returns fuzzy T (Tl,Tm,Tu) and the crisp D+R, D-R after defuzzification.
    """
    # --- Normalization factor: largest row sum across the matrices ---
    # Use max row sum of each component; the standard uses s = 1/max(row sums).
    def norm_factor(X):
        row_sums = X.sum(axis=1)
        col_sums = X.sum(axis=0)
        return max(row_sums.max(), col_sums.max())

    s = 1.0 / max(norm_factor(L), norm_factor(M), norm_factor(U))
    Nl, Nm, Nu = L * s, M * s, U * s

    I = np.eye(N)

    # --- Total-influence matrix  T = N (I - N)^-1  (per component) ---
    # Fuzzy inversion is approximated component-wise (standard practical method).
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

    top_cause = CODES[int(np.argmax(relation))]
    print(f"\nDominant cause factor (highest D-R): {top_cause} "
          f"({NAME[top_cause]})")
    print("  -> expected to be AF (Aging) with the placeholder data, "
          "validating\n     its placement under Mechanical with DEMATEL cross-effects.")

    fr_i = IDX["FR"]
    print(f"\nFailure Rate (FR) relation D-R = {relation[fr_i]:+.3f} "
          f"-> {'CAUSE' if relation[fr_i] > 0 else 'net EFFECT (as expected)'}")


def main():
    L, M, U = build_direct_matrix()
    (Tl, Tm, Tu), Tcrisp, D, R, prominence, relation = fuzzy_dematel(L, M, U)
    report(D, R, prominence, relation)

    # Save the defuzzified total-influence matrix + relation for Stage 2 (ANP).
    np.savez("stage1_outputs.npz",
             codes=np.array(CODES),
             T_crisp=Tcrisp, D=D, R=R,
             prominence=prominence, relation=relation)
    print("\n[Saved stage1_outputs.npz for Stage 2 (fuzzy ANP).]")


if __name__ == "__main__":
    main()
