# Plan: doc-drift-prevention

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is almost entirely **documentation/convention content** plus one new
catalogue-only Python lint and one small self-host machinery edit. The shape:
pin the contract once (CONVENTIONS seed), then make the three construction/
judgment surfaces (template, reviewer, work-loop) reference that single source;
give deferred work a durable home (seed `backlog.md`, preserve the curated
instance); then add the mechanical gate where it can run (a stdlib lint wired
into `make build-check`, never the projected pre-pr hook). Finally normalize the
live corpus so the gate passes, record the decision in an ADR, and re-project.

Order of operations matters: the contract (T1) is the source the other surfaces
quote, so it lands first. The lint (T6) encodes the same invariants mechanically,
so it depends on both the pinned vocab (T1) and the backlog anchor target (T5).
The riskiest part is the self-host `EXCLUDED_PATTERNS` edit (T5): get the
preserve-on-disk predicate wrong and `make build-self` clobbers the curated
`docs/backlog.md`. That task carries a real unit test against `_project_seeds`.
Re-projection (T10) is last so the projected `.claude/*` copies match source.

## Constraints

- **RFC-0016** (Accepted 2026-05-29) — the five mechanisms, the catalogue-only
  lint, the `ROADMAP.md`→`backlog.md` register, and the open-question defaults
  (copilot = follow-up, inline `(deferred: <anchor>)` token, invariant (iii)
  doc-refs-only) all come from it.
- **RFC-0002** (self-hosting seed contract) — pack seeds are placeholder
  templates; `_project_seeds` preserves Manual on-disk instances. The backlog
  seed must obey the placeholder/blocklist rules in `tools/lint-seeds.py`.
- **CONVENTIONS § 3** — these convention edits are RFC-0016's authorized
  follow-ons; they ride in this implementing PR.

## Construction tests

**Integration tests:** after T1–T5 and T10, `make build-check` runs clean
(projection matches source, all artifact lints pass) — the cross-cutting proof
that the pack edits projected correctly and nothing drifted.
**Manual verification:** none — every task has an automatable goal-based or TDD
check below.

## Tasks

### T1: CONVENTIONS seed pins the doc-drift contract

**Depends on:** none

**Tests:**
- Goal-based (AC5): `grep` `packs/core/seeds/docs/CONVENTIONS.md` § 4 for all of:
  the status vocabulary `Draft | Approved | Implementing | Shipped | Archived`,
  the `(deferred: <anchor>)` token, the `- [ ]`/`- [x]` AC notation, and the
  one-line *metadata-only* note naming semantic drift as adversarial-reviewer
  #5's job.

**Approach:**
- In `packs/core/seeds/docs/CONVENTIONS.md` § 4 (Specs and Plans), add a short
  subsection — "Spec metadata contract" — pinning the four items above.
- Keep it tight (a few lines); it is the single source the template, reviewer,
  and work-loop quote. State explicitly that it is metadata-only.

**Done when:** the grep finds all four pinned items in the seed source.

### T2: new-spec template carries the deferral hatch

**Depends on:** T1

**Tests:**
- Goal-based (AC1): `grep` `packs/core/.apm/skills/new-spec/assets/spec.md` for
  the `(deferred: <anchor>)` convention in the Acceptance-Criteria region, and
  confirm the status comment line is unchanged.

**Approach:**
- In the Acceptance Criteria comment block of the template, add a one-line note:
  a deferred criterion is written `- [ ] <outcome> (deferred: <backlog-anchor>)`
  and points into `docs/backlog.md`.
- Do not alter the status comment (already canonical).

**Done when:** the grep finds the deferral note in the template source.

### T3: adversarial-reviewer "Spec drift" check is named, not vague

**Depends on:** T1

**Tests:**
- Goal-based (AC2): `grep` `packs/core/.apm/agents/adversarial-reviewer.md`
  implementation-stage check #5 for the four named sub-checks (status flip, AC
  `[x]`-or-`(deferred:)`, deferred-in-register, intra-repo refs resolve).

**Approach:**
- Replace the one-sentence "Spec drift" check #5 with a named enumeration of the
  four invariants from RFC-0016 mechanism 2. Keep it concrete and few — name the
  checks, cite the register, do not bloat.

**Done when:** the grep finds the four sub-checks under check #5.

### T4: work-loop § GATES names the lint; § DECIDE points to the register

**Depends on:** T1

