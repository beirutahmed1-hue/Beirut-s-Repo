# Criteria & Sub-Criteria Specification — Loading Arm Reliability-on-Demand Model

*Companion document to the main methodology report. This is the authoritative reference for the criteria hierarchy, sub-criteria definitions, and scoring scales used to build the model/code.*

**Scoring convention (kept from Alarfaj):** every sub-criterion is scored on a four-segment scale — **0 / 3.33 / 6.67 / 10** — worst to best. A sub-criterion score of 10 = optimum condition; 0 = worst/failed condition. Final composite is the weighted sum (weights from DANP) mapped to a 0–100 index and then to replacement zones.

**Legend:**
- **[Alarfaj]** = scale taken verbatim from Alarfaj (2023); established, not assumed.
- **[ASSUMED]** = reasonable placeholder scale built for this thesis; **must be validated with the expert panel / standards before final use.** Used now so the code can be built and tested.
- **Basis:** *Quantitative* = scored from a record/number; *Qualitative* = scored from inspection/expert judgment.

---

## Hierarchy overview

5 main criteria (clusters), 15 sub-criteria. Clusters 1–4 = Condition branch; cluster 5 = Obsolescence branch.

| # | Cluster | Sub-criteria | Source |
|---|---|---|---|
| 1 | Corrosion / External Integrity | External integrity (corrosion/coating/metal loss); Internal integrity | EI = Alarfaj; internal = added |
| 2 | Mechanical Integrity | Swivel joint condition; Seal integrity; Hydraulic/control system health; Emergency release (QC-DC) function; Aging | Aging = Alarfaj; rest = added |
| 3 | Operational Performance | Operation performance compliance (pressure/flow); Utilization frequency; Failure rate | OPC, FR = Alarfaj; utilization frequency = added |
| 4 | Maintenance | PM compliance; Maintenance execution quality | MC = Alarfaj; quality = added |
| 5 | Obsolescence & Supportability | Spare parts availability; Vendor support; Reverse engineering | all Alarfaj |

---

## Cluster 1 — Corrosion / External Integrity

### 1.1 External Integrity (EI) — [Alarfaj]
- **Definition:** physical external condition of the asset — external coating condition and external corrosion, expressed as external metal loss (ML). Poorly maintained → external ML → eventual full penetration of the pipe wall.
- **Basis:** Quantitative (metal loss %).
- **Scale [Alarfaj]:**
  - 0 — ML ≥ 60%
  - 3.33 — 60% > ML ≥ 40%
  - 6.67 — 40% > ML ≥ 20%
  - 10 — ML < 20%

### 1.2 Internal Integrity — [ASSUMED]
- **Definition:** internal condition of the flow path (bore, internal swivel surfaces) with respect to internal corrosion/erosion and internal metal loss — a degradation path distinct from external corrosion.
- **Basis:** Quantitative (internal metal loss %, via UT/NDT) where available; otherwise Qualitative.
- **Scale [ASSUMED] (mirrors EI thresholds for consistency):**
  - 0 — internal ML ≥ 60%
  - 3.33 — 60% > ML ≥ 40%
  - 6.67 — 40% > ML ≥ 20%
  - 10 — ML < 20%

---

## Cluster 2 — Mechanical Integrity

### 2.1 Swivel Joint Condition — [ASSUMED]
- **Definition:** mechanical condition of the swivel joints (the classic single point of failure) — rotational play/backlash, wear, and freedom of movement. Excludes seal leakage (see 2.2).
- **Basis:** Qualitative (inspection/expert assessment).
- **Scale [ASSUMED]:**
  - 0 — seized, or severe wear/excessive play; movement unreliable
  - 3.33 — significant play/roughness; degraded but operable
  - 6.67 — minor wear; functional with full range of motion
  - 10 — as-new; smooth, free rotation, no detectable play

