# Plan: adr-template-right-sizing

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is entirely prose / template / JSON, applied to the `new-adr` skill
pack plus two governance-record artifacts. The shape is: **extend the template
first** (it is the published interface every other artifact references), then
ripple the description outward — skill guidance, evals, how-to guide — then
record the change in governance (a follow-on ADR that dogfoods the new fields,
an Errata on the frozen RFC-0038), then version + changelog + projection.

The riskiest part is **not** mechanical — it is staying on the lean side of the
line ADR-0027 drew. Each field must read as optional and source to a lean
precedent; the failure mode is wording that makes a reader treat the summary as
mandatory or as a per-option debate surface. That risk is addressed by the
template's guidance comments and the skill prose, and checked by the manual-QA
read-through and the adversarial review, not by a unit test.

The template edit (T1) is the single upstream dependency: the evals (T3), the
how-to guide (T4), and the dogfooding ADR (T5) all reference the fields T1
introduces, so they cannot be authored against a template that doesn't yet carry
them. The RFC-0038 Errata (T6) is independent. Version + changelog (T7) and
projection (T8) close the loop.

## Constraints

- **RFC-0056** (Accepted, heavy) — the decision this implements; D1/D2/D3 fix the
  bindingness and shape of the three fields, D4 fixes the vehicle, D5 fixes the
  skill-pack-only scope.
- **ADR-0027** (frozen) — the lean-vs-full thesis this stays on the lean side of;
  the follow-on ADR *extends* it (`Related:`, not `Supersedes:`).
- **RFC-0038** (frozen) — the template decision this amends via `## Errata`.
- **RFC-0055 errata convention** — the `## Errata` shape used for T6 lives in the
  `new-rfc` skill; follow it.
- **AGENTS.local.md adopter-clean rule** — shipped pack artifacts (template,
  skill, evals) must not cite catalogue-internal RFC/ADR numbers; provenance
  lives in the ADR/spec, not the seed-shaped pack files.

## Construction tests

Most construction tests live per-task below. Cross-cutting checks:

**Integration tests:** none beyond per-task checks — there is no code path to
integrate; the "integration" surface is the projected `.claude/`/`.agents/` tree,
covered by T8's `make build-self` clean-tree check.

**Manual verification:**
- Read the assembled template end-to-end: the three fields read as optional, the
  answer-first ordering survives, and a short ADR could delete all three and
  remain valid.
- Read ADR-0041 as an adopter would: it demonstrates the three fields in use and
  extends — does not supersede — ADR-0027.

## Design (LLD)

Shape is `mixed` but the design surface is small (prose/template/JSON), so only
the two sub-sections that earn their place are kept.

### Design decisions

- **Decision summary lives before Context, as an optional `## H2`** — mirrors the
  RFC template's `## Reviewer brief` (duplicate-by-design first-screen surface).
  Rejected: a mandatory block (taxes short ADRs — the boundary case ADR-0027 was
  drawn to avoid). Traces to: AC1 · no contract.
- **`Revisit if:` canonical home is Consequences, mirrored in the summary** —
  Consequences is always present, so the trigger survives deletion of the
  optional summary. Rejected: home it only in the summary (would vanish when the
  summary is deleted). Traces to: AC2 · no contract.
- **`Mode: none` is an explicit value, not silent omission** — makes a
  non-checkable residual visible. Rejected: keep "delete the section" as the only
  no-confirmation path (hides the residual). Traces to: AC3 · no contract.
- **Follow-on ADR extends, Errata records** — ADR-0027's thesis stands; we add
  lean-compatible fields on the same side of the line (precedent: ADR-0037
  extends ADR-0034). Traces to: AC7, AC8 · no contract.

### Component / module decomposition

- **Reused, edited:** `assets/adr.md` (template), `SKILL.md` (procedure step 6
  guidance), `evals/evals.json`, the how-to guide.
- **New:** `docs/adr/0041-*.md` (the dogfooding ADR), an `## Errata` block on
  `docs/rfc/0038-*.md`, a changelog entry, an index row in `docs/adr/README.md`.
- **Generated, not hand-edited:** the `.claude/` and `.agents/` projections and
  `marketplace.json` aggregation — produced by `make build-self` (T8), never
  edited directly.

## Tasks

### T1: Extend the ADR template with the three fields

**Depends on:** none

