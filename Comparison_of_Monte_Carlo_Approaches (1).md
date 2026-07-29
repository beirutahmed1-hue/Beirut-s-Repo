# Comparison of Monte Carlo Approaches for the Loading Arm Reliability-on-Demand Model

*Companion document to the main methodology report. Scope: how Monte Carlo simulation is used in the thesis, given the constraint of very few historical failure records (~5 per loading arm, due to access restrictions).*

---

## The two approaches at a glance

The thesis has two **separate** sources of uncertainty, and each Monte Carlo (MC) approach addresses one of them. They are not competing alternatives — they stack.

| | **Approach 1 — Weight-perturbation sensitivity** | **Approach 2 — Scenario generation from historical data** |
|---|---|---|
| **What it perturbs** | The criteria weights (EI 31%, AF 20%, FR 14%, etc.) | The failure-rate / aging criterion inputs, derived from the ~5 historical records |
| **Source of uncertainty addressed** | Subjective expert judgment in the weights | Sparse, limited field failure data |
| **Question it answers** | "Is my ranking stable if the weights wobble within a plausible range?" | "How uncertain is each loading arm's score given so few failure records?" |
| **Touches historical records?** | No | Yes — this is the approach that uses them |
| **Output** | e.g. "LA-410 ranked worst in 98% of runs" | A *distribution* of final scores per arm, e.g. "LA-409 = 27.9 ± 4.2" |
| **Always worth including?** | Yes — weights are always uncertain | Only if failure-rate uncertainty materially affects the conclusions (see sensitivity check below) |

---

## Approach 1 — Weight-perturbation sensitivity (recommended, unconditional)

**What it does:** Runs the model thousands of times, each time randomly nudging the criteria weights within a plausible range around the expert-derived values, and records whether the ranking and zone assignments stay the same.

**Why it earns its place:** The weights come from expert judgment (via AHP or DANP), so they are inherently uncertain — an expert who said EI = 31% could reasonably have said 28% or 34%. Approach 1 converts a single fixed-weight result into a confidence statement, directly answering the examiner question: *"How sensitive are your results to the weights you chose?"*

**Key point:** It only touches the weights — not the failure records, not the criterion scores. It is therefore valuable regardless of how much historical data exists.

**Suggested implementation:** ≥1,000 runs, Latin Hypercube sampling of weights within plausible bounds; report per-unit ranking-stability probabilities and per-zone assignment stability.

---

## Approach 2 — Scenario generation from historical records (conditional, small-sample care required)

**What it does:** Takes the ~5 historical failure records and generates many plausible failure scenarios from them, to characterize how uncertain the failure-rate criterion input is.

**Critical constraint — only ~5 records:** A standard frequentist Weibull fit (shape β + scale α) to ~5 points produces very wide parameter confidence intervals; scenarios generated from such a fit inherit that uncertainty and can create a false sense of rigor. A knowledgeable committee member is likely to challenge a Weibull fit on 5 records. Avoid presenting a standalone Weibull fit to 5 points as if the distribution were well-established — that is the framing most likely to draw fire in a viva.

**Defensible ways to generate scenarios from sparse data:**

- **Option A — Bayesian updating (most defensible for small n):** Start from a *prior* failure distribution taken from generic industry reliability data (e.g. OREDA/SINTEF-type for loading arms or analogous marine transfer equipment; literature reports β ≈ 1.556, indicating wear-out behavior). Use the ~5 site records to *update* that prior into a posterior. MC then samples scenarios from the posterior. The generic data stabilizes the estimate; the site records personalize it. More conceptual work, but far more defensible than a raw fit.
- **Option B — Bootstrap / resampling (simplest, honest about limits):** Resample the ~5 records with replacement thousands of times to build empirical distributions of the statistic of interest (e.g. failures per period). Makes no parametric shape assumption; honestly quantifies estimate uncertainty given the small sample. It does not create information that isn't there — it characterizes what little there is.

