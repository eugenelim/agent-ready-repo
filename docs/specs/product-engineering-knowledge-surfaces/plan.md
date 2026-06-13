# Plan: product-engineering-knowledge-surfaces

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This mirrors the `architect-knowledge-surfaces` change (PR #297) with a
different lens. The change is almost entirely prose authored into one new skill
reference, plus a single conditional step wired into `frame-intent/SKILL.md`, a
brownfield-gate wiring note in an existing reference, and the mechanical bump /
changelog / build-self that any non-cosmetic product-engineering-pack change
requires.

The riskiest part is *not* code — it is getting two things right: (1) the
detection mechanism worded so it is genuinely harness-agnostic (names no tool),
genuinely permissive (zero cost until a surface is detected), and degrades
honestly; and (2) the **lens discipline** — the reference must carry exactly the
four problem-framing areas and deliberately *omit* the four solution-design ones,
or product-engineering drifts into the architect's space. So the reference is
authored first (T1) carrying the subset + the omission rationale + the
shared-canonical-core anchor, the SKILL.md routing step and the maturity-gate
wiring second (T2), the mechanical bump third (T3), then build-self + the full
gate set (T4), then the detect-vs-degrade manual QA (T5).

Because product-engineering is a user-scope-default pack, the skill content
never lands in this repo's `.claude/` tree; the only working-tree projection
effect of the change is the `marketplace.json` version bump. The gate set is
therefore lint/build/pytest + build-self, not the projection `pre-pr` path.

## Constraints

- No ADR/RFC governs this; the doctrine lives in the skill reference, mirroring
  the owner's decision on `architect-knowledge-surfaces` (spec Assumptions).
- Self-hosting: edit `packs/product-engineering/...` source only; never the
  projected tree. `make build-self` reconciles `marketplace.json`.
- Distribution-agnostic + no-cross-pack-dependency are hard spec Boundaries
  (Route B was rejected): the reference is product-engineering-local — a
  *duplicate* of the shared core, anchored to architect's canonical reference by
  a note, not a shared file.
- Strict-subset discipline: areas 3/5/6/7 must not appear (spec Boundary).
- Version 0.3.0 — base advanced via #298 (value-stream 0.2.0) then #300
  (enriched-manifest 0.2.1); this feature takes the next minor, 0.3.0, atop #300's
  enriched `pack.toml`. The now-Shipped sibling work is left untouched (spec
  Boundary + Assumptions).

## Construction tests

Most verification is per-task below. Cross-cutting:

**Integration tests:** none beyond per-task checks.
**Manual verification:** the detect-vs-degrade QA in T5 is the one cross-cutting
manual check; it exercises the SKILL.md step (T2) against the reference (T1)
end-to-end as an adopter would receive them.

## Design (LLD)

Shape is `mixed` but the feature is skill-authoring, so only one sub-section
earns its place; the rest are pruned.

### Design decisions

- **Progressive disclosure gate.** The SKILL.md step does the cheap detection
  probe inline; the four-area taxonomy reference loads **only when a surface is
  detected**. Rejected: always loading the taxonomy (taxes every framing run);
  rejected: putting the taxonomy in the SKILL.md body (bloats the lean file and
  always-loads). Traces to: AC6 · no contract.
- **Strict subset, not a parallel taxonomy.** Reuse architect's eight-area MECE
  core and *select* the four problem-space areas; do not invent a new taxonomy
  and do not include the four solution-design areas. The selection itself is the
  lens. Rejected: an independent product taxonomy (would diverge from architect
  and re-derive MECE); rejected: all eight areas (drifts into solution space).
  Traces to: AC1, AC2, AC3 · no contract.
- **Detection over declaration.** Discover surfaces from the live tool/CLI
  surface, not from a declared registry or shared-config file. Rejected: an
  AGENTS.md registry (fails at user-scope, no anchor file) and a `~/.agentbundle`
  registry (breaks skill isolation). Traces to: AC4, AC8 · no contract.
- **Generic compose/degrade framing (divergence from architect).**
  `frame-intent` does not compose with `research` today, so the step uses the
  generic "compose if present, degrade if absent" framing rather than architect's
  "as the skill already does when `research` is absent." Lowered-confidence
  markers route into the intent's `Assumptions`. Traces to: AC5, AC6 · no
  contract.
- **Brownfield gate reuse for area 2.** The current-landscape area wires into the
  *existing* greenfield/brownfield maturity gate in `current-state-inputs.md`
  rather than adding a new gate. Traces to: AC7 · no contract.

## Tasks

### T1: Author the knowledge-surfaces reference (problem lens)

**Depends on:** none

**Touches:** packs/product-engineering/.apm/skills/frame-intent/references/knowledge-surfaces.md

**Tests:**
- `grep -iE 'mcp__|servicecatalog|confluence|backstage|jira|<any concrete tool/CLI>'`
  over the new file returns nothing — proves no hardcoded surface name (AC4).
- `grep` confirms the four-area subset is present and areas 3/5/6/7 are **named
  as omitted** with a why (AC1, AC2).
- Manual read confirms: the four areas each with question + **problem-framing**
  trigger (AC1); the omission rationale (AC2); the shared-canonical-core anchor
  naming the architect reference + the modality×space placement of the four +
  the 2/4 adjacency seam (AC3); the detection rules incl. the internal-only /
  name-the-surface / single-source rails (AC4); and the degradation rules as
  reference text — clauses (a)/(b)/(c), with (a) routing the marker into the
  intent's `Assumptions` (AC5, "reference states" half; the "honours" half is T2,
  observed in T5).

