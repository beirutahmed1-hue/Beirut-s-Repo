# Build Brief — Loading Arm Reliability-on-Demand Model (for Claude Code)

*Hand this to Claude Code together with `stage1_fuzzy_dematel.py`. It is self-contained: everything needed to build Stages 2–3 and wire the pipeline together is here. Companion planning docs (methodology, criteria spec, DEMATEL-ANP-TOPSIS, MC approaches) hold the full reasoning if deeper context is wanted, but are not required to build.*

---

## What this project is

A decision-support model that assesses the **reliability-on-demand** of marine/crude-oil loading arms and ranks them for replacement priority. It advances a prior KFUPM AHP model (Alarfaj 2023) by (a) modelling criteria **interdependency** with fuzzy DEMATEL-ANP instead of plain AHP, and (b) adding a Monte Carlo robustness layer.

**Pipeline:** FMECA (offline, defines criteria) → **Fuzzy DEMATEL** (Stage 1) → **Fuzzy ANP** (Stage 2) → **TOPSIS** (Stage 3) → **Monte Carlo** weight-perturbation robustness. Output: a 0–100 reliability-on-demand index per arm, a ranking, and replacement zones.

**Current status:** Stage 1 is written and verified (`stage1_fuzzy_dematel.py`). Experts are not yet available, so all expert inputs are **synthetic placeholders** clearly marked for later replacement. Build the rest the same way — runs end-to-end today, real data swaps in later.

---

## Language & structure

- **Python.** Keep it dependency-light: `numpy` required; `matplotlib` optional (cause-effect diagram, score charts). Avoid heavy frameworks.
- Suggested layout:
  ```
  loading_arm_model/
    common.py          # hierarchy, TFN scale, shared helpers
    stage1_dematel.py  # (exists — refactor to import from common)
    stage2_anp.py      # build
    stage3_topsis.py   # build
    montecarlo.py      # build (Approach 1)
    run_pipeline.py    # orchestrates 1->2->3->MC, prints/【saves results
    data/              # placeholder inputs, structured for later real data
  ```
- Refactor the hierarchy + TFN scale out of Stage 1 into `common.py` so all stages share one definition.

---

## The criteria hierarchy (5 clusters, 15 sub-criteria)

Fixed. Codes are the row/column labels throughout.

| Cluster | Sub-criteria (code) |
|---|---|
| Corrosion / External Integrity | External Integrity (EI), Internal Integrity (II) |
| Mechanical Integrity | Swivel Joint (SJ), Seal Integrity (SEAL), Hydraulic/Control (HYD), Emergency Release (ER), Aging (AF) |
| Operational Performance | Operation Perf. Compliance (OPC), Utilization Frequency (UF), Failure Rate (FR) |
| Maintenance | PM Compliance (MC), Maintenance Execution Quality (MQ) |
| Obsolescence & Supportability | Spare Parts Availability (SPA), Vendor Support (VS), Reverse Engineering (RE) |

Branches: clusters 1–4 = Condition; cluster 5 = Obsolescence.

---

## Key method decisions (already made — implement as-is)

**Fuzzy-only DANP, Triangular Fuzzy Numbers (TFNs).** Influence judgments use a 5-grade linguistic scale on normalized [0,1]:

| Grade | TFN (l, m, u) |
|---|---|
| No | (0, 0, 0.25) |
| Low | (0, 0.25, 0.5) |
| Medium | (0.25, 0.5, 0.75) |
| High | (0.5, 0.75, 1.0) |
| Very High | (0.75, 1.0, 1.0) |

- Screened-out / no-link cells = fuzzy zero (0,0,0).
- **Defuzzification: centroid**, which for a TFN is `(l+m+u)/3`. **Defuzzify once, at the end** — after fuzzy ANP produces fuzzy weights, before TOPSIS. Not earlier.

**DEMATEL (Stage 1 — done):** screened sub-criterion level. Only "plausible" directed links get a strength grade; all other directed pairs = fuzzy zero. Directionality matters (A→B ≠ B→A). Produces total-influence matrix T, and per-factor D+R (prominence) and D−R (relation → cause if >0, effect if ≤0). Verified behaviour: **AF is the dominant cause; FR is the dominant effect** — preserve this as a sanity check.

**ANP (Stage 2 — build):** use the DEMATEL total-influence matrix to build the network/supermatrix, i.e. DEMATEL-based ANP (DANP). Steps:
1. Take T (fuzzy or its defuzzified form) from Stage 1.
2. Normalize T by columns (each column sums to 1) to get the normalized influence/weighted supermatrix.
3. Raise the (crisp, normalized) supermatrix to successive powers until it converges (columns stabilize / become identical) → the **limit supermatrix**.
4. The stabilized column = the **criteria weights** (global weights across all 15 sub-criteria; also derive cluster weights by summing within-cluster).
5. If kept fuzzy through the supermatrix, defuzzify the final weights with centroid here. (Simpler acceptable approach: defuzzify T at the end of Stage 1, run a crisp supermatrix in Stage 2 — document whichever is chosen.)
Output: a weight vector over the 15 sub-criteria, summing to 1.