**Framing for the thesis:** Treat the ~5 records as *informing / updating* the failure-rate criterion, not as *defining* a fitted failure distribution. State the access-restriction data limitation explicitly, turning a weakness into a documented, defensible scoping decision.

---

## How to actually *use* the Approach 2 scenarios

Generating scenarios is only worthwhile if they feed back into a decision. Uses, from most to least valuable:

1. **Propagate into the composite score → get a score distribution per arm.** Each scenario yields a plausible failure count/rate → mapped to its FR sub-score (0 / 3.33 / 6.67 / 10) → run through the weighted model → produces a *distribution* of final scores instead of one number. Result: e.g. "LA-409 scores 27.9 ± 4.2; 90% chance it falls in Zone 4." Converts a point estimate into a confidence band on the replacement decision.

2. **Test whether FR uncertainty ever changes a zone / replacement decision.** Across all scenarios, does any arm cross a zone boundary? A borderline arm (e.g. Zone 4 in 95% of scenarios, Zone 3 in 5%) is flagged for a second look. If *no* arm ever changes zone, that is itself a valuable finding — it shows the conclusions are robust to the sparse-data limitation and defends the small-sample scope.

3. **Forward-looking failure projection (optional, higher ambition).** If the records contain time information, scenarios can estimate probability of failure over the next operating period — moving toward the true reliability-on-demand (PFD) framing. Requires time-to-failure data, not just failure counts.

---

## Do both give the "best" result?

Using both gives the most complete coverage, because they address the two distinct uncertainty sources (subjective weights + sparse data). But "both = best" only holds **if the failure data matters enough to the conclusions to be worth modeling.** More MC layers help only when each answers a question you actually need answered.

**Recommended sequence — test before you build the heavy layer:**

1. Build **Approach 1** first (always earns its place).
2. Run a **quick FR-sensitivity check**: because EI dominates the weights (31%) and FR is only 14%, first test whether failure-rate uncertainty even moves the final scores.
   - If FR uncertainty **barely moves** the scores → report that finding, lean primarily on Approach 1, and save the effort of the full small-sample modeling.
   - If FR uncertainty **pushes borderline arms across zones** → Approach 2 fully earns its place; build it (via Option A or B).

**The combined picture, when both are used:**
- Approach 2 → each arm gets a *distribution* of final scores (from failure-data uncertainty).
- Approach 1 → tells you whether the *ranking* of those arms holds up (from weight uncertainty).
- Together → e.g. "LA-410 is worst in 98% of weight scenarios **and** its score distribution never leaves Zone 5 across failure scenarios" — a strong, uncertainty-aware conclusion, and a clean differentiator from Alarfaj's single-point-estimate model.

---

## Decision summary

- **Approach 1:** include unconditionally. **Finalized parameters (decided):**
  - Perturb the ANP sub-criterion weights by a **±15% relative band** (configurable — also runnable at ±10% and ±20% to show conclusions aren't an artifact of one band); renormalize each perturbed weight vector to sum to 1.
  - **Latin Hypercube Sampling** if readily available (e.g. scipy), else simple random — not load-bearing, don't let it block the build.
  - **10,000 runs** (trivial compute at this problem size; set as a config constant).
  - **Report all four:** ranking stability (% of runs each arm held each rank), zone stability (% of runs in base zone + any boundary crossings), and per-arm score distribution (mean + 5th–95th percentile CI on the 0–100 index).
- **Approach 2:** **deferred** — build later, when real historical failure records exist. Rationale: the ~5 records aren't available yet, and whether Approach 2 is even worth building depends on the FR-sensitivity check (does failure-rate uncertainty, at 14% weight, actually move results?) which can only be run with real data. Leave a **clearly-marked stub/hook** in the code so it slots in without restructuring. If/when built, use **Bayesian updating** or **bootstrap**, never a raw Weibull fit to ~5 points.
- **Always:** document the access-restriction data limitation explicitly as a scoping decision.