**Tests:**
- Goal-based: `grep -n "## Decision summary" packs/governance-extras/.apm/skills/new-adr/assets/adr.md` returns a match positioned before `## Context`. Verifies AC1.
- Goal-based (AC2, two-part — binds the match to the canonical home): `awk '/## Consequences/,/## Confirmation/' assets/adr.md | grep -q '\*\*Revisit if:\*\*'` succeeds (the named line lives in Consequences) **and** `! grep -q 'Neutral / to revisit' assets/adr.md` (the old ad-hoc bullet is renamed, not merely supplemented). A bare `grep "Revisit if"` is insufficient because R2 also puts the phrase inside `## Decision summary`. Verifies AC2.
- Goal-based: inside `## Confirmation`, `Mode:` appears alongside `Signal:` and `Owner:`, and the `Mode` enum line carries the verbatim RFC-0056 R7 values per AC3. Verifies AC3.
- Goal-based (adopter-clean — `.apm/skills/` files are NOT scanned by `lint-seeds`, so verify by hand): `! grep -nE 'RFC-0[0-9]|ADR-0[0-9]' packs/governance-extras/.apm/skills/new-adr/assets/adr.md` (no catalogue-internal numbers in the shipped template; the literal `ADR-NNNN` placeholder is allowed).
- Manual-QA: read the template top-to-bottom — all three fields carry OPTIONAL/deletable guidance comments; answer-first ordering holds; a short ADR could delete all three.

**Approach:**
- Add a `## Decision summary` section immediately after the frontmatter HTML
  comment block and before `## Context`, with the five fields from RFC-0056 R2
  and a guidance comment keying inclusion to length (delete on a short ADR).
- In `## Consequences`, rename the `**Neutral / to revisit:**` bullet to a named
  `**Revisit if:**` line; note `Revisit if: stable — no foreseeable trigger` as a
  valid explicit value in the section's guidance comment.
- In `## Confirmation`, add the `Mode` / `Signal` / `Owner` sub-structure (with
  the `Mode` enum from RFC-0056 R7 including `none`) and update the OPTIONAL
  comment to prefer explicit `Mode: none` over silent deletion where a reader
  would expect a mechanism.
- Keep all guidance generic — no catalogue-internal RFC/ADR numbers in the
  shipped template (adopter-clean).

**Done when:** the three greps match as specified, the old revisit bullet is
gone, and the read-through confirms optionality + answer-first ordering.

### T2: Describe the three fields in the skill

**Depends on:** T1

**Tests:**
- Goal-based: `grep -n "Decision summary\|Revisit if\|Mode: none" SKILL.md` shows all three referenced in the drafting guidance (step 6 / the optional-sections area).
- Goal-based (adopter-clean): `! grep -nE 'RFC-0[0-9]|ADR-0[0-9]' packs/governance-extras/.apm/skills/new-adr/SKILL.md` (the `ADR-NNNN` placeholder is allowed; catalogue numbers are not).
- Manual-QA: the prose keeps the offer-don't-force shape — inclusion keyed to length (summary), aging (revisit), explicit-`none` (Confirmation) — and makes none mandatory; when both summary and Consequences are present it states the summary's `Revisit if:` **restates** (does not diverge from) the canonical Consequences line.

**Approach:**
- Extend the existing optional-sections guidance in `SKILL.md` step 6 (today it
  covers `Decision drivers` and `Confirmation`) to add the Decision summary and
  Revisit-if, and to restructure the Confirmation guidance around
  Mode/Signal/Owner with the explicit-`none` preference.
- Match the prose register of the track-1 edits; no repo-internal citations.

**Done when:** the grep matches and the read-through confirms the offer-don't-force
shape with nothing made mandatory.

### T3: Add the three format-dependent evals

**Depends on:** T1

**Tests:**
- Goal-based: `python -c "import json; json.load(open('packs/governance-extras/.apm/skills/new-adr/evals/evals.json'))"` succeeds.
- Goal-based: the three assertion strings pinned verbatim in spec AC5 are each present in `evals.json` (grep each one literally) and reference the three fields T1 added. Verifies AC5.
- Goal-based: `git diff --stat packs/governance-extras/.apm/skills/new-adr/evals/eval_queries.json` is empty (byte-unchanged).
- Goal-based (adopter-clean): `! grep -nE 'RFC-0[0-9]|ADR-0[0-9]' packs/governance-extras/.apm/skills/new-adr/evals/evals.json`.

