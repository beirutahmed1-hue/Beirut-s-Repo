# DEMATEL-ANP-TOPSIS (DANP + TOPSIS) — Method Reference & Design Decisions

*Companion document to the main methodology report. Consolidates everything about the DEMATEL, ANP, and TOPSIS stages of the loading arm reliability-on-demand model: what each method does, how they combine, and the design decisions made for this thesis.*

---

## 1. Role in the overall pipeline

The full pipeline is: **FMECA → DEMATEL-ANP (DANP) → (Weibull sub-model) → TOPSIS**, framed as reliability-on-demand.

DANP occupies the **weighting** stage. It takes the criteria hierarchy (5 clusters, 15 sub-criteria) and produces **interdependency-aware importance weights**, which TOPSIS then uses to rank the loading arms. DANP does not rank arms and does not score them — it only weights the criteria.

**Division of labor:**
- **DEMATEL** maps the *cause–effect structure* — which criteria influence which others, and how strongly (a directional influence network).
- **ANP** takes that structure and computes the *final weights*, accounting for direct and indirect interdependencies via a supermatrix.
- One-line: *DEMATEL tells ANP how the network is wired; ANP does the weighting math on that wired network.* The combination is called **DANP (DEMATEL-based ANP)**.

**Why DANP over plain AHP (the Alarfaj baseline):** AHP assumes criteria are independent and only captures *relative importance*. The loading-arm criteria are demonstrably interdependent — aging drives failure rate; aging/obsolescence drives spare-parts and vendor-support; maintenance compliance affects integrity; reverse engineering is a *response* to poor spare-parts/vendor-support. DEMATEL captures these directional cause–effect links; ANP turns them into weights. This is the single strongest methodological differentiator from Alarfaj.

---

## 2. DEMATEL — what it does and how

**Core question asked of experts:** for each ordered pair of factors, *"Does factor A directly influence factor B, and how strongly?"* on a **5-grade linguistic scale** mapped to **triangular fuzzy numbers** (see 4.5):
- No influence
- Low influence
- Medium influence
- High influence
- Very High influence

Each grade maps to a triangular fuzzy number (l, m, u) rather than a single crisp value, so the uncertainty around each judgment is carried through the computation.

**Directionality is the whole point:** A→B is assessed separately from B→A (aging→corrosion is strong; corrosion→aging is nil). A pairwise *importance* comparison (AHP) cannot represent this.

**Processing steps (standard DEMATEL):**
1. **Direct-influence matrix (D):** the filled-in grid of 0–4 judgments (screened-out cells = 0).
2. **Normalize** D (typically divide by the largest row sum) → normalized matrix N.
3. **Total-influence matrix (T):** T = N(I − N)⁻¹ — captures *indirect* influence (A→B→C ripples through), not just direct links.
4. **Prominence and relation per factor:**
   - **D+R (prominence):** total influence given + received → how central/important the factor is in the network.
   - **D−R (relation):** influence given minus received → **positive = net cause** (a driver), **negative = net effect** (a receiver).
5. **Cause–effect diagram:** plot factors on (D+R, D−R) axes — a standalone, intuitive thesis finding showing which factors drive reliability and which are driven.

---

## 3. ANP — what it does after DEMATEL

Once DEMATEL has produced the influence structure, **ANP converts it into weights**:
1. The total-influence matrix / normalized influence relationships define the **network structure** (which criteria connect to which) — replacing AHP's strict top-down hierarchy.
2. ANP builds a **supermatrix** capturing how much each criterion affects every other (direct + indirect).
3. The supermatrix is raised to successive powers until values **converge (stabilize)** — letting influence ripple through the network repeatedly.
4. The stabilized column values are the **final criteria weights** — the same *role* as AHP's eigenvector weights, but now reflecting network-wide influence rather than isolated pairwise importance.

These weights feed TOPSIS as the criteria weights for ranking the arms.

---

## 4. Design decisions for this thesis

### 4.1 Level of assessment — screened sub-criterion-level (two-stage)

