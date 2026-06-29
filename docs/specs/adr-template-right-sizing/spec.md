# Spec: adr-template-right-sizing

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0056, RFC-0038, ADR-0027
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An ADR author using the `new-adr` skill can put the decision on the first
screen, name a decision's own expiry condition, and make Confirmation a
checkable claim — through three **optional, lean** additions to the ADR
template: a first-screen `## Decision summary` block, a structured
`Revisit if:` trigger, and a `Mode / Signal / Owner` sub-structure for the
existing Confirmation section. Each field is deletable, length- or
aging-keyed, and sourced to a lean precedent, so a short ADR stays terse
while a heavy ADR gains first-screen retrieval and a named expiry condition —
without re-importing MADR-full ceremony. The users are adopters who install
`governance-extras` and scaffold ADRs from the bundled template, plus this
repo's own ADR authors.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep every new field **optional-deletable** — the `Revisit if:` trigger is
  recommended-not-required; nothing becomes mandatory surface that a short ADR
  carries as dead weight.
- Preserve answer-first ordering and the lean budget: source each field to a
  lean precedent (Y-statement for the summary, Nygard for the revisit trigger,
  MADR 4.0's existing Confirmation for the sub-structure).
- Co-land the three artifacts the change spans — the template/skill/eval/guide
  edits, the follow-on ADR, and the RFC-0038 Errata — atomically in the
  implementing PR.

### Ask first

- Any template or skill wording that would make a reader treat one of the
  three fields as **mandatory** rather than optional.
- Whether `Revisit if:` **replaces** the existing `**Neutral / to revisit:**`
  Consequences bullet or sits **alongside** it (default: replaces/renames it,
  per RFC-0056 R6).

(Two decisions resolved at approval — see Assumptions: the pack version rides
`0.4.0` and is released under it, no bump; the ADR-0041 ordinal is recorded by
filling RFC-0056's `## Follow-on artifacts` placeholder in place, no RFC-0056
errata.)

### Never do

- Touch `docs/CONVENTIONS.md` § 2 or `docs/CHARTER.md` — the status vocabulary
  is unchanged; any convention edit is separately RFC-gated and out of scope.
- Adopt any MADR-full element — no per-option pros/cons, no options-first
  ordering, no mandatory `Decision drivers`.
- Rewrite, convert, or re-number any existing ADR — forward-only; accepted
  ADRs are immutable.
- Edit the frozen argument body of RFC-0038, ADR-0027, or RFC-0056 — record
  against them via `## Errata` and an extending ADR only. (RFC-0056's
  `## Follow-on artifacts` placeholder is the sole sanctioned in-body exception,
  and only if explicitly authorized under *Ask first*.)
- Add a mechanical ADR-section lint — conformance stays reviewer-checked, as
  ADR-0027 settled; a lint remains separately RFC-gated.
- Add a new dependency, module boundary, or top-level directory.

## Testing Strategy

All changes are prose / template / JSON — no production logic — so verification
is **goal-based** with a **manual-QA** read-through where coherence is the
contract. No TDD-mode task; there is no compressible invariant to drive.

- **Template fields exist and are shaped correctly** (AC1–AC3): goal-based —
  `grep` confirms the `## Decision summary` block, the `**Revisit if:**` line,
  and the `Mode / Signal / Owner` Confirmation sub-structure are present with
  their OPTIONAL/deletable guidance comments.
- **Skill + guide describe the fields without making them mandatory** (AC4,
  AC6): manual-QA read-through — the prose reads coherently, keeps the
  offer-don't-force shape, and keys inclusion to length/aging/explicit-none.
- **Evals extended, queries untouched** (AC5): goal-based — `evals.json`
  parses, carries the three new behavioral assertions, and `eval_queries.json`
  is byte-unchanged. The assertions are LLM-judged by the pack-eval harness,
  not a unit gate — they are *authored* here; running them is the harness's job
  and is out of `make build-check`.
- **Follow-on ADR + governance records** (AC7–AC8b): goal-based (files present,
  cross-references resolve, frozen status lines intact, the RFC-0038 Errata carries
  a date + Approver signature, and RFC-0056's `## Follow-on artifacts` names
  ADR-0041 with the rest of its body unchanged) + manual-QA read-through that the
  ADR dogfoods the three new fields.
- **CONVENTIONS § 2 untouched** (AC9): goal-based — `git diff` shows no change
  to `docs/CONVENTIONS.md`.
- **Changelog + version + projection** (AC10–AC12): goal-based — `make
  build-self` leaves a clean `git status`; `lint-packs` and
  `tools/lint-agent-artifacts.py` pass.

## Acceptance Criteria

- [x] **AC1 (R2/D1 — first-screen Decision summary).** `assets/adr.md` gains an
  **optional, deletable** `## Decision summary` section placed immediately after
  the frontmatter and before `## Context`, carrying the five fields
  `Decision` / `Because` / `Applies to` / `Tradeoff accepted` / `Revisit if:`,
  with a guidance comment that keys inclusion to ADR length (include once the
  Decision isn't visible on the first screen; delete on a short ADR).
- [x] **AC2 (R6/D2 — structured Revisit-if trigger).** The Consequences section's
  ad-hoc `**Neutral / to revisit:**` bullet is renamed to a named
  `**Revisit if:**` line as the **canonical home** (Consequences is always
  present, so the trigger survives deletion of the optional summary); it is
  mirrored in `## Decision summary` when that block is present; and
  `Revisit if: stable — no foreseeable trigger` is documented as a valid
  explicit value.
- [x] **AC3 (R7/D3 — right-sized Confirmation).** The existing optional
  `## Confirmation` section, when present, carries a `Mode` / `Signal` / `Owner`
  sub-structure where `Mode` takes the RFC-0056 R7 enum verbatim —
  `reviewer-checked | lint/CI | architecture fitness test | periodic audit | none`
  — and `Mode: none` (with a one-line reason) is a **valid, explicit** value; the
  section stays deletable for trivial decisions, but the guidance prefers explicit
  `Mode: none` over silent deletion where a reader would plausibly expect a
  confirmation mechanism. No field beyond `Mode`/`Signal`/`Owner` is added (no
  per-option content — the lean line).
- [x] **AC4 (skill guidance).** `new-adr/SKILL.md` describes the three fields in
  the established offer-don't-force shape — inclusion keyed to length (summary),
  aging (revisit), and the explicit-`none` preference (Confirmation) — makes
  none of them mandatory, and states that when both are present the summary's
  `Revisit if:` **restates** (does not diverge from) the canonical Consequences
  line.
- [x] **AC5 (format-dependent evals).** `evals/evals.json` is extended with the
  three behavioral assertions track 1 foreclosed, authored verbatim as the
  following three assertion strings (so the eval checks authored-against-contract,
  not authored-against-itself):
  1. `A ## Decision summary block is present when the ADR is long enough that the Decision is not visible on the first screen, and is omitted on a short ADR where it would be pure redundancy`
  2. `A Revisit if: trigger is present in Consequences for a decision likely to age, with 'stable — no foreseeable trigger' as the valid explicit value when it will not`
  3. `When a ## Confirmation section is present it is concrete (a named Mode/Signal/Owner) or explicitly Mode: none with a one-line reason — not aspirational, and not silently omitted where a reader would expect a conformance check`

  The file parses as JSON; `eval_queries.json` (trigger detection) is byte-unchanged.
- [x] **AC6 (how-to guide sync).** Step 5 of
  `docs/guides/governance-extras/how-to/new-adr.md` describes the three fields
  consistently with the skill, so guide and skill don't contradict each other.
- [x] **AC7 (follow-on ADR extends ADR-0027).** A new ADR (ADR-0041) records the
  template extension with `Related:` pointing at ADR-0027 ("extends — read the
  two together"), **not** `Supersedes:`; it dogfoods the three new fields; and
  `docs/adr/README.md` gains its index row.
- [x] **AC8 (Errata on RFC-0038).** RFC-0038 gains an `## Errata` entry — dated
  and Approver-signed (eugenelim), per the RFC-0055 errata convention — naming
  RFC-0056 as extending its template decision; the rest of the RFC body stays
  frozen.
- [x] **AC8b (RFC-0056 ↔ ADR-0041 link).** RFC-0056's `## Follow-on artifacts`
  placeholder (`ADR-NNNN`) is filled in place with `ADR-0041` (Approver-authorized
  at approval — this is the section's self-described "filled in on acceptance"
  area, not an `## Errata`); the rest of the RFC-0056 body stays frozen. ADR-0041's
  `Related:` back-reference to RFC-0056 is authored in T5 and is the durable
  cross-link (the forward link in RFC-0056 is the backfill this AC authorizes; the
  back link is net-new content in a frozen-once-Accepted ADR).
- [x] **AC9 (CONVENTIONS § 2 untouched).** `docs/CONVENTIONS.md` is unchanged —
  the status vocabulary the section governs is not affected by this change.
- [x] **AC10 (changelog).** A `[Unreleased]` entry records the user-visible
  template + skill change under the chosen pack version.
- [x] **AC11 (version).** The change ships under `governance-extras` **`0.4.0`**
  (no bump — track-2 rides the unreleased 0.4.0, which is released carrying it):
  `pack.toml` and `.claude-plugin/plugin.json` stay at `0.4.0` and top-level
  `marketplace.json` reflects `0.4.0`.
- [x] **AC12 (projection clean).** `make build-self` projects the source change
  to `.claude/` and `.agents/` (plus marketplace aggregation) and leaves a clean
  `git status`; `lint-packs` and `tools/lint-agent-artifacts.py` pass.

## Assumptions

- Technical: the change is prose/template/JSON only — no code — touching
  `new-adr` `assets/adr.md`, `SKILL.md`, `evals/evals.json`, and the repo-owned
  how-to guide (source: RFC-0056 § Proposal; `docs/specs/new-adr-decision-capture/spec.md` shape precedent)
- Technical: `governance-extras` is at `0.4.0` and unreleased — `pack.toml` +
  `.claude-plugin/plugin.json` both `0.4.0`, changelog `[Unreleased]` holds the
  track-1 + RFC-0055 entries, no released `## [0.4.0]` heading (source: `grep version packs/governance-extras/pack.toml` + `docs/product/changelog.md`)
- Technical: the next ADR ordinal is `0041` (source: `python3 packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py docs/adr`)
- Technical: `evals.json` is LLM-judged behavioral assertions run by the
  pack-eval harness, not by `make build-check`; authoring is in scope, running
  is the harness's job (source: `packs/governance-extras/.apm/skills/new-adr/evals/evals.json` + memory: pack-evals detector uses stream-json)
- Process: RFC-0056 is Accepted, weight `heavy`, Approver-signed — the gate to
  build is satisfied (source: `docs/rfc/0056-…md` header)
- Process: vehicle is `## Errata` on RFC-0038 + an ADR that **extends** ADR-0027
  (`Related:`, not `Supersedes:`); `CONVENTIONS.md` § 2 stays untouched (source: RFC-0056 D4/D5)
- Process: this is full work-loop mode — governance-boundary + public-interface
  (published template) risk triggers fire (source: `work-loop` SKILL.md risk-triggers)
- Process: the change ships under `0.4.0` (no bump); 0.4.0 is released carrying
  track-2 (source: user confirmation 2026-06-28)
- Process: the ADR-0041 ordinal is recorded by filling RFC-0056's
  `## Follow-on artifacts` placeholder in place — no RFC-0056 `## Errata` — while
  RFC-0038 still gets its dated, Approver-signed `## Errata` (source: user confirmation 2026-06-28)
- Product: the three fields are optional-deletable (summary, Confirmation) /
  recommended-not-required (Revisit-if); users are `governance-extras` adopters
  and this repo's own ADR authors (source: RFC-0056 § Proposal)
