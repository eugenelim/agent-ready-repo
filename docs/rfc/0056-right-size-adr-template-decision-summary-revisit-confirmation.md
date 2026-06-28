# RFC-0056: Right-size the ADR template — first-screen Decision summary, Revisit-if trigger, structured Confirmation

- **Status:** Draft <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-28
- **Date closed:** <!-- filled in when status reaches a terminal state -->
- **Decision weight:** heavy <!-- amends a frozen RFC (0038) and extends the format a frozen ADR (0027) froze; governance-template surface; explicit Approver sign-off required -->
- **Related:** [RFC-0038](0038-align-adr-template-with-madr.md) (the template decision this amends), [ADR-0027](../adr/0027-adr-format-is-madr-aligned-but-lean.md) (froze the format as MADR-aligned-but-lean; this extends it), [RFC-0014](0014-answer-first-rfc-format-and-drafting-flow.md) (the answer-first house style), [RFC-0054](0054-new-rfc-two-humans.md) (introduced the `## Reviewer brief` first-screen grid — the duplicate-by-design precedent for R2), `packs/governance-extras/.apm/skills/new-adr/` (the skill + template + evals this changes), PR #441 (track 1 — guidance + format-independent evals)

## Reviewer brief

- **Decision:** Three optional ADR-template fields — a first-screen `## Decision summary`, a structured `Revisit if:` trigger, and a `Mode / Signal / Owner` sub-structure for Confirmation — plus the vehicle that records them against the frozen RFC-0038 / ADR-0027.
- **Recommended outcome:** accept (amend RFC-0038, extend ADR-0027).
- **Change if accepted:** (1) `assets/adr.md` gains the three fields; (2) `new-adr` `SKILL.md` + how-to guide describe them; (3) the format-dependent evals track 1 foreclosed get authored.
- **Affected surface:** `governance-extras` pack only — `new-adr` skill, template, evals, and the repo-owned how-to guide. No code; no CONVENTIONS § 2 change.
- **Stakes:** costly-to-reverse (the template is a published interface adopters scaffold from; immutable ADRs accumulate against it) — but each field is optional-deletable, which keeps a wrong call cheap to walk back.
- **Review focus:** (D1) is the Decision summary optional-deletable or mandatory? (D3) the delete-vs-explicit-`none` default for Confirmation; (D4) does the follow-on ADR *extend* ADR-0027 or *supersede* it? (D2 and D5 are confirmations, not contested calls.)
- **Not in scope:** MADR-full (per-option pros/cons, options-first ordering) — still excluded, per ADR-0027; rewriting existing ADRs; a mechanical ADR-status/section lint.

## The ask