**Approach:**
- Create
  `packs/product-engineering/.apm/skills/frame-intent/references/knowledge-surfaces.md`.
- Section 1: the four-area problem-framing subset table (area · question it
  answers · problem-framing consult trigger), area 1 & 8 PRIMARY, 2
  brownfield-only, 4 light; then the explicit omission of 3/5/6/7 with a why; then
  the shared-canonical-core anchor note (architect = canonical), the
  modality×space placement of the four, and the 2/4 adjacency-seam note.
- Section 2: the harness-agnostic detection mechanism (discover from the
  session's tools/CLIs — tool search where deferred, loaded list otherwise; no
  hardcoded names; internal-only / name-the-surface / single-source rails) and
  the graceful-degradation rule (ask + lower confidence into the intent's
  `Assumptions`; never fabricate; sensitive/read-only = ask-before-quoting).
- Keep the **problem-framing lens** throughout; this reference is problem-only.

**Done when:** the file exists, the grep tests are clean, and a read confirms
AC1/AC2/AC3/AC4/AC5 ("reference states" half) are satisfied.

### T2: Wire the conditional consult step + the brownfield maturity gate

**Depends on:** T1

**Touches:** packs/product-engineering/.apm/skills/frame-intent/SKILL.md, packs/product-engineering/.apm/skills/frame-intent/references/current-state-inputs.md

**Tests:**
- `python tools/lint-skill-spec.py packs/product-engineering/.apm/skills/frame-intent/SKILL.md`
  passes (body under cap; frontmatter intact).
- The new step references `references/knowledge-surfaces.md`, is conditional on
  surface detection, names no concrete tool, and uses the generic compose/degrade
  framing (`grep` for the reference path; manual read for the conditional +
  framing) — AC6.
- The step wording instructs the skill to **honour** the degrade rule (ask +
  lower confidence into `Assumptions`; ask-before-quoting sensitive sources) —
  manual read. This is the "SKILL.md step honours" half of AC5 (observed in T5).
- `current-state-inputs.md` names the current-landscape area as the brownfield
  knowledge-surface input and preserves greenfield = skip (`grep` for the
  cross-reference + manual read) — AC7.
- `git diff` shows `de-risk-intent/SKILL.md` and `decompose-intent/SKILL.md`
  untouched (Never-do Boundary).

**Approach:**
- Insert a single conditional procedure step into `frame-intent/SKILL.md` after
  the intake step (so Scale + maturity are known) and before the outcome/
  opportunity shaping it feeds. Renumber the subsequent steps and update the one
  `(step 4)` cross-reference inside the intake step accordingly. Wording: *if you
  detect a knowledge-retrieval surface in this session, load
  `references/knowledge-surfaces.md` and consult the problem-framing areas your
  intent turns on (business-domain meaning, in-flight work); name the surface you
  used (or "none"); otherwise ask the user for the missing context and lower
  confidence, never fabricate, and ask before quoting sensitive sources.*