**Tests:**
- Goal-based (AC3): `grep` `packs/core/.apm/skills/work-loop/SKILL.md` § GATES
  for `lint-spec-status.py` described as catalogue-governance (does not project).
- Goal-based (AC4): `grep` the § DECIDE "Deferred items" bullet — the new wording
  routes deferrals into `docs/backlog.md` by anchor with a one-line PR pointer;
  assert the phrase "the PR is the durable record" is **gone**; the end-of-session
  checklist references the four drift invariants.

**Approach:**
- § GATES: add a line noting the catalogue-only `tools/lint-spec-status.py` runs
  in `make build-check` (not in adopter trees).
- § DECIDE: rewrite the "Deferred items" bullet — register-not-PR; PR keeps a
  pointer. Add the four drift invariants to the end-of-session checklist.

**Done when:** both greps pass and the old "durable record" phrasing is absent.

### T5: seed `backlog.md` and preserve the curated instance on self-host

**Depends on:** T1

**Tests:**
- TDD (AC7): a unit test asserting `_project_seeds` does **not** overwrite an
  existing on-disk `docs/backlog.md` when the path is excluded, but **does** write
  the placeholder seed when the file is absent. Lives next to existing self-host
  tests (`packages/agentbundle/agentbundle/build/tests/test_self_host_check.py`
  or a new sibling).
- Goal-based (AC6): `python tools/lint-seeds.py` exits 0 with the new seed present.

**Approach:**
- Create `packs/core/seeds/docs/backlog.md` as a placeholder (no blocklisted
  catalogue strings; documents that `(deferred: <anchor>)` markers resolve to
  anchors here). Model on `packs/core/seeds/docs/product/roadmap.md`. The seed
  contains the literal placeholder token `<!-- no deferred items yet -->`, which
  the curated in-tree `docs/backlog.md` does **not** contain (verified: the
  curated file lists real open items) — so the placeholder/instance distinction
  is unambiguous.
- Add `"docs/backlog.md"` to `EXCLUDED_PATTERNS` in
  `packages/agentbundle/agentbundle/build/self_host.py`.
- Add `"docs/backlog.md": ("<!-- no deferred items yet -->",)` to
  `REQUIRED_PLACEHOLDERS` in `tools/lint-seeds.py`.

**Done when:** the preserve unit test is green, `lint-seeds.py` exits 0, and
`make build-self` leaves the curated `docs/backlog.md` byte-identical.

### T6: Tier-1 lint enforces the four spec-metadata invariants

**Depends on:** T1, T5

**Tests:**
- TDD (AC9/AC11): `tools/test-lint-spec-status.py` spawns `tools/lint-spec-status.py`
  as a subprocess against fixture spec trees and asserts:
  - clean fixture → exit 0;
  - **invariant (i)** out-of-vocab leading token (`Drafting`) → exit non-zero;
  - **invariant (i) lenient parse**: an annotated `Shipped (2026-05-26)` and an
    `Approved → Shipped (…)` status → exit 0 (leading token is in-vocab);
  - **invariant (ii)** a spec whose header Status *changes to* `Shipped` in the
    diff with an unchecked, non-deferred AC → exit non-zero;
  - **invariant (ii) grandfather**: a spec already `Shipped` on the base with
    unchecked ACs → exit 0;
  - **invariant (ii) no-base**: when no base ref resolves, invariant (ii) is
    skipped (warning, exit 0 for that invariant);
  - **invariant (iv)** `(deferred: <missing-anchor>)` with no matching
    `backlog.md` heading → exit non-zero;
  - **invariant (iii)** a dangling intra-repo doc ref → reported, does **not**
    fail the run (warn-only).

**Approach:**
- Write `tools/lint-spec-status.py` as a standalone stdlib script mirroring the
  shape of `tools/lint-seeds.py` (repo-root discovery, exit 0/1, readable
  diagnostics).
- **Invariant (i):** read each spec's header `- **Status:**` line, extract the
  leading token (first word after `Status:`, truncated at the first ` (`, ` →`,
  or `<!--`), match against the frozenset `{Draft, Approved, Implementing,
  Shipped, Archived}` (prior art: PEP `check-peps.py` `_validate_status`).
- **Invariant (ii):** diff against `origin/<default-branch>` (resolve the
  default branch via `git symbolic-ref` / fall back to `main`). Detect a spec
  whose header Status token changed *to* `Shipped`; grandfather specs already
  `Shipped` on the base. If the base ref does not resolve, emit a warning and
  skip the invariant — never fail.