### 2.2 Seal Integrity — [ASSUMED]
- **Definition:** condition of swivel-joint and coupler mechanical seals with respect to leakage, wear, and time since last replacement. (Seals are the routine PM wear item.)
- **Basis:** Qualitative (leakage observation/inspection).
- **Scale [ASSUMED]:**
  - 0 — active leakage / seal failure
  - 3.33 — weeping/seepage or seals well past service interval
  - 6.67 — no leakage; seals mid-life
  - 10 — no leakage; seals recently replaced / as-new

### 2.3 Hydraulic / Control System Health — [ASSUMED]
- **Definition:** condition and performance of the hydraulic and control system — cylinders, valves, actuators, tubing, pressurization — driving arm movement.
- **Basis:** Qualitative (functional test/inspection).
- **Scale [ASSUMED]:**
  - 0 — major malfunction; system unreliable or inoperable
  - 3.33 — recurring faults / notable leaks / sluggish response
  - 6.67 — minor issues; fully functional
  - 10 — fully functional; no leaks; correct response across all modes

### 2.4 Emergency Release (QC-DC) Function — [ASSUMED]
- **Definition:** readiness and reliability of the safety-critical emergency release / quick connect-disconnect coupler function on demand (the most directly "reliability-on-demand" element).
- **Basis:** Qualitative (function test / test records).
- **Scale [ASSUMED]:**
  - 0 — fails to actuate on test / non-functional
  - 3.33 — actuates unreliably or overdue for function test
  - 6.67 — functional; tested within interval
  - 10 — fully functional; recently tested; no anomalies
- **Note:** high-criticality safety function — flag for possible non-compensatory treatment (a very low score here arguably should not be offset by strong scores elsewhere; revisit when finalizing aggregation).

### 2.5 Aging (AF) — [Alarfaj]
- **Definition:** chronological service life / natural degradation over time from environmental exposure (heat, humidity, sea splash). Placed under Mechanical; cross-effects on Corrosion and Obsolescence captured via DEMATEL interdependency links (not duplicated as separate criteria).
- **Basis:** Quantitative (age in years).
- **Scale [Alarfaj]:**
  - 0 — Age ≥ 25 years
  - 3.33 — 25 > Age ≥ 15
  - 6.67 — 15 > Age ≥ 5
  - 10 — Age < 5 years

---

## Cluster 3 — Operational Performance

### 3.1 Operation Performance Compliance (OPC) — [Alarfaj]
- **Definition:** operating within design envelope — internal pressure compliance (avoiding overpressure/rupture) and flow compliance (avoiding erosion from over-velocity or internal corrosion from under-velocity). Measured over last 5 years.
- **Basis:** Quantitative (% compliance).
- **Scale [Alarfaj]:**
  - 0 — OPC < 70%
  - 3.33 — 70% ≤ OPC < 80%
  - 6.67 — 80% ≤ OPC < 90%
  - 10 — 90% ≤ OPC ≤ 100%

### 3.2 Utilization Frequency — [ASSUMED]
- **Definition:** how heavily the arm is worked — connect/disconnect (loading) operations per year. Higher utilization drives wear and affects reliability-on-demand. (Directional note: define whether higher utilization scores lower because of wear, or is normalized against design cycle rating — see note.)
- **Basis:** Quantitative (operations/cycles per year).
- **Scale [ASSUMED] (higher utilization = more wear = lower score; thresholds are placeholders pending site cycle data):**
  - 0 — very high utilization (well above typical)
  - 3.33 — high utilization
  - 6.67 — moderate utilization
  - 10 — low / standby-level utilization
- **Note:** thresholds must be set from actual site cycle counts and/or OEM design cycle rating. Also confirm scoring direction with the panel — a heavily used arm is not necessarily "worse" if within design rating; may instead be scored as utilization *relative to rated capacity*.

### 3.3 Failure Rate (FR) — [Alarfaj]
- **Definition:** frequency of failures over time; indicates reliability/probability of failure. For loading arms, counted as number of failures since the last major Turnaround & Inspection (T&I), which occurs every 5 years.
- **Basis:** Quantitative (failure count since last T&I).
- **Scale [Alarfaj]:**
  - 0 — # failures ≥ 5
  - 3.33 — 5 > # failures ≥ 3
  - 6.67 — 3 > # failures ≥ 1
  - 10 — # failures = 0
