"""
============================================================================
LOADING ARM RELIABILITY-ON-DEMAND MODEL
Shared definitions: criteria hierarchy + TFN linguistic scale.
============================================================================
Used by every stage (DEMATEL, ANP, TOPSIS, Monte Carlo) so the hierarchy and
fuzzy scale are defined exactly once. See BUILD_BRIEF_for_Claude_Code.md.
============================================================================
"""

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

CLUSTERS = sorted(set(CLUSTER.values()), key=lambda c: [CLUSTER[code] for code in CODES].index(c))

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


def centroid(l, m, u):
    """Centroid defuzzification for a TFN: (l+m+u)/3."""
    return (l + m + u) / 3.0
