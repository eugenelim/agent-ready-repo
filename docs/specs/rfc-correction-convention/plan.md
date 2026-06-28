# Plan: RFC correction convention (Errata / Amendments)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is prose, in four files: the `new-rfc` skill's `SKILL.md` (the
source of truth), its `assets/rfc.md` template (the optional scaffold), the
repo-only how-to guide, and the changelog. There is no executable behavior —
the riskiest part is *prose precision*: wording the Errata/Amendments split and
the two-layer threshold so an author can't misfile, and shaping the asset block
so it reads as clearly conditional and isn't cargo-culted into empty RFCs.

Order of operations follows the dependency arrows: `SKILL.md` first, because it
is the authoritative description every other artifact points at; then
`assets/rfc.md`, whose scaffold must mirror the shape `SKILL.md` describes; then
the how-to note, which points at the skill; then the changelog; then a final
projection-and-gates task that runs `make build-self`, both lint surfaces, and
the dogfood walk against RFC-0048. The convention's two-layer shape is lifted
directly from the worked precedent (RFC-0048 / PR #430) rather than invented, so
the dogfood walk is a real check, not a formality.

**Declined temptations (declared, so REVIEW can catch drift):**

- *A mechanical lint enforcing the Errata/Amendments structure* — declining;
  RFC-0055's Open question recommends *no* (the structure is optional and
  threshold-gated; "erratum vs amendment" is a lifecycle judgment, not a regex),
  revisit only if drift recurs.
- *Retrofitting the 24 existing correction sections for back-catalogue
  consistency* — declining; RFC-0055 D5 is forward-only, a big-bang diff against
  frozen history is churn for cosmetics.
- *Adding the convention to `CONVENTIONS.md` (the repo's prevailing Option-C
  pattern)* — declining; RFC-0055 D4 forbids it for this case, to keep a
  `governance-extras` feature out of a `core`-seeded doc.
- *Editing the skill's frontmatter `description` or adding an eval for the new
  convention* — declining; the skill's trigger is unchanged (RFC drafting), and
  an eval for a prose convention is speculative.

## Constraints

- **RFC-0055** (Accepted 2026-06-28) — D1 (lifecycle-keyed Errata/Amendments),
  D2 (optional threshold-gated two-layer, current-state wins), D3 (append-only,
  supersession, whole-RFC carve-out), D4 (skill is the sole source of truth, no
  `CONVENTIONS.md` change), D5 (forward-only).
- **`CONVENTIONS.md` § Document lifecycle** — the Frozen (`accepted/rejected
  rfc/*`) vs Governance (`open rfc/*`) classification the naming split keys off.
- **RFC-0048 / PR #430** (commit `159853b1`) — the worked two-layer precedent the
  convention generalizes; the dogfood walk verifies against it.
- **ADR supersession** (`CONVENTIONS.md` § 2, supersede-in-place) — precedent for
  D3's whole-RFC carve-out.

## Construction tests

Most construction tests are per-task `grep` checks (below). Cross-cutting:

**Integration tests:** none beyond per-task tests.
**Cross-cutting verification:**
- `make build-self` — source edits project to `.claude/skills/new-rfc/` with a
  clean drift gate.
- `make lint-packs` and `python tools/lint-agent-artifacts.py` — both lint
  surfaces pass.
- `git diff --name-only` shows no `docs/CONVENTIONS.md` change and no edit to any
  `docs/rfc/*.md` (all RFCs, not just `00*`).
- **Dogfood walk (manual QA):** apply the documented `SKILL.md` procedure to
  RFC-0048's correction state (`docs/rfc/0048-*.md`, the `## Amendments`
  section) and confirm it reproduces the same two-layer *structure* — a
  current-state layer (authoritative, wins) over a dated append-only audit
  trail; record the observed result in the PR description. Heading wording need
  not match (RFC-0048 predates the convention; D5 forward-only — read, not
  retrofitted).

## Design (LLD)

Shape `mixed`, but this is a documentation change, so only the design *decisions*
need recording; the remaining LLD sub-sections are pruned.

### Design decisions

- **Section placement in `SKILL.md`** — the convention is recorded as a new
  section after `## After acceptance` (corrections are a post-publication
  activity), not folded into the drafting procedure. Traces to: AC1–AC3.
- **Section names** — `## Errata` and `## Amendments`, matching the
  Document-lifecycle vocabulary verbatim so the heading itself signals whether
  the text beneath it is immutable. Traces to: AC1.
- **Scaffold placement in `assets/rfc.md`** — a trailing commented block after
  `## Follow-on artifacts`, since corrections are the last thing an RFC accretes;
  shipped as an HTML comment (not a live heading) so an empty new RFC carries no
  visible correction section. Traces to: AC4.
- **How-to note placement** — extends the guide's "After acceptance" step with a
  short pointer to the skill's convention rather than restating it (one canonical
  home). Traces to: AC6.

## Tasks

### T1: Document the correction convention in `new-rfc` `SKILL.md`

**Depends on:** none

**Tests:** (goal-based)
- `grep` `SKILL.md` confirms both `Errata` (Frozen) and `Amendments` (in-flight
  Open) are named and selected by lifecycle class — AC1.
