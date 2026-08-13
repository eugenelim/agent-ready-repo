# Adaptive planning for multi-spec initiatives — applied survey

> Discipline: applied (practitioner-pattern survey)

**Question.** How should a multi-spec engineering initiative avoid front-loading a
fixed decomposition that drifts once early increments ship, and how can governance
artifacts (RFCs/ADRs/specs) stay revisable without losing decision traceability?

**Occasion.** `ini-008` (RFC-0083) cut seven delivery groups in one pass on
2026-08-09. Groups 2 and 3 shipped (2026-08-10, 2026-08-12). Group 3 made canonical
routing the enforced contract and thereby made its own initiative's remaining queue
non-dispatchable. Nothing detected this; it surfaced when a human asked.

---

## Findings

**F1. The mature pattern is a fixed anchor plus rolling detail — not one or the
other.** `[moderate]` The finance rolling-forecast analog is explicit that best
practice *combines* a rolling forecast with a fixed annual budget rather than
replacing it, and the same shape recurs in Kubernetes KEPs (durable
Motivation/Proposal + rewritable Graduation Criteria). One retriever flagged that
pure rolling-wave without an outer anchor may itself be an anti-pattern. Downgraded
from high: convergent across independent domains, but no measured comparison.
[synthesis across Basecamp Shape Up, KEP template, rolling-forecast sources]

**F2. Governance systems that work separate the durable decision from the
perishable plan, by one of four mechanisms.** `[high]` Section-based in one living
doc (Kubernetes KEP — *"You do not need a new KEP to move from beta to GA"*, with
major post-`implementable` changes needing approver sign-off); two-artifact (Rust
RFC frozen + tracking issue carries the plan); status-based by category (Python PEP
— Standards-track freezes at Final, Process/Informational stay Active, *Provisional*
is accepted-in-principle-but-plan-mutable); append-only chain (IETF Updates/Obsoletes;
ADR `superseded by`). Four independent, primary-sourced process documents.

**F3. "Freezing a delivery plan inside an immutable decision record" is a real
anti-pattern with no agreed name.** `[moderate]` Described independently in the Rust
and ADR communities but with no shared vocabulary. Rust's insider critique documents
the failure concretely: stabilisation decisions happen outside the RFC system, so
neither the frozen doc nor the tracker reflects reality, with 54+ RFCs open with no
resolution path. Downgraded: two communities, no cross-system term, one insider
account.

**F4. The dominant failure of decision records is neglect, not bad edits.**
`[moderate]` ADR practitioner literature repeatedly reports corpora that are never
revisited, so superseding never happens even when it should — "quietly drifted from
their own decisions," or "200 ADRs nobody reads." Directly matches this occasion.
Practitioner-consensus, no measurement.

**F5. "No plan survives first contact" is folklore, and does not say what it is
used to say.** `[high]` Moltke's 1871 claim was narrower — *"no plan of operations
extends with any certainty beyond the first encounter with the main body"* — and his
actual doctrine was preparing **branching option sets**, not abandoning planning. The
compression dropped precisely the nuance that made planning compatible with
adaptation. Well-sourced quote-history research.

**F6. Both "BDUF is dangerous" and "adaptive is dangerous" are under-evidenced
relative to how confidently each is argued.** `[high]` No controlled study, survey,
or numbered post-mortem was found showing front-loaded decomposition causes rework;
equally, no audited cost-quantified case study of under-planning was found. The
asymmetry is a survivorship signature: BDUF failures draw government audits (FBI VCF
≈$170M, NPfIT £12.7–20bn, healthcare.gov), under-planning failures get silently
refactored.

**F7. The strongest empirical plank under "plan more up front" is contested.**
`[moderate]` Menzies, Nichols, Shull & Layman (2016, peer-reviewed, N=171) found no
reliable delayed-issue effect, undercutting the Boehm cost-of-change curve. Note the
unit-of-analysis gap: that study measures *defects*, not architecture/requirements
rework, so it weakens rather than refutes the argument.

**F8. Standish/CHAOS figures should not be cited.** `[high]` Multiple peer-reviewed
critiques (Eveleens & Verhoef; Glass; Jørgensen & Moløkken-Østvold) find methodology
undisclosed, definitions inconsistent across editions, replications inconsistent —
*"a business, not science."*

**F9. Requirements churn is real, measurable, and front-loads.** `[moderate]`
Peer-reviewed requirements-volatility studies find statistically significant impact
on schedule/cost overrun, with volatility *decreasing* over the lifecycle. Modest
sample sizes, single-company case studies. Capers Jones's <1%–>10%/month figures are
large-N but proprietary and unauditable.