- **Recommendation (BLUF):** Extend the `new-adr` template with three fields the original critique deferred from track 1 because they change the format ADR-0027 froze — a first-screen `## Decision summary` block (R2), a structured `Revisit if:` trigger (R6), and a `Mode / Signal / Owner` sub-structure with an explicit-absent value for the existing Confirmation section (R7). Adopt all three as **optional-deletable** additions, not mandatory surface, so they serve retrieval and lifecycle without re-importing MADR-full ceremony.
- **Why now (SCQA):**
  - *Situation* — Track 1 of the `new-adr` critique (PR #441) shipped the guidance and the format-*independent* evals, and explicitly deferred the three format-changing recommendations to "a track-2 RFC, since ADR-0027 froze the MADR-aligned-but-lean format."
  - *Complication* — Those three are the critique's highest-value retrieval/lifecycle asks (R6 is called "the biggest missing ADR-specific field"), and three of the R8 usability checks the critique proposed (`Decision summary exists`, `Revisit trigger present`, `Confirmation concrete or explicitly absent`) were *foreclosed* in track 1 — its spec states outright "No assertion references a track-2 field" (`docs/specs/new-adr-decision-capture/spec.md` AC5) — because they cannot be authored until the template carries the fields. Meanwhile the repo's own heavy ADRs (ADR-0031, ADR-0037) demonstrate the density problem: a multi-line title plus a paragraph of metadata push the actual decision off the first screen.
  - *Question* — Can we add these three without crossing the lean-vs-full line ADR-0027 deliberately drew?
- **Decisions requested:**

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  | --- | --- | --- | --- | --- | --- |
  | D1 | Add a first-screen `## Decision summary` block before Context — optional or mandatory? | Add it, **optional-deletable**, with length-based guidance to include it | Mirrors the RFC `Reviewer brief` and the Y-statement; mandatory-always is ceremony on short ADRs and fights the arXiv conciseness finding | this review | Rule on optional vs mandatory |
  | D2 | Add a structured `Revisit if:` trigger, and where does it live? | Add it; canonical home in **Consequences**, mirrored in the summary when present | Survives deletion of the optional summary; formalizes today's ad-hoc "Neutral / to revisit" bullet | this review | Confirm field + home |
  | D3 | Add `Mode / Signal / Owner` sub-structure to Confirmation, with `Mode: none` (explicitly absent) as valid? | Add it as the shape *when the section is present*; keep the section deletable; prefer explicit `none` over silent deletion | Resolves the delete-vs-explicit-absent tension; makes a non-checkable residual visible | this review | Confirm, and rule on the delete-vs-explicit-none default |
  | D4 | What vehicle records this against the frozen RFC-0038 / ADR-0027? | `## Errata` on RFC-0038; a follow-on ADR that **extends** ADR-0027 (Related, not Supersedes) | ADR-0027's lean-vs-full *thesis stands*; we add lean-compatible fields, we don't reverse it | this review | Rule on extend vs supersede |
  | D5 | Is the scope skill-pack-only — leaving `CONVENTIONS.md` § 2 **untouched** — with the now-authorable format-dependent evals and the how-to guide updated alongside? | Yes, § 2 untouched | § 2 governs the *status vocabulary*, which is unchanged; the change is body-section structure, which lives in the skill/template — so unlike RFC-0038 this needs no convention edit | this review | Rule on the § 2-untouched scope claim; the eval/guide updates ride with it |

  (This RFC amends a frozen RFC and extends the format a frozen ADR froze; per `CONVENTIONS.md` § 3 and the `heavy` weight it requires explicit Approver sign-off — no silent-default adoption.)

## Problem & goals

**Diagnosis.** ADR-0027 froze the ADR format as *MADR-aligned but lean*: it adopted MADR 4.0's value-adds (the `Rejected` status, the decision-roles split, optional `Decision drivers` and `Confirmation`) and deliberately excluded MADR-full (per-option pros/cons, options-first ordering). That choice is sound and is **not** reopened here. But the format it produced has three residual gaps the track-1 critique named and track 1 could not close without touching the template:

- **The decision is not first on the screen.** The template orders Context → Decision (standard Nygard/MADR). For a short ADR that is fine. For the repo's heavy ADRs it is not: ADR-0031's H1 is a ~40-word sentence and its `Consulted`/`Related` block runs to a paragraph, so a reader hunting "what did we actually decide?" must scroll past all of it. The critique: "your actual ADRs are long enough that future readers need the decision first."
- **There is no revisit trigger.** An ADR records *why we got here* but not *when to question it*. Today this is carried only by the ad-hoc `Neutral / to revisit` bullet in Consequences and the implicit "re-run the decision when a driver changes" mechanism. The critique calls a dedicated trigger "the biggest missing ADR-specific field." MADR 4.0 has no such field either — this is a genuine gap, not drift.
- **Confirmation drifts toward aspirational.** The Confirmation section is good but unstructured, so it can read as a hope rather than a checkable claim; and a decision with *no* way to confirm conformance simply omits the section — making the non-checkable residual invisible.

**Goals.**
- Put the decision on the first screen for the ADRs long enough to need it, without bloating short ones.
- Give a decision a place to name its own expiry condition.
- Make Confirmation a checkable claim with an honest "none" value.
- Do all three *within* the lean budget — no per-option pros/cons, no options-first ordering, nothing mandatory that a short ADR would carry as dead weight.

**Non-goals** (could-have-been-goals deliberately dropped):
- *Not* adopting MADR-full — the lean-vs-full line ADR-0027 drew stands; this RFC stays strictly on the lean side of it.
- *Not* making any of the three fields mandatory-always (D1/D3 keep them deletable; D2 is recommended-not-required).
- *Not* rewriting existing ADRs — they are Frozen history; the change is forward-only.
- *Not* adding a mechanical ADR-section lint — conformance stays reviewer-checked, as ADR-0027 already settled. (A lint remains separately RFC-gated.)
- *Not* touching `docs/CONVENTIONS.md` § 2 — it governs the status vocabulary, which is unchanged.

## Proposal

Applied to `packs/governance-extras/.apm/skills/new-adr/` (`assets/adr.md`, `SKILL.md`, `evals/evals.json`) and the repo-owned how-to guide `docs/guides/governance-extras/how-to/new-adr.md`.

### R2 — first-screen `## Decision summary` (D1)

A new optional section placed **immediately after the frontmatter, before Context**:

```markdown
## Decision summary

- **Decision:** We will <the choice, one sentence>.
- **Because:** <the one winning driver>.
- **Applies to:** <scope / boundary of the decision>.
- **Tradeoff accepted:** <the main negative consequence>.
- **Revisit if:** <the trigger — see R6>.
```

This is a **TL;DR by design**: every line restates something the body already carries (Decision ← Decision section, Because ← Decision drivers, Tradeoff accepted ← Consequences, Revisit if ← Consequences). The duplication is the point — it is the first-screen retrieval surface, exactly as the RFC template's `## Reviewer brief` duplicates "The ask" to orient before the reader argues. It strengthens the answer-first house style (RFC-0014) rather than fighting it: today "answer-first" means the Decision *section* leads its own section, but only *after* Context; this puts the decision genuinely first.

**Optionality (the D1 call).** Recommended **optional-deletable**, with skill guidance to include it once the ADR is long enough that the Decision isn't visible on the first screen — and to delete it on a short ADR (ADR-0027 itself would not carry one). Rationale: a five-line summary bolted onto a fifteen-line ADR is pure redundancy and the exact ceremony the lean position rejects; the empirical finding (below) is that conciseness *wins* on comprehension, so the default must not tax the short case. The alternative — mandatory-always, matching the RFC `Reviewer brief` — is left for the Approver to rule on (see Options, and the Open question).

### R6 — structured `Revisit if:` trigger (D2)

A dedicated trigger naming when the decision should be reconsidered: a new constraint, a failed confirmation, changed platform support, a scale threshold. Its **canonical home is Consequences** — it replaces today's ad-hoc `**Neutral / to revisit:**` bullet with a named `**Revisit if:**` line — and it is **mirrored in the Decision summary when that block is present**. Canonical-in-Consequences is deliberate: Consequences is an always-present section, so the trigger survives deletion of the optional summary. Recommended **optional-but-recommended**: present for decisions likely to age, with `Revisit if: stable — no foreseeable trigger` as a valid explicit value for decisions that genuinely won't.

### R7 — right-sized Confirmation (D3)

Keep the existing optional Confirmation section; when present, give it a sub-structure:

```markdown
## Confirmation

- **Mode:** reviewer-checked | lint/CI | architecture fitness test | periodic audit | none
- **Signal:** <what proves conformance>
- **Owner:** <who notices drift>
```

`Mode: none` (with a one-line reason) is a **valid, explicit** value — a non-checkable decision can still be valid, but the residual should be *visible* rather than silently omitted. This resolves a small tension with the current template, which says "delete this section if the decision isn't the kind you can verify." Reconciliation (the D3 call): the section stays deletable for trivial decisions, but where a reader would plausibly expect a confirmation mechanism, the skill prefers the explicit `Mode: none` form over silent deletion.

### Migration & vehicle (D4)

Forward-only; no existing ADR is converted. Recording against the frozen artifacts:
- **RFC-0038** gets an `## Errata` entry naming RFC-0056 as extending its template decision (the body stays frozen).
- A **follow-on ADR extends ADR-0027** — `Related:`, "read the two together," not `Supersedes:`. ADR-0027's load-bearing thesis (MADR-aligned-but-lean, *not* full) is unchanged; this adds lean-compatible fields on the same side of the line. Repo precedent: ADR-0037 extends ADR-0034 the same way.

### Evals & guide (D5)

Author the three format-dependent usability evals track 1 foreclosed because they need the fields: a Decision summary is present (when the ADR's length warrants), a Revisit trigger is present for an aging decision, and Confirmation is concrete or explicitly `Mode: none`. Update the how-to guide Step 5 to describe the three fields. `CONVENTIONS.md` § 2 is untouched.

## Options considered

Axis: *how much template surface to add, and how binding* — exhausts the space from "add nothing" through "add, optional" to "add, mandatory."

| Option | What | Trade-off |
| --- | --- | --- |
| Do nothing | Keep ADR-0027's format unchanged | The three gaps persist: heavy ADRs stay decision-last, no revisit trigger, Confirmation stays unstructured; three deferred evals stay un-wireable. Cost of delay: the critique's highest-value asks never land, and track 1 ships visibly half-finished. |
| **Add, optional-deletable** ★ | R2/R6/R7 as optional fields with length/aging guidance | Closes the gaps and lets short ADRs stay terse; matches the F4/F5 optional-section precedent. Risk: a hurried author skips the summary on an ADR that needed it (mitigated by skill guidance + the eval). |
| Add, mandatory | Same fields, required on every ADR | Guarantees first-screen retrieval everywhere; but taxes every short ADR with five redundant lines — the ceremony the lean position and the arXiv conciseness finding both argue against. This is the boundary case ADR-0027 was drawn to avoid. |

Prior art grounds the recommended option as *lean*, not additive ceremony: R2 is the **Y-statement** (Zimmermann, SATURN 2012) rendered as a first-screen block; R6 operationalizes **Nygard's** own warning against blind acceptance/reversal; R7 structures **MADR 4.0's** existing Confirmation section. None reintroduces per-option pros/cons or options-first ordering — the two things ADR-0027 excluded.

## Risks & what would make this wrong

- **Pre-mortem — the optional summary rots or is skipped where needed.** If authors omit `## Decision summary` on exactly the heavy ADRs that need it, the retrieval benefit evaporates and we've added template surface for nothing. Mitigation: skill guidance keys inclusion to length, and the R8 eval checks for it; the failure is visible, not silent.
- **Pre-mortem — the additions creep toward MADR-full.** If reviewers start expecting the summary to carry per-option reasoning, the lean line erodes. Mitigation: the summary is fixed-shape (five single-value fields, no per-option content); the skill rejects turning it into a debate surface — that is the RFC's job, not the ADR's.
- **Key assumption (falsifiable):** these three fields can be added without crossing into MADR-full ceremony. Falsified if a field cannot be sourced to a lean precedent, or if any introduces per-option pros/cons or options-first ordering — see the spike result below; it holds. Also falsified if adopters report the optional fields are noise — revisit toward dropping them in a follow-on ADR (the same falsification ADR-0027 already set up for its optional sections).
- **Key assumption (falsifiable):** optional-deletable is the right bindingness. Falsified if, in practice, "optional" means "always skipped," at which point the mandatory-but-tiny variant (Decision/Because required, the rest optional) becomes the better call — a cheap follow-on adjustment, not a re-architecture.
- **Drawback:** more template surface to read and more skill prose to maintain, and a known counter-pressure — the arXiv study found Nygard's *concise* template scored highest overall. Accepted because every field is optional and length-keyed, so the concise case keeps the concise template; the surface is spent only where the ADR is already long enough to need it.

## Evidence & prior art

- **Spike / de-risk (riskiest assumption: do these cross into MADR-full?).** Mapped each field to a lean source and checked against ADR-0027's two explicit exclusions. R2 = Y-statement compression (a structured one-paragraph summary, an established lean form). R6 = Nygard's revisit warning made into a field; MADR 4.0 has no equivalent. R7 = structuring MADR's *existing* optional Confirmation section. None of the three introduces per-option pros/cons or options-first ordering. **Result: the additions sit on the lean side of the line — assumption holds.**
- **Repo precedent.**
  - `new-rfc/assets/rfc.md` — the mandatory `## Reviewer brief` first-screen grid ("orients; 'The ask' argues"): the direct precedent that a duplicate-by-design summary earns its place. R2 is its ADR analog.
  - `assets/adr.md` Consequences `**Neutral / to revisit:**` bullet (and ADR-0027's use of it) — R6's current ad-hoc home, which R6 formalizes.
  - ADR-0037 `Related:` "ADR-0034 (the doctrine this *extends* — read the two together)" — the extend-not-supersede precedent for D4.
  - RFC-0038 F4/F5 — Decision drivers and Confirmation shipped as optional-deletable sections: the precedent that added MADR sections are optional, which R2/R6/R7 follow.
  - ADR-0031, ADR-0037 — heavy ADRs whose dense first screens demonstrate the retrieval problem R2 addresses.
- **External prior art.**
  - [MADR 4.0](https://adr.github.io/madr/) — section order is Context → Decision Drivers → Considered Options → Decision Outcome → Consequences → Confirmation; **no** first-screen summary, **no** revisit field, and Confirmation has **no** sub-structure. *Fetched and confirmed.* Establishes that R2/R6 are net-new (not MADR drift) and R7 is an additive refinement.
  - [Y-statements — Zimmermann, SATURN 2012](https://medium.com/olzzio/y-statements-10eb07b5a177) — "In the context of X, facing Y, we decided for Z and against W, to achieve Q, accepting R." R2's five fields map onto it (Decision ← Z, Because ← Q/driver, Applies to ← X, Tradeoff accepted ← R, plus the Revisit-if extension). *Fetched and confirmed.* Grounds R2 as a recognized **lean** compression, not added ceremony.
  - [arXiv 2604.27333 — "One Size Fits All? An Empirical Comparison of ADR Templates"](https://arxiv.org/abs/2604.27333) (2026) — Nygard and MADR were the top-performing templates in expert screening; in the controlled experiment **Nygard's concise template scored highest overall**, with "Nygard supports concise and objective documentation, while MADR facilitates structural details." *Fetched and confirmed.* This is double-edged and we surface it as such: it warrants the "MADR-aligned but lean" middle path the repo already chose, **and** it is the strongest argument for keeping these additions optional rather than mandatory.

## Open questions

- **Should the Decision summary's first two lines (Decision / Because) be mandatory while the rest stay optional?** *Recommended default:* no — keep the whole block optional for simplicity and the lean default; revisit only if "optional" proves to mean "always skipped" (see the falsifiable assumption). *Owner:* eugenelim. *Decide-by:* this review (foldable into the D1 ruling).

## Follow-on artifacts

Filled in on acceptance:
- ADR-NNNN: ADR template adds optional Decision summary / Revisit-if / structured Confirmation — extends ADR-0027 (Related, not Supersedes).
- Errata entry on RFC-0038 naming RFC-0056.
- Pack change: `governance-extras` `new-adr` template + skill + evals + how-to guide; pack version bump.
- (No `docs/CONVENTIONS.md` change — status vocabulary is unchanged.)