- **Note:** expected to appear as a net *effect/receiver* in DEMATEL (analysis output, not a design choice). Candidate for the Monte Carlo Approach 2 sparse-data treatment (see MC companion doc).

---

## Cluster 4 — Maintenance

### 4.1 PM Compliance (MC) — [Alarfaj]
- **Definition:** compliance with required time-based Preventive Maintenance. Loading arm requires annual PM (seal changes, lubrication, pantograph cable greasing). Measured as PM deferral since last T&I.
- **Basis:** Quantitative (months of PM deferral).
- **Scale [Alarfaj]:**
  - 0 — Deferral ≥ 9 months
  - 3.33 — 9 > Deferral ≥ 6
  - 6.67 — 6 > Deferral ≥ 3
  - 10 — Deferral < 3 months

### 4.2 Maintenance Execution Quality — [ASSUMED]
- **Definition:** quality/correctness of maintenance actually performed — distinct from mere compliance (PM can be done on time but poorly). Captures workmanship, correct procedures, and rework/repeat-failure evidence.
- **Basis:** Qualitative (maintenance records, rework/repeat-failure history, expert judgment).
- **Scale [ASSUMED]:**
  - 0 — frequent rework / evidence of poor workmanship or wrong procedures
  - 3.33 — occasional rework / inconsistent quality
  - 6.67 — generally sound; rare issues
  - 10 — consistently correct; no rework; procedures fully followed

---

## Cluster 5 — Obsolescence & Supportability

### 5.1 Spare Parts Availability (SPA) — [Alarfaj]
- **Definition:** availability of consumable and main spare parts from the manufacturer or authorized third party. Readily available spares reduce downtime and protect business continuity.
- **Basis:** Qualitative (supply status).
- **Scale [Alarfaj]:**
  - 0 — no spare parts available
  - 3.33 — only consumable parts available
  - 6.67 — consumable & some main parts available
  - 10 — all spare parts available with OEM

### 5.2 Vendor Support (VS) — [Alarfaj]
- **Definition:** contractual support from the manufacturer/authorized third party for maintenance and inspection — technical support by trained personnel per the intended function/design.
- **Basis:** Quantitative-ish (contract term).
- **Scale [Alarfaj]:**
  - 0 — no support
  - 3.33 — contractual support ≤ 1 year
  - 6.67 — contractual support ≤ 3 years
  - 10 — contractual support > 3 years

### 5.3 Reverse Engineering (RE) — [Alarfaj]
- **Definition:** feasibility of disassembling/analyzing the equipment to replicate a part/component and reinstall it — a mitigation for obsolescence (subject to intellectual-property constraints).
- **Basis:** Qualitative (RE capability level).
- **Scale [Alarfaj]:**
  - 0 — no reverse engineering possible
  - 3.33 — partial RE (consumable parts)
  - 6.67 — partial RE (some critical parts)
  - 10 — complete reverse engineering

---

## Notes for coding

- **Inputs:** each arm supplies, per sub-criterion, either a raw value (quantitative → mapped to 0/3.33/6.67/10 via the thresholds above) or a direct band score (qualitative → expert selects the band).
- **Direction:** all scales are oriented so **higher = better condition** (10 best, 0 worst). Keep this uniform so TOPSIS ideal-best/worst and any weighted-sum aggregation are consistent.
- **Weights:** sub-criterion and cluster weights come from DANP (not equal). Until DANP weights exist, the code can use equal weights or the Alarfaj weights (for the 8 shared criteria) as a placeholder to test the pipeline.
- **[ASSUMED] scales are placeholders** — the 7 added sub-criteria (internal integrity, swivel, seals, hydraulics, emergency release, utilization frequency, maintenance quality) need expert/standards validation before final results. They are fine for building and testing the code now.
- **Emergency Release (2.4)** flagged for possible non-compensatory handling — revisit at the aggregation-design stage.
- **Utilization Frequency (3.2)** scoring direction and thresholds are the least settled — confirm against site cycle data and OEM rating.