Influence is assessed at the **sub-criterion level** for best cause–effect coverage, but a **plausibility screen** first removes non-relationships so expert effort concentrates on links that matter.

**Why not the alternatives:**
| Option | Judgments | Verdict |
|---|---|---|
| Cluster-only (5×5) | 20 | Standard & defensible but coarse — can't show *aging specifically* → corrosion |
| Hybrid (cluster + aging sub-links) | ~30–40 | Safe middle path; considered |
| Full unscreened sub-criterion (15×15) | 210 | Maximal resolution in theory, but fatigue-driven noise + wasted effort on ~150 non-relationships; quality collapses with a small pool |
| **Screened sub-criterion (chosen)** | ~40–60 (after screen) | Best coverage achievable *reliably* |

**Two-stage process:**
1. **Screening pass (binary, fast):** mark each potential directional link plausible / not plausible — *"could A influence B at all?"* — not strength yet. Structured by cluster pairs (within-cluster links + physically sensible cross-cluster links). Prunes 210 → ~40–60 realistic links.
2. **Strength assessment (0–4, careful):** only surviving links are rated for strength. Screened-out cells fixed at 0. Attention spent only on links that matter — no fatigue confirming zeros.

**Thesis framing sentence:** *"To balance interdependency coverage against elicitation reliability, a two-stage screened DEMATEL reduced the 210 candidate directional links via a binary plausibility screen to N realistic links, which were then assessed for influence strength."*

### 4.2 Aging links — special care

All aging→X links (→corrosion, →operational/failure rate, →obsolescence/spare parts) should survive screening into Stage 2 and be assessed carefully. Rationale: **"aging as the dominant cause factor" (high D−R) is a headline finding** and the justification for placing aging under Mechanical rather than duplicating it across clusters. This is where sub-criterion resolution earns its cost.

### 4.3 Failure Rate — expected as a net effect

Failure Rate is expected to appear with **high R, low D (net effect / receiver)** — corrosion, mechanical wear, and poor maintenance all *cause* failures. This is an *analysis output*, not a design choice; if it emerges as expected, it is a sensible-behavior check on the influence model.

### 4.4 Screening method

For a small expert pool, a **single consensus session** (panel agrees plausible/not together) is cleaner than individual-then-merged. If done individually, set a merge rule in advance (e.g. a link is kept if any expert marks it plausible).

### 4.5 Crisp vs. fuzzy — DECIDED: fuzzy-only, triangular fuzzy numbers (TFNs)

The DANP computation runs **fuzzy-only**, using **triangular fuzzy numbers (TFNs)** throughout DEMATEL and ANP.