**Approach:**
- Extend `evals.json` with behavioral assertions for: Decision summary present
  when length warrants; Revisit trigger present for an aging decision;
  Confirmation concrete or explicitly `Mode: none`. Prefer extending an existing
  eval scenario's assertions where it fits; add a focused scenario only if a new
  prompt is needed to exercise an aging/heavy ADR.
- Leave `eval_queries.json` untouched.

**Done when:** the JSON parses, the three assertions are present, and
`eval_queries.json` is unchanged.

### T4: Sync the how-to guide

**Depends on:** T1

**Tests:**
- Goal-based: `grep -n "Decision summary\|Revisit if\|Mode" docs/guides/governance-extras/how-to/new-adr.md` shows the three fields described in Step 5.
- Manual-QA: guide and skill don't contradict each other on optionality or shape. Verifies AC6.

**Approach:**
- Extend Step 5 ("Draft the body sections") to describe the three new optional
  fields alongside the existing `Decision drivers` / `Confirmation` mention,
  matching the guide's task-oriented register.

**Done when:** the grep matches and a read-through confirms guide/skill agreement.

### T5: Author the follow-on ADR (ADR-0041) and index it

**Depends on:** T1

**Tests:**
- Goal-based: `docs/adr/0041-*.md` exists; `grep "Related:" ` cites ADR-0027 with "extends"; no `Supersedes:` of ADR-0027. Verifies AC7.
- Goal-based: `docs/adr/README.md` gains the ADR-0041 row.
- Manual-QA: the ADR dogfoods the three new fields (it carries a `## Decision summary`, a `Revisit if:`, and a structured `Confirmation`) **and** its summary `Revisit if:` is identical to its Consequences `Revisit if:` line (the AC4 restate invariant, exercised here on a real ADR).

**Approach:**
- Run `new-adr` (or scaffold from the just-edited `assets/adr.md`) for "ADR
  template adds optional Decision summary / Revisit-if / structured Confirmation",
  status `Accepted` (RFC-0056 is Accepted and Approver-signed), `Related:`
  ADR-0027 (extends — read the two together) + RFC-0056 + RFC-0038.
- Write it so it visibly uses the three new fields — it is the dogfood.
- Add the index row to `docs/adr/README.md`.

**Done when:** the ADR exists, extends (not supersedes) ADR-0027, dogfoods the
three fields, and the index row is present.

### T6: Errata on RFC-0038 + fill RFC-0056 follow-on placeholder

**Depends on:** T5 (needs the concrete ADR-0041 ordinal)

**Tests:**
- Goal-based: `grep -n "## Errata" docs/rfc/0038-*.md` matches; the entry names RFC-0056 **and** carries a date + Approver signature line (`eugenelim`) per the RFC-0055 convention; the rest of the RFC-0038 body is unchanged (diff scoped to the appended section). Verifies AC8.
- Goal-based: RFC-0056's `## Follow-on artifacts` placeholder `ADR-NNNN` is replaced with `ADR-0041`; the rest of the RFC-0056 body is unchanged (diff scoped to that line). Verifies AC8b.

**Approach:**
- Append an `## Errata` section to RFC-0038 per the RFC-0055 convention — dated
  and Approver-signed (`eugenelim`) — naming RFC-0056 as extending its template
  decision. RFC-0038 has no prior errata, so this is a **single dated, signed
  bullet** — below the RFC-0055 two-layer threshold (>1 entry / supersession), so
  no `### Current state` / `### History` structure.