**TOPSIS (Stage 3 — build):** ranks the loading arms using the ANP weights.
1. Decision matrix: rows = arms, cols = 15 sub-criteria, entries = each arm's sub-criterion **score** (0/3.33/6.67/10 — see scoring below). All scores oriented so higher = better condition.
2. Vector-normalize each column: `r_ij = x_ij / sqrt(sum_i x_ij^2)`.
3. Weight: `v_ij = w_j * r_ij` (w from ANP).
4. Ideal best A+ = max per column, ideal worst A− = min per column (all criteria are benefit-type since higher=better).
5. Distances `S+_i = sqrt(sum_j (v_ij - A+_j)^2)`, `S−_i` likewise.
6. Closeness `C_i = S−_i / (S+_i + S−_i)` ∈ [0,1]. Scale to **0–100** as the reliability-on-demand index.
7. Rank by C_i (higher = more reliable). Map to **5 replacement zones** by **score-band with FIXED, configurable thresholds** (not statistical, not rank-based). Provisional starting bands: ≥80 Z1, 60–80 Z2, 40–60 Z3, 20–40 Z4, <20 Z5 — placeholders, calibrate to actual TOPSIS score distribution (closeness coefficients cluster toward the middle, so don't assume naive 20-pt bins hold). Thresholds live in a config constant. Attach Alarfaj-style actions per zone (Z1/2 no action; Z3 inspect/RCA/plan; Z4 plan replacement at shutdown; Z5 replace now).

**Monte Carlo — Approach 1 (build):** weight-perturbation robustness. **Finalized parameters:**
- Perturb the ANP sub-criterion weights by a **±15% relative band** (make the band a config constant so ±10% / ±20% can also be run), renormalize each perturbed vector to sum 1, re-run TOPSIS.
- **10,000 runs** (config constant). **Latin Hypercube Sampling** if readily available (scipy), else simple random.
- Report all four: **ranking stability** (% of runs each arm held each rank), **zone stability** (% in base zone + any boundary crossings), and **per-arm score distribution** (mean + 5th–95th percentile CI on the 0–100 index).
- **Approach 2 (sparse-data failure-rate scenarios): DEFERRED** — leave a clearly-marked stub/hook only; do **not** build yet (no real failure records available; worth building only after an FR-sensitivity check on real data). If built later: bootstrap or Bayesian updating, never a raw Weibull fit to ~5 points. (See MC companion doc.)

**AHP benchmark (core deliverable — build):** compute plain-AHP weights on the same 15 criteria (replicating the Alarfaj approach: pairwise comparison matrix → normalized → weights → consistency ratio) and run TOPSIS with those AHP weights on the same arms. Report side-by-side: AHP vs. DANP weights per criterion, AHP vs. DANP ranking per arm, and where/why they diverge. This is the contribution-focused finding (what interdependency modelling changes) and simultaneously the primary validation benchmark — not optional.

---

## Scoring scales (for the TOPSIS decision matrix)

Each arm supplies, per sub-criterion, a score in {0, 3.33, 6.67, 10} (higher = better). Quantitative sub-criteria map a raw value to a band; qualitative ones are scored directly by inspection/expert. Full band thresholds are in the **Criteria & Sub-Criteria Specification** doc. Alarfaj's 8 use his exact bands; the 7 added sub-criteria (II, SJ, SEAL, HYD, ER, UF, MQ) use **[ASSUMED]** placeholder bands pending validation — fine for building/testing.

For placeholder arm data, use **Alarfaj's 6 arms** (LA-403, LA-410, LA-409, LA-402, LA-303, LA-312) so results look familiar. Alarfaj's per-arm scores for his 8 criteria are in the source report/spec; assign reasonable placeholder scores for the 7 new sub-criteria. Structure the data file so real scores drop in later.

---

## What is placeholder vs. fixed

**Placeholder (swapped later, mark clearly):**
- The screened plausible-links set (screening result).
- The influence strength grades (expert judgments).
- Per-arm sub-criterion scores.
- The [ASSUMED] band thresholds for the 7 added sub-criteria.
- Zone thresholds.

**Fixed (the method — don't change without a decision):**
- Criteria hierarchy, TFN scale, centroid defuzzification, the DEMATEL/ANP/TOPSIS/MC math, higher=better orientation.

---

## Acceptance checks

- Whole pipeline runs end-to-end on placeholder data with one command (`run_pipeline.py`).
- Stage 1 still shows AF as dominant cause, FR as dominant effect.
- ANP weights sum to 1; all 15 sub-criteria present.
- TOPSIS produces a 0–100 index, a full ranking of the 6 arms, and zone assignments.
- Monte Carlo prints ranking/zone stability and per-arm CIs.
- Every placeholder input is labelled and isolated so swapping in real data needs no math changes.
- Keep viva-relevant steps commented (fuzzy inversion method, defuzzification point, normalization choices).

---

## Nice-to-have (if time)

- Cause-effect diagram (D+R vs D−R scatter) from Stage 1.
- Per-arm radar/bar chart of sub-criterion scores (Alarfaj-style).
- CSV/Excel export of the decision matrix and results.