**Rationale:** fuzzy carries expert uncertainty through the whole computation instead of discarding it (more comprehensive), matches how experts actually judge influence (inherently vague), is the current DANP research standard (cf. Arjomandi et al. 2021), and stacks a second differentiator on top of interdependency modeling (fuzzy DANP vs. Alarfaj's crisp AHP). TFNs specifically hit the master's-thesis sweet spot — genuinely fuzzy and well-precedented, but defensible without the difficulty of interval type-2 sets.

**How it works in practice:**
- **Inputs are the same 5 linguistic grades** experts would use anyway (No / Low / Medium / High / Very High). What changes is what each grade *becomes* in the math: instead of a single number (crisp: High = 3), each grade maps to a **triangular fuzzy number** — a (lower, peak, upper) range, e.g. High = (2.5, 3, 3.5) or a normalized equivalent — so the uncertainty band around each judgment is carried through every calculation.
- The DEMATEL steps (normalize, total-influence matrix T = N(I−N)⁻¹, D+R / D−R) and the ANP supermatrix all run in **fuzzy arithmetic**, with **defuzzification** (e.g. centroid method) collapsing to crisp weights only at the very end.

**What this commits to (accepted trade-offs):**
- **Heavier, error-prone computation** — fuzzy matrix normalization, fuzzy matrix inversion for T, and defuzzification are fiddly. Mitigation: follow a well-documented fuzzy DEMATEL-ANP reference implementation and verify fuzzy operations against a worked example from a paper.
- **Harder viva defense** — must be able to explain TFNs, the chosen membership functions, and defuzzification (centroid) under questioning. Examiners probe fuzzy methods specifically.
- A *broken* fuzzy model is worse than a correct crisp one — so implementation correctness is the priority, not just the choice of method.

**TFN membership mapping (decided — normalized [0,1] scale):**

| Linguistic grade | TFN (l, m, u) |
|---|---|
| No influence | (0, 0, 0.25) |
| Low | (0, 0.25, 0.5) |
| Medium | (0.25, 0.5, 0.75) |
| High | (0.5, 0.75, 1.0) |
| Very High | (0.75, 1.0, 1.0) |

- **Standard published mapping** (normalized fuzzy linguistic scale, widely used in fuzzy DEMATEL studies) — taken as-is rather than invented, for defensibility.
- **Endpoints clamped:** "No" and "Very High" are truncated at 0 and 1 (influence cannot be negative or exceed the maximum) — hence they are not symmetric like the middle three.
- **Adjacent-grade overlap is intentional** (e.g. Low's upper = 0.5 = Medium's peak) — it represents that the boundary between grades is itself vague. This is the point of fuzzy, not a bug.
- **Scale note:** a 0–4 version (No (0,0,1) … Very High (3,4,4)) is mathematically equivalent because DEMATEL normalizes the matrix early; final weights are identical. The [0,1] version was chosen for convention-match with recent literature and clean "degree of influence" reading.
- **Screened-out links** = fuzzy zero (0, 0, 0).

**Defuzzification — centroid method, at the fuzzy→crisp transition after ANP:**
- A criterion's fuzzy weight (l, m, u) is collapsed to a single crisp value by the centroid (center-of-gravity). For a triangular fuzzy number this reduces to the mean of the three parameters:

  crisp value = (l + m + u) / 3

- Example: fuzzy weight (0.12, 0.18, 0.25) → (0.12 + 0.18 + 0.25)/3 = **0.183**.
- General form (for defense): centroid = ∫x·μ(x)dx / ∫μ(x)dx; for a TFN this integrates to (l+m+u)/3. Note the fuzzy-DEMATEL literature's "BNP" (Best Non-fuzzy Performance) = l + (u−l)/3 + ... is the same value for these TFNs.
- **Timing is critical:** defuzzify **once, at the end** — after fuzzy DEMATEL and fuzzy ANP produce fuzzy weights, and before feeding TOPSIS. Defuzzifying earlier would discard the uncertainty and defeat the purpose of going fuzzy.

**Pipeline (fuzzy → crisp transition point):**
1. Experts give linguistic grades → mapped to TFNs (table above)
2. Fuzzy DEMATEL (all fuzzy arithmetic) → fuzzy total-influence matrix
3. Fuzzy ANP (fuzzy supermatrix) → fuzzy weights
4. **Defuzzify (centroid, (l+m+u)/3)** → crisp weights ← *the transition*
5. Crisp weights feed TOPSIS

---

## 4A. TOPSIS — the ranking stage (decided)

TOPSIS is the final stage: it takes the defuzzified ANP weights and the per-arm sub-criterion scores and produces a composite reliability-on-demand index and ranking. **TOPSIS runs entirely on crisp numbers** — the fuzzy→crisp boundary is at the end of ANP (see 4.5), so this is standard crisp TOPSIS, *not* fuzzy TOPSIS.

**Rationale for crisp TOPSIS:** the fuzziness belongs where the uncertainty is — the expert influence judgments that produce the weights. The arm scores come from inspection data mapped to defined 0/3.33/6.67/10 bands; they are not vague in the same way, so crisp TOPSIS on crisp scores is appropriate and cleaner to defend.

**Steps:**
1. **Decision matrix:** rows = arms, columns = 15 sub-criteria, entries = each arm's score in {0, 3.33, 6.67, 10}.
2. **Vector normalization:** `r_ij = x_ij / sqrt(Σ_i x_ij²)`.
3. **Apply weights:** `v_ij = w_j · r_ij`, where `w_j` are the defuzzified ANP weights.
4. **Ideal solutions:** ideal-best `A⁺_j = max_i v_ij`, ideal-worst `A⁻_j = min_i v_ij` (all criteria benefit-type — see below).
5. **Separation distances:** `S⁺_i = sqrt(Σ_j (v_ij − A⁺_j)²)`, `S⁻_i = sqrt(Σ_j (v_ij − A⁻_j)²)`.
6. **Closeness coefficient:** `C_i = S⁻_i / (S⁺_i + S⁻_i)` ∈ [0,1]; **×100 → 0–100 reliability-on-demand index** (matches Alarfaj's output style).
7. **Rank** by C_i (higher = more reliable); map to replacement zones (thresholds TBD — see main methodology doc).

**Design decisions:**

- **All criteria are benefit-type (higher = better)** — *on the score scale*. This is the subtle-but-important point: cost-direction quantities (Aging, Failure Rate — where a higher raw value is worse) are **inverted during the 0–10 scoring step**, per the defined bands (e.g. Age ≥ 25 yr → 0; Age < 5 yr → 10; failures ≥ 5 → 0; failures = 0 → 10). By the time a value enters TOPSIS it is already a score where 10 = good, so every column is benefit-type and ideal-best is always the max. **The cost→benefit inversion lives in the scoring/data-prep step, never inside TOPSIS.** TOPSIS stays a plain all-benefit routine; feeding raw age/failure counts straight in (without band conversion) would give wrong results — the scoring step is load-bearing and must be documented as where the inversion happens.

- **Vector normalization** (not min-max). Vector is the classic TOPSIS choice (Hwang & Yoon 1981), preserves relative proportions, and — decisive for this data — avoids two failure modes that min-max would hit here: (i) divide-by-zero when all arms score identically on a criterion (e.g. all six arms scored 10 on OPC in Alarfaj's data), and (ii) tie-exaggeration, where the discrete 0/3.33/6.67/10 bands produce many equal values that min-max would stretch to 0/1 extremes. Vector keeps ties proportional.

- **0–100 index** via C_i × 100 — presentation choice for continuity with Alarfaj's 0–100 output.

**VIKOR alternative:** TOPSIS was chosen over VIKOR for a clean 0–100 index. Switch to VIKOR only if an explicit compromise/acceptable-advantage replacement threshold is later required (see main methodology doc).

### Zone classification (decided)

The 0–100 reliability-on-demand index maps to **5 replacement zones** (keeping Alarfaj's framework for continuity and operational usefulness), each with a recommended action and risk level:

| Zone | Recommended action | Risk |
|---|---|---|
| Zone 1 | No action | Very low |
| Zone 2 | No action | Low |
| Zone 3 | Expand/improve inspection; RCA on low-performing criteria; develop & monitor action plan | Mid |
| Zone 4 | Plan replacement at next shutdown; use only when demand is high and no alternative | High |
| Zone 5 | Take out of service immediately; replace | Very high |

**Design decisions:**
- **Score-band classification (absolute), not rank-based.** An arm is assigned by its score band, not its position among the current batch — so an arm's zone does not change just because other arms are added to or removed from the comparison. This gives an absolute replacement signal, which is what a reliability-on-demand decision needs (an unreliable arm is unreliable regardless of its neighbours).
- **Fixed thresholds, not statistical.** Boundaries are fixed numbers (configurable constant in the code), not derived from the batch's mean/SD. Rationale: (i) fixed gives stable, memorizable, defensible cutoffs ("below X → replace") with absolute meaning; (ii) statistical thresholds are batch-dependent and need ~20+ data points to be stable — with only 6 arms, mean/SD are shaky and one extreme arm would move every boundary; (iii) the TOPSIS index is *already* relative (closeness to batch best/worst), so statistical thresholds on top would make zones doubly relative and drift further from an absolute readout.
- **Calibration caveat:** because the index is a TOPSIS closeness coefficient, C_i values tend to cluster mid-range and avoid the extremes (0/100), so naive 20-point bins may not match where real scores fall. Set the thresholds as a config constant, start with sensible bands, and **calibrate to the actual score distribution** once real data exists. Thesis position: *"5-zone framework with action recommendations; thresholds set as configurable parameters calibrated to the TOPSIS score distribution; final thresholds to be validated with more arms/data."* This is honest about the small-sample limit and avoids over-claiming precision.

---

## 4B. Zone Classification (decided)

The 0–100 reliability-on-demand index is mapped to **5 replacement zones**, keeping Alarfaj's zone/action/risk framework for continuity and operational usefulness. This is the step that turns the score into a decision (keep / monitor / plan replacement / replace now).

**Assignment method: score-band with FIXED thresholds (configurable).** An arm's zone depends only on its own score against fixed cutoffs — not on its rank or on the other arms in the batch.

- **Why fixed, not statistical (mean/SD):** statistical thresholds are *batch-dependent* (the same arm can change zones depending on which other arms it's evaluated with) and *unstable on small samples* (mean/SD from 6 arms are shaky; one extreme arm shifts every boundary). They also compound badly here — the TOPSIS index is *already* relative (closeness to best/worst in the set), so statistical thresholds would make the zones doubly relative. Fixed thresholds give an absolute, stable, defensible replacement signal ("below X = replace") that doesn't depend on the comparison batch.
- **Why score-band, not rank-based:** a replacement decision shouldn't depend on batch composition — an arm can be genuinely unreliable even if it isn't the worst in the current set.

**Zone framework (Alarfaj-style):**

| Zone | Risk | Recommended action |
|---|---|---|
| Zone 1 | Very low | No action required |
| Zone 2 | Low | No action required |
| Zone 3 | Mid | Expand/improve inspection; RCA on low-scoring criteria; develop & monitor action plan |
| Zone 4 | High | Plan replacement at upcoming shutdown; use only under high demand with no alternative |
| Zone 5 | Very high | Take out of service immediately; replace |

**Thresholds — provisional, calibrated to the TOPSIS score distribution:**
- The specific cutoffs are set as a **config constant** in the code (not hard-coded through the logic), so they can be tuned without touching the method.
- **Do not assume naive 20-point bins.** Because the index is a TOPSIS *closeness coefficient*, scores tend to cluster toward the middle and avoid the extremes (0/100), so cutoffs should be calibrated to where real scores actually fall. Provisional starting bands can be even (e.g. ≥80 Z1, 60–80 Z2, 40–60 Z3, 20–40 Z4, <20 Z5) but are placeholders until real-data calibration.
- **Honest caveat (state in thesis):** with only 6 arms and a relative index, zone thresholds cannot be robustly calibrated. Defensible position: *"5-zone framework with action recommendations; thresholds set as configurable parameters and calibrated to the score distribution; final thresholds to be validated with more arms/data."* This avoids over-claiming precision the method can't support at this scale.

**Link to "reliability on demand":** a low-zone arm is precisely one that cannot be relied upon when a vessel calls on it — the zone is the operational expression of the reliability-on-demand index.

---



Run **plain AHP in parallel** as a benchmark (replicating the Alarfaj approach with the same criteria). The difference between AHP weights/rankings and DANP weights/rankings *is itself a thesis result* — it quantifies how much criteria interdependency changes the conclusion. This directly demonstrates the value added over the precedent work.

---

## 6. Fallback

If the full fuzzy DANP proves too heavy to run with the available expert pool, there is a pre-agreed graceful downgrade path. This is maintained as a separate document — see **Fallback Plan** (companion doc) for the triggers and the ordered downgrade tiers.

---

## Open items
- **Expert elicitation plan** — who, how many, session design (shared with the weighting-mechanics step).
- **Exact link count (N)** after screening — determined once the screening session is run.
- **ANP pairwise fuzzy scale** — if ANP comparisons are elicited separately from the DEMATEL influence judgments, they may use a different fuzzy scale (fuzzy Saaty 1–9); confirm at the ANP elicitation-detail stage.