- In `current-state-inputs.md`, add a short note under the maturity gate wiring
  the **brownfield** branch to the current-landscape area of the new reference
  (present → consult; absent → ask + degrade); leave greenfield = skip unchanged.
- Keep both edits frugal.

**Done when:** `lint-skill-spec` is green, the step is present and conditional,
the maturity-gate wiring is in place, and the two sibling SKILL.md files are
byte-unchanged.

### T3: Version bump + changelog

**Depends on:** none

**Tests:**
- `grep '0.3.0' packs/product-engineering/pack.toml packs/product-engineering/.claude-plugin/plugin.json`
  matches the pack `version` in both (AC9).
- `docs/product/changelog.md` `[Unreleased]` contains the new entry (AC10).

**Approach:**
- Bump `version` `0.2.1 → 0.3.0` in `packs/product-engineering/pack.toml` (the
  `[pack]` version, not the unrelated `[pack.adapter-contract] version`) and in
  `packs/product-engineering/.claude-plugin/plugin.json`, preserving #300's
  enriched metadata fields. (Base is 0.2.1 after the #298→#300 rebase chain;
  authored against 0.1.0, target 0.3.0 unchanged.)
- Add an `[Unreleased]` changelog entry: frame-intent now detects and consults an
  enterprise knowledge-retrieval surface through a problem-framing lens when
  present, degrading gracefully when absent.

**Done when:** both version greps show 0.3.0 and the changelog entry is present.

### T4: build-self + full gate set

**Depends on:** T1, T2, T3

**Tests:**
- `make build-self` exits clean; `git diff .claude-plugin/marketplace.json` shows
  product-engineering at `0.3.0` and no unrelated pack churn (AC11).
- `git status` shows no stray/untracked artifacts (no `__pycache__`) (AC11).
- **Diff inspection** over `git diff origin/main...` confirms the AC8 negatives:
  no new registry or shared-config file, no `~/.agentbundle` read added to any
  skill, no new dependency in `packs/product-engineering/pack.toml`, no new
  cross-pack artifact, and the four solution-design areas (3/5/6/7) do not appear
  (AC8).
- `python tools/lint-packs.py`, `python tools/lint-agent-artifacts.py`,
  `make validate`, `make build` pass; and the marketplace-aggregation suites that
  guard a non-projected user-scope pack bump pass by explicit path —
  `pytest packages/agentbundle/agentbundle/build/tests/test_self_host_check.py
  packages/agentbundle/agentbundle/build/tests/test_pipeline.py` (AC12).

**Approach:**
- Clear any stray `__pycache__` under `packs/` and `.claude/` first (known
  build-check tripwire).
- Run `make build-self`; inspect the `marketplace.json` diff is version-only.
- Run the lint/validate/build/pytest gate set by hand (build-check parity for a
  non-projected pack).

**Done when:** build-self is clean, marketplace.json is version-only, and every
gate is green with a clean tree.

### T5: Detect-vs-degrade manual QA

**Depends on:** T4