- Fill RFC-0056's `## Follow-on artifacts` placeholder in place: `ADR-NNNN` →
  `ADR-0041` (Approver-authorized — the section's self-described "filled in on
  acceptance" area; **no RFC-0056 `## Errata`**). Leave the rest of the RFC-0056
  body frozen. ADR-0041's `Related:` back-reference (T5) carries the link too.

**Done when:** RFC-0038 carries the dated, signed Errata; RFC-0056's follow-on
list names ADR-0041; and neither frozen argument body is otherwise touched.

### T7: Changelog entry (version stays 0.4.0)

**Depends on:** T1, T2, T3, T4
<!-- T5/T6 (the ADR + Errata governance records) are deliberately not upstream:
the changelog narrates the user-visible template + skill change, not the
governance-record artifacts. T8 closes the DAG over all of T1–T7. -->

**Tests:**
- Goal-based: `docs/product/changelog.md` `[Unreleased]` gains an entry for the
  template + skill change under `governance-extras 0.4.0`. Verifies AC10.
- Goal-based: `pack.toml` + `.claude-plugin/plugin.json` remain at `0.4.0`
  (no bump — track-2 rides the unreleased 0.4.0). Verifies AC11.

**Approach:**
- Add a `### Added` (template fields are new surface) `[Unreleased]` changelog entry
  written for users, describing the three optional fields, tagged `governance-extras
  0.4.0` to sit beside the existing track-1 + RFC-0055 entries.
- **Distinguish from track 1 explicitly.** The existing track-1 entry states "none
  of which changes the ADR template's sections or fields"; track 2 *does* change the
  template's sections/fields and adds *format-dependent* evals. Word the new entry so
  a reader can tell the two apart and so it does not read as contradicting the
  track-1 entry (e.g. open with "the ADR *template* now offers three optional fields"
  to contrast with track-1's guidance-only scope).
- No version-file change: 0.4.0 is unreleased and ships carrying track-2.

**Done when:** the changelog entry is present and the version files are unchanged
at `0.4.0`.

### T8: Project and verify clean

**Depends on:** T1, T2, T3, T4, T5, T6, T7

**Tests:**
- Goal-based: `make build-self` then `git status --porcelain` is empty (clean tree). Verifies AC12.
- Goal-based: `lint-packs` passes; `python tools/lint-agent-artifacts.py` passes (the two lint surfaces).
- Goal-based: `git diff --stat docs/CONVENTIONS.md` is empty. Verifies AC9.
- Goal-based: `python .claude/skills/work-loop/scripts/lint-spec-status.py` is clean for this spec — spec Status is `Shipped` and every AC is `[x]`.

**Approach:**
- **Flip spec metadata in this implementing PR** (the spec+code land atomically, so
  this is not a forward-claim): set `docs/specs/adr-template-right-sizing/spec.md`
  Status `Approved` → `Shipped`, check every AC `[x]`, and flip the plan Status to
  `Done`. (Memory: set final status in the implementing PR.)
- Run `make build-self` to project core + governance-extras to `.claude/` +
  `.agents/` and re-aggregate `marketplace.json`.
- Run both lint surfaces by hand (memory: only `lint-packs` is in the local gate;
  `lint-agent-artifacts.py` is CI-only).
- Confirm `docs/CONVENTIONS.md` is untouched.

**Done when:** spec is `Shipped` with all ACs `[x]`, `make build-self` leaves a clean
tree, both lints pass, and CONVENTIONS shows no diff.

## Rollout

- **Delivery:** documentation/template change, no flag, no runtime. Reversible —
  every field is optional-deletable and the version (if bumped) is not yet
  released. The one not-cleanly-reversible artifact is ADR-0041 (immutable once
  Accepted) and the RFC-0038 Errata (append-only) — both are intended-permanent
  records, not rollback-sensitive.
- **Infrastructure:** none.
- **External-system integration:** none — pack consumed via APM / Claude plugins /
  CLI; projection is the only "deploy" and is in-repo.
- **Deployment sequencing:** template (T1) before everything that references it;
  ADR (T5) before the RFC-0056 follow-on backfill (T6); projection (T8) last.

## Risks

- **Lean-line erosion** — the additions read as ceremony or invite per-option
  reasoning into the summary. Mitigation: fixed-shape five-field summary, optional
  guidance, manual-QA read-through, adversarial review. (Spec Boundaries / Never
  do.)
- **Adopter-clean leak** — a catalogue-internal RFC/ADR number sneaks into the
  shipped template/skill/evals. Mitigation: keep provenance in ADR-0041 + this
  spec; `lint-seeds`/reviewer catches numbers in seed-shaped pack files.
- **Projection drift** — a prior PR edited a projected path only; `make
  build-self` reverts it. Mitigation: T8 checks `git status` is clean and
  investigates any unexpected revert (memory: build-self undoes projection-only
  edits).
- **Version-decision churn** — if the user picks `0.5.0` after T7 runs against
  `0.4.0`, T7 + T8 re-run. Cheap; the decision is confirmed before T7 executes.

## Changelog

- 2026-06-28: initial plan — drafted from RFC-0056 (Accepted) as the gated
  implementing spec/plan for track 2.