- `grep` confirms the two-layer structure is documented (a current-state layer
  over a history/audit-trail layer — assert the *structure* and the rule words,
  not a literal heading string), the threshold ("more than one entry, or any
  entry supersedes another"), and "current-state … wins" — AC2.
- `grep` confirms append-only, the `*(Superseded: …)*` in-place reword scoped to
  Amendments, and the whole-RFC-replacement-out-of-scope carve-out naming a
  superseding RFC — AC3.

**Approach:**
- Add a new `## Recording corrections (Errata / Amendments)` section after
  `## After acceptance` in
  `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`.
- Cover D1 (lifecycle-keyed split, cross-referencing `CONVENTIONS.md` §
  Document lifecycle), D2 (optional threshold-gated two-layer with the
  current-state-wins rule), D3 (append-only, no per-entry ritual, optional
  Amendments-only reword, whole-RFC carve-out).
- Cite RFC-0048 / PR #430 as the worked two-layer precedent.

**Done when:** all three `grep` checks pass and the section reads coherently
against `CONVENTIONS.md` § Document lifecycle.

### T2: Add the optional conditional scaffold to `assets/rfc.md`

**Depends on:** T1

**Tests:** (goal-based)
- `grep` `assets/rfc.md` confirms a **commented** correction-section block
  exists with a delete-unless-accumulating instruction — AC4.
- `grep` confirms the block carries the two-layer skeleton (a current-state
  layer over a history/audit-trail layer) matching the shape T1 documents —
  assert the structure, not a literal heading string — AC4.

**Approach:**
- Append a commented HTML block after `## Follow-on artifacts` in
  `packs/governance-extras/.apm/skills/new-rfc/assets/rfc.md` showing the
  `## Errata` (or `## Amendments`) section with the optional Current state /
  History skeleton.
- Head it with a "delete unless this RFC is accumulating corrections"
  instruction so it is never filled into an empty RFC.

**Done when:** both `grep` checks pass; the block is an HTML comment, not a live
empty section.

### T3: Add the how-to dogfood note

**Depends on:** T1

**Tests:** (goal-based)
- `grep` `docs/guides/governance-extras/how-to/new-rfc.md` confirms a short note
  referencing the correction convention and pointing at the skill — AC6.

**Approach:**
- Extend the guide's "Step 7 — After acceptance" (or its Related/Pitfalls
  region) with a short note that an RFC records post-publication corrections
  under the skill's Errata/Amendments convention, pointing at the skill.
- Keep it a pointer, not a restatement (the skill is the single canonical home);
  the guide is repo-only and does not ship with the pack.

**Done when:** the `grep` check passes; the note points at the skill and does not
duplicate the convention text.

### T4: Record the change in the changelog

**Depends on:** T1, T2, T3

**Tests:** (goal-based)
- `grep` `docs/product/changelog.md` `[Unreleased]` confirms an entry naming
  RFC-0055 and `governance-extras` 0.4.0 — AC7.

**Approach:**
- Add a bullet under the existing `[Unreleased]` block describing the new
  correction convention in user-facing terms, attributing it to RFC-0055 and
  `governance-extras` 0.4.0 (no version bump — rides the unreleased 0.4.0).

**Done when:** the `grep` check passes; the wording reads for users, not contributors.

### T5: Project and verify the gates

**Depends on:** T1, T2, T3, T4

**Tests:** (goal-based + manual QA — cross-cutting)
- `make build-self` projects the edits to `.claude/skills/new-rfc/` with a clean
  drift gate — AC8.
- `make lint-packs` and `python tools/lint-agent-artifacts.py` both pass — AC8.
- `git diff --name-only` shows no `docs/CONVENTIONS.md` change and no
  `docs/rfc/*.md` edit (all RFCs) — AC5.
- Dogfood walk: the documented convention reproduces RFC-0048's two-layer
  *structure* (current-state-wins over an append-only audit trail), result
  recorded in the PR description — AC9.

**Approach:**
- Clear any stray `__pycache__` under `packs/` and `.claude/` first (it trips the
  self-host dry-run drift gate), then run `make build-self`.
- Run both lint surfaces; resolve any finding.
- Confirm the constraint boundaries from the diff, then walk the convention
  against RFC-0048 and record the observed shape.

**Done when:** all gates green; `git status` clean except the four source/doc
edits (`SKILL.md`, `assets/rfc.md`, the how-to guide, the changelog), this
spec+plan, and their `.claude/` / `.agents/` projections; the dogfood walk
reproduces the two-layer structure and its result is recorded.

## Rollout

Pure documentation/convention change — no infrastructure, no external-system
integration, no deployment sequencing. Delivery is the merge itself; it ships to
adopters the next time they install or update `governance-extras` (the convention
travels in the skill). Reversible by reverting the PR; nothing irreversible.

## Risks

- **Prose ambiguity → authors misfile a correction.** Mitigation: key the naming
  to the existing Document-lifecycle table and lean on the RFC-0055 census
  (Errata applied correctly 16/16 on Frozen RFCs today) — the convention mostly
  writes down an existing instinct.
- **The optional scaffold gets cargo-culted into empty RFCs.** Mitigation: ship
  it as a commented, clearly-conditional block with a delete-unless instruction,
  never a live empty section.
- **Source edited but not projected → `build-self` drift gate red in CI.**
  Mitigation: T5 runs `make build-self` and confirms a clean tree before finish.

## Changelog

- 2026-06-28: initial plan.