**Fixed driver** (same prompt across scenarios): framing prompt *"Frame the
intent for a self-serve refund flow in our billing product."* Mock surfaces:
- **domain/in-flight mock** — a stub tool that answers the **business-domain**
  and **in-flight** areas (e.g. "'refund' means a credit-note reversal here, and
  team X is already building a refunds API this quarter").
- **landscape mock (brownfield)** — a stub answering the **current-landscape**
  area, used in the brownfield scenario.
- **sensitive mock** — a stub flagged read-only / sensitive returning
  do-not-quote content (e.g. an internal roadmap memo).

**Tests** (each maps to a named AC5 clause / AC13 scenario):
- *(manual QA, surface-present)* With the domain/in-flight mock exposed, run the
  driver through `frame-intent`; **invariant:** the intent's opportunity/outcome
  uses the org's real meaning of "refund" and the assumptions flag the in-flight
  refunds API (no duplicate bet), and the reference was loaded. Record the
  excerpt. (AC13 present-path.) *Note:* AC5's present-path single-unconfirmed-
  source-lowered-confidence sub-clause is verified by **T1 read** (the reference
  states it), not by this behavioural QA — a single-source-staleness branch is
  impractical to trigger in a described simulation.
- *(manual QA, surface-absent)* With no retrieval surface, run the same prompt;
  **invariants:** AC5 clause (a) — an explicit ask for the missing domain/
  in-flight context plus a lowered-confidence marker routed into the intent's
  `Assumptions`; AC5 clause (b) — no fabricated domain/in-flight fact. Record a
  per-clause pass/fail. (AC13 absent-path.)
- *(manual QA, sensitive-surface-present)* With the sensitive mock exposed, run
  the same prompt; **invariant:** AC5 clause (c) — the skill asks before quoting
  the do-not-quote content. Record pass/fail.
- *(manual QA, brownfield-with-surface)* With `Maturity: brownfield` and the
  landscape mock exposed, run the prompt; **invariant:** the current-state-inputs
  maturity gate routes to the current-landscape area and the intent accounts for
  the existing system. Record pass/fail. (AC13 brownfield-path.)

**Approach:**
- Install the product-engineering pack into a throwaway/temp scope (per owner
  guidance), or run the projected artifacts directly.
- Run all scenarios with the fixed driver; capture observable behaviour.
- Clean up the temp install afterwards.

**Done when:** the present-path invariant holds; AC5 clauses (a), (b), (c) each
record a pass; the brownfield-path passes; observations recorded against AC13;
temp install removed.

**Results (recorded 2026-06-13).**
- *Structural (real):* `make build` projects the change to both routes (`apm`,
  `claude-plugins`); the projected `frame-intent/SKILL.md` carries step 2 and the
  projected `references/knowledge-surfaces.md` is **byte-identical to source** on
  both routes, with exactly the four area rows and no hardcoded tool name. This
  is what an adopter install delivers. **PASS.**
- *Behavioural (independent agent executing step 2 against the fixed driver; the
  harness can't inject a real mock MCP tool, so tool presence was described per
  scenario — a simulation of the decision logic, not a live MCP detection):*
  - **S1 present (greenfield):** loaded the reference, consulted areas 1 & 8, the
    opportunity used the org's meaning of "refund" (credit-note reversal) and the
    Assumptions flagged the in-flight Atlas refunds API; surface named. **PASS.**
  - **S2 absent:** did not load the reference; asked for the missing domain/
    in-flight context, recorded a lowered-confidence marker in `Assumptions`,
    fabricated nothing, named the surface "none detected". **PASS.**
  - **S3 sensitive:** cited that the memo exists and asked before quoting; no
    verbatim reproduction. **PASS.**
  - **S4 brownfield-with-surface:** the maturity gate routed to the
    current-landscape area; the intent accounted for the existing `CreditNote`
    service / refunds ledger rather than recall. **PASS.**
- *Findings folded back in:* the independent run flagged that the internal-only
  rail lived only in the reference (which loads *after* detection, so a public
  web tool could be mis-claimed as a surface pre-load) and that the named-surface
  had no home field. Both fixed in this PR — the SKILL.md step now carries the
  internal-only exclusion inline and pins the surface name (and the
  lowered-confidence marker) to the intent's `Assumptions`.
- *Deferred (unchanged):* a true temp-install-with-live-mock run remains the
  existing `live-mock-mcp-detection-qa` backlog item (now enumerating both
  skills).

### T6: Quality-engineer follow-ups (owner-requested, post-review)

**Depends on:** T1, T2, T3

**Touches:** tools/lint-knowledge-surface-parity.py, tools/test-lint-knowledge-surface-parity.py, tools/pre-pr-catalogue.py, packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md (audit-home line; #300 already relocated it to assets/), packs/product-engineering/.apm/skills/frame-intent/SKILL.md, packs/architect/.apm/skills/architect-design/assets/concept.md, packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:**
- `python3 tools/lint-knowledge-surface-parity.py` exits 0 on the real repo
  (all copies in parity); `python3 tools/test-lint-knowledge-surface-parity.py`
  exits 0 (8 fixture cases: parity passes; reworded pe question, renamed canonical
  area, subset drift, canonical-incomplete, missing-file, a reworded
  architect-review copy, and an out-of-canon area each fail) — AC14.
- Both are invoked by `tools/pre-pr-catalogue.py` (the `make build-check`
  aggregator); a `grep` confirms the two `_run(...)` lines — AC14.
- The intent template's `## Assumptions` carries the optional `Knowledge surface:`
  line; architect `concept.md` carries the symmetric optional section; architect
  `[pack]` version is `0.4.2` in pack.toml + plugin.json; `marketplace.json` shows
  architect `0.4.2` — AC15.

**Approach:**
- Author the parity lint (stdlib, fixture-mode env overrides
  `KS_CANONICAL_FILE`/`KS_REVIEW_FILE`/`KS_PE_FILE`) + its paired self-test,
  mirroring the `lint-knowledge.py` / `test-lint-credentialed-skills.py`
  convention; cover every copy of the core (canonical `architect-design`, plus
  `architect-review` and `frame-intent`); wire both into `pre-pr-catalogue.py`.
- Add the `Knowledge surface:` audit-home line to the intent template (at its
  `assets/` home, which #300 produced) and the symmetric optional section to
  architect's concept asset; bump architect `0.4.1 → 0.4.2` (asset change) +
  changelog; `make build-self` to refresh `marketplace.json`.
- The template relocation (`seeds/` → skill `assets/`) was done upstream by #300
  (enriched-pack-manifest), which removed `seeds/` entirely; this PR pins the
  audit-home line on #300's asset rather than performing the move.

**Done when:** the lint + self-test are green and wired into build-check, both
audit homes are pinned, architect 0.4.2 is reflected in marketplace.json, and the
intent template projects from the skill's `assets/` (byte-identical to source).

## Rollout

Pure content + version bump. No infra, no flag, no migration. Reversible by
reverting the PR. The only external-facing effect is the `marketplace.json`
version advertised to adopters; nothing must ship in sequence. Coordination
note: the pack base advanced under this branch — #298 shipped value-stream
(`0.1.0 → 0.2.0`), then #300 (enriched-pack-manifest) patch-bumped to `0.2.1` and
enriched `pack.toml`; this spec was authored against 0.1.0 and rebased forward,
so the bump is now `0.2.1 → 0.3.0` (target unchanged across the rebases).
Architect, touched only for the symmetric concept-pin, goes `0.4.1 → 0.4.2`. The
now-Shipped `value-stream-meta-repo` and `enriched-pack-manifest` work is left
untouched (spec Boundary).

## Risks

- **Wording drifts toward prescriptive/always-on**, taxing every framing run —
  mitigated by the progressive-disclosure gate (T1/T2) and the QA (T5) checking
  the surface-absent path stays cheap.
- **Lens leak** — a solution-design area (3/5/6/7) creeps into the reference,
  drifting product-engineering into the architect's space — caught by the T1
  grep + the T4 diff inspection.
- **Accidental tool-name leak** into the reference makes it non-agnostic —
  caught by the T1 grep test.
- **build-self churns unrelated packs** in marketplace.json — caught by the T4
  diff inspection (version-only assertion).

## Changelog

- 2026-06-13: initial plan.
- 2026-06-13: executed T1–T5; all gates green; QA recorded under T5. Rebased onto #298 (value-stream-meta-repo shipped 0.2.0) mid-flight; version base 0.1.0→0.2.0, target 0.3.0 unchanged; marketplace regenerated; spec/plan/README version-base references corrected.
- 2026-06-13: T6 (owner-requested post-review) — built the knowledge-surface parity lint + self-test (guards all copies: `architect-design` canonical, `architect-review`, `frame-intent`), wired into build-check; pinned the detection audit home in both the intent template and architect's concept asset (architect 0.4.1→0.4.2) (AC14–16).
- 2026-06-13: rebased again onto #299 (architect-review knowledge surfaces, architect 0.4.0) then #300 (enriched-pack-manifest, pack.toml rich metadata + adapter-contract 0.14; pe→0.2.1, architect→0.4.1; templates relocated `seeds/`→`assets/`). Re-derived versions (pe 0.2.1→0.3.0, architect 0.4.1→0.4.2), generalized the parity lint to a third copy (`architect-review`), dropped the now-redundant manual template move (#300 did it), and reconciled backlog/changelog/specs-README against the shipped architect-review + enriched-manifest entries.