- **Invariant (iv):** resolve `(deferred: <anchor>)` against `docs/backlog.md`
  heading anchors (GitHub slug rules: lowercase, spaces→`-`, strip punctuation).
- **Invariant (iii):** warn-only; doc-refs only (code paths deferred to v1.1).

**Done when:** `python tools/test-lint-spec-status.py` is green across all
invariant cases above.

### T7: wire the lint into `make build-check` (catalogue-only)

**Depends on:** T6

**Tests:**
- Goal-based (AC10): `grep` the `Makefile` `build-check` target invokes
  `tools/lint-spec-status.py` (and its self-test); `grep` confirms
  `packs/core/.apm/hooks/pre-pr.py` does **not** reference it.

**Approach:**
- Add `$(PYTHON) tools/lint-spec-status.py` and
  `$(PYTHON) tools/test-lint-spec-status.py` to the Makefile `build-check` target.

**Done when:** both greps pass; `make build-check` runs the lint.

### T8: normalize the live spec corpus so the lint passes

**Depends on:** T6

**Tests:**
- Goal-based (AC11): `python tools/lint-spec-status.py` over this repo exits 0.

**Approach:**
- Run the lint; the one expected live true positive is
  `docs/specs/lint-packs-target-vocab/spec.md` carrying `Status: Drafting` (an
  out-of-vocab *spec* status). Normalize it to `Draft`.
- `wire-session-start-hook` (Shipped, 0/11 ACs checked) is **Frozen and
  grandfathered** by invariant (ii) — do **not** edit it.
- Do **not** retro-edit any Frozen spec body (Boundary). If the lint surfaces a
  Frozen-only violation, that is a lint bug (parse/grandfather), not a corpus fix.

**Done when:** `python tools/lint-spec-status.py` exits 0 over the live corpus
with the single `lint-packs-target-vocab` status fix and no Frozen-body edits.

### T9: ADR records the construction+judgment decision

**Depends on:** none

**Tests:**
- Goal-based (AC12): the new ADR file exists, status `Accepted`, cites RFC-0016,
  and states the construction-for-adopters / mechanical-gate-as-catalogue-
  governance decision. Authored via the `new-adr` skill.

**Approach:**
- Use `new-adr` to create `docs/adr/NNNN-doc-drift-construction-and-judgment.md`
  with the decision, context (the delivery complication), and consequences.

**Done when:** the ADR exists and the goal-based grep finds the decision + RFC ref.

### T10: re-project and update the open-work indexes

**Depends on:** T2, T3, T4, T5

**Tests:**
- Integration (AC1–AC5 projection): `make build-check` exits clean — projected
  `.claude/skills/new-spec/assets/spec.md`, `.claude/agents/adversarial-reviewer.md`,
  `.claude/skills/work-loop/SKILL.md`, and `docs/CONVENTIONS.md` match source.

**Approach:**
- Run `make build-self` to refresh projected paths from the T1–T5 source edits.
- Add `doc-drift-prevention` to the **on-disk Manual instance**
  `docs/specs/README.md` active list — *not* the pack seed
  `packs/core/seeds/docs/specs/README.md`, which stays the `<!-- no specs yet -->`
  placeholder.
- Add this spec's open items to the curated in-tree `docs/backlog.md` if any AC
  defers.

**Done when:** `make build-check` is clean and the spec appears in
`docs/specs/README.md`.

## Rollout

Big-bang within this catalogue, fully reversible (all edits are doc/convention
content plus one additive lint and one additive `EXCLUDED_PATTERNS` entry). No
adopter-facing runtime change ships — adopters receive only projected content
(template, reviewer, work-loop, CONVENTIONS, backlog seed) on their next install.

## Risks

- **`EXCLUDED_PATTERNS` edit clobbers the curated backlog.** Mitigated by the T5
  preserve unit test and a `make build-self` dry-run check before committing.
- **Diff-triggered invariant (ii) misfires on the merge base.** Mitigated by
  grandfathering specs already `Shipped` on the base and testing the transition
  case explicitly in T6.
- **Tier-1 lint flags Frozen-corpus noise.** Mitigated by the grandfather rule;
  T8 fixes only live true positives.

## Changelog

- 2026-05-29: initial plan (RFC-0016 implementation).