**F10. Fitness functions are the only concrete, continuously-run drift detector
found.** `[moderate]` Automated repeatable checks in the deployment pipeline that
flag objective movement away from desired characteristics; ThoughtWorks Radar lists a
*"dependency drift fitness function."* Practitioner-consensus, not independently
measured for effectiveness. **This is the operational answer to "we had no trigger."**

**F11. Deferring commitment has no operational trigger, and that is its main
failure mode.** `[moderate]` LRM is critiqued by independent practitioners for
providing no way to recognise the moment except in hindsight; Wirfs-Brock reframes it
as the *most* responsible moment, naming coordination lead time, early unconscious
choices becoming de facto architecture, and false confidence in revisability. The
originating claims trace to a small cross-citing author cluster; the *critique* is
independently corroborated.

**F12. Bezos type-1/type-2 door classification is the most operational
translation.** `[moderate]` Reversible decisions delegated and made fast; irreversible
ones deliberated. Widely applied by unrelated practitioners, though originating in a
single shareholder letter.

**F13. There is a live, unresolved 2026 debate about whether AI changes the
economics of up-front specs.** `[moderate]` Spec-driven development tooling (Kiro,
spec-kit, Tessl) revived write-specs-first. Böckeler reports a small bug fix
producing 4 stories / 16 ACs — *"a sledgehammer to crack a nut"*; Johnson argues SDD
is BDUF rebranded but that AI changes the cost basis; Yeret calls up-front
multi-feature specs *"requirements theater"* and recommends backlogs carry only
**intent and context**, with detail generated when work starts. Directly relevant —
this repo is a spec-driven repo — and genuinely unsettled.

---

## What this implies here

1. Keep the decision frozen, let the forecast roll (F1, F2). RFC-0083's § Proposal
   is durable; Groups 1–7 are a forecast. Erratum, not new RFC (repo precedent:
   RFC-0011, RFC-0013 § Errata).
2. Re-cut each group immediately before building it, one horizon ahead (F1, F13).
3. Automate the trigger; do not rely on vigilance (F4, F10, F11). A staleness check
   that flags a queued spec whose `needs` shipped after its last revision.
4. Do not claim evidence we do not have (F6, F7, F8). Argue from the local
   instance — #928 invalidating four specs — not from borrowed authority.

## Known unknowns

- **Known-unknown:** does front-loaded decomposition measurably increase rework?
  Would be closed by a controlled study or an audited multi-project dataset with
  churn attributed to decomposition age. None found.
- **Known-unknown:** does AI-assisted spec authoring change the up-front/JIT
  trade-off? Would be closed by outcome data from SDD adopters; the 2026 debate is
  argued from single-team anecdote.
- **Known-unknown:** do fitness functions reduce drift in practice? Would be closed
  by before/after measurement at an adopter. Only practitioner assertion found.
- **Unknowable:** what Groups 4–7 *would* have cost had they been built against
  their original anchors. The counterfactual cannot be run.
- **Unknowable (as posed):** the "right" amount of up-front planning. Contested
  across contexts in a way no single study settles; belongs in a tension, not a
  finding.

## Sources

Ward/Sobek/Liker, *Toyota's Principles of Set-Based Concurrent Engineering*, MIT
Sloan Management Review (primary) · Kubernetes KEP template (primary) · PEP 1, PEP 8
(primary) · Rust RFC `0002-rfc-process.md` (primary) · RFC 2026, IETF process
(primary) · Nygard, *Documenting Architecture Decisions* (primary) · Menzies,
Nichols, Shull & Layman (2016), *Are Delayed Issues Harder to Resolve?* (primary,
peer-reviewed) · Eveleens & Verhoef, *The Rise and Fall of the Chaos Report Figures*
(peer-reviewed critique) · HICSS 2010, *Understanding Requirements Volatility*;
Verhoef group, *Quantifying Requirements Volatility Effects* (peer-reviewed) ·
Quote Investigator, *No Plan Survives First Contact* (secondary, quote history) ·
Cohn, *Agile Estimating and Planning* (secondary) · Basecamp, *Shape Up* (primary) ·
Ford/ThoughtWorks, *Fitness function-driven development*; Radar, *Dependency drift
fitness function* (secondary) · Wirfs-Brock, *Agile Architecture Myths #2*; Morris,
*LRM should address uncertainty* (secondary critique) · Matts & Maassen, *Real
Options Underlie Agile Practices* (primary, practitioner) · Henney, *The Uncertainty
Principle* (primary) · Fowler, *Is Design Dead?* (secondary) · Böckeler,
*Understanding Spec-Driven Development* (secondary, 2026); Yeret; Johnson · ncameron,
*We need to talk about RFCs* (insider critique) · Marchewka, *FBI Virtual Case File*;
Anderson, *NPfIT Case History* (academic case studies) · Foote & Yoder, *Big Ball of
Mud*; Lehman's Laws validation studies (peer-reviewed).
