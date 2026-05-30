# Spec: doc-drift-prevention

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0016

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

We keep shipping specs whose docs have drifted from reality — a `Shipped` spec
with unchecked acceptance criteria, an out-of-vocabulary status, a deferral that
evaporated into a stale PR comment. The work-loop replaced "feel" with mechanical
gates everywhere *except* docs, where the only controls are an honor-system
principle and a judgmental reviewer. RFC-0016 resolves this by routing prevention
to the surfaces that actually reach adopters — **construction** (a canonical-by-
birth spec template, a pinned contract) and **judgment** (sharpened reviewer +
work-loop checklists) — while keeping a hard **mechanical gate only where it can
run: inside this catalogue** (Python + CI both present, neither guaranteed in a
polyglot adopter tree).

Success for the **catalogue maintainer** (the primary user): authoring a spec
stamps the canonical status vocabulary, checkbox AC notation, and the
`(deferred: <anchor>)` deferral hatch from birth; the adversarial-reviewer and
work-loop name the four drift invariants as concrete checks; deferred work has a
durable, version-controlled home (`docs/backlog.md`) instead of a PR comment that
rots; and `tools/lint-spec-status.py` mechanically fails our CI when a spec's
metadata drifts. Success for the **adopter**: the template, the reviewer/work-loop
checklists, the pinned CONVENTIONS contract, and a seeded `backlog.md` all project
to their tree on every adapter — no Python or CI runtime assumed.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit pack **source** under `packs/<pack>/.apm/...` or `packs/<pack>/seeds/...`,
  then run `make build-self` to refresh projected paths (`.claude/`, `AGENTS.md`,
  `docs/CONVENTIONS.md`, …). Never edit a projected copy directly.
- Keep the new-spec template, the sharpened reviewer/work-loop checklists, and
  the pinned CONVENTIONS contract mutually consistent **in this same PR** — a
  template change that isn't reflected in CONVENTIONS is itself drift.
- Treat the canonical status vocabulary as exactly
  `Draft | Approved | Implementing | Shipped | Archived` — the set already in the
  new-spec `assets/spec.md` status comment.

### Ask first

- Reclassifying any path in `EXCLUDED_PATTERNS` other than adding
  `docs/backlog.md` (the one addition this spec authorizes). Touching the
  self-host source-of-truth split beyond that needs sign-off.
- Extending the Tier-1 lint's invariant (iii) (dangling intra-repo references)
  from doc-refs to code paths — RFC-0016 defers this to v1.1.
- Flipping copilot's `agent` projection from `dropped` to enabled to extend the
  sharpened reviewer to 4/4 adapters — RFC-0016 defers this to a separate follow-up.

### Never do

- **Add `tools/lint-spec-status.py` (or any catalogue linter) to the projected
  `tools/hooks/pre-pr.py`.** That hook projects to adopters via
  `packs/core/.apm/hooks/pre-pr.py`; wiring a catalogue-only linter there would
  make an adopter's pre-PR hook call a script absent from their tree. The lint
  is invoked from the **Makefile `build-check` target only**.
- **Add a pack `packs/` source for `tools/lint-spec-status.py`.** Linters are
  catalogue-internal; they do not project. No `seeds/` entry, no `.apm/` entry.
- **Introduce a new top-level directory, a new runtime dependency, or a new
  module boundary.** The lint is a standalone stdlib Python script alongside the
  existing `tools/lint-*.py`; it shares their shape, adds no framework.
- **Retro-edit the bodies of Frozen specs** (shipped `specs/*`, accepted
  `rfc/*`, `adr/*`) to satisfy the lint. Invariant (ii) is diff-triggered and
  grandfathers the completed corpus; only out-of-vocabulary *status fields* on
  live specs are normalized.
- **Ship a fail-closed doc-drift gate to adopters.** Prevention for adopters is
  construction + judgment only; the hard gate is catalogue governance.

## Testing Strategy

Most of this spec is documentation and convention content; its verification is
predominantly **goal-based checks** (grep/build/typecheck one-liners), with the
Tier-1 lint and the backlog-preserve behavior carrying real **TDD** invariants.

- **Construction content (mechanisms 1–5: template, reviewer, work-loop,
  CONVENTIONS seed, backlog seed prose) — goal-based.** Each is a documentation
  edit; the verification is a `grep` proving the required tokens/phrases are
  present in the pack **source**, plus `make build-self` followed by a drift-clean
  `make build-check` proving the projection landed. A test that re-asserts prose
  word-for-word would be a brittle mirror, not a contract — so goal-based is the
  right mode.
- **Backlog seed preservation (AC7) — TDD.** "`make build-self` must not clobber
  a curated on-disk `docs/backlog.md`" is a compressible invariant with a clear
  failure mode; it gets a unit test against `_project_seeds`' preserve gate.
- **Tier-1 lint (AC9, AC11) — TDD.** The four invariants are pure functions over
  spec text; each gets red-green construction tests (valid corpus passes; a
  crafted out-of-vocab status, an unchecked-AC ship transition, a dangling
  `(deferred:)` anchor each fail). The lint must also pass clean against the live
  corpus after normalization (goal-based: run it, exit 0).
- **Lint wiring (AC10) — goal-based.** `grep` that `build-check` invokes the lint
  and that `pre-pr.py` does **not**.
- **Governance (ADR, RFC status) — goal-based.** The artifact exists with the
  required decision recorded.

## Acceptance Criteria

<!-- A deferred criterion uses: - [ ] <outcome> (deferred: <backlog-anchor>) -->

- [x] **AC1 — new-spec template carries the deferral hatch.**
  `packs/core/.apm/skills/new-spec/assets/spec.md` documents the
  `(deferred: <anchor>)` convention in its Acceptance-Criteria region and retains
  the canonical status comment; the projected copy matches after `make build-self`.
- [x] **AC2 — adversarial-reviewer drift check is named, not vague.** The "Spec
  drift" implementation-stage check in
  `packs/core/.apm/agents/adversarial-reviewer.md` enumerates the four invariants:
  (a) status flipped to match the change, (b) every AC `[x]` or carrying
  `(deferred: <anchor>)`, (c) deferred items recorded in the register, (d)
  intra-repo references resolve.
- [x] **AC3 — work-loop § GATES names the catalogue lint.**
  `packs/core/.apm/skills/work-loop/SKILL.md` § GATES references
  `tools/lint-spec-status.py`, framed explicitly as *catalogue governance*: this
  catalogue additionally gates spec metadata via that lint in CI, while adopters
  rely on the reviewer + work-loop drift checks (the lint does not ship to their
  tree). The framing must make clear an adopter has no such file — so the
  adopter-facing projected skill does not send readers chasing a missing script.
- [x] **AC4 — work-loop deferral rule points to the register, not the PR.** The
  § DECIDE "Deferred items" bullet is replaced: deferred work is recorded in
  `docs/backlog.md` by anchor and the PR description keeps a one-line *pointer*;
  the "PR is the durable record" wording is gone. The end-of-session checklist
  references the four drift invariants.
- [x] **AC5 — CONVENTIONS seed pins the contract.**
  `packs/core/seeds/docs/CONVENTIONS.md` § 4 pins: the canonical status
  vocabulary, the `- [ ]` / `- [x]` AC notation, the `(deferred: <anchor>)`
  token, and a one-line note that this contract is *metadata-only* — semantic
  spec↔code drift remains adversarial-reviewer #5's job.
- [x] **AC6 — backlog seed exists and is lint-clean.**
  `packs/core/seeds/docs/backlog.md` is a placeholder seed that passes
  `tools/lint-seeds.py` (registered in `REQUIRED_PLACEHOLDERS`, no blocklisted
  catalogue strings) and documents that `(deferred: <anchor>)` markers resolve to
  anchors here.
- [x] **AC7 — self-host preserves the curated backlog.** `docs/backlog.md`
  already exists in-tree (renamed from `ROADMAP.md` in commit `8888fa3`); this PR
  adds only the `EXCLUDED_PATTERNS` entry and the placeholder seed that protect
  it. With the path excluded, `make build-self` against this repo leaves the
  curated `docs/backlog.md` byte-identical (the placeholder seed lands only on a
  tree that lacks the file). A unit test pins both branches of the preserve gate.
- [x] **AC8 — the deferral convention is end-to-end.** The
  `(deferred: <anchor>)` token introduced in the template (AC1), pinned in
  CONVENTIONS (AC5), checked by the reviewer (AC2) and work-loop (AC4), and
  validated by the lint (AC9-iv) all name the same `docs/backlog.md` anchor target.
- [x] **AC9 — Tier-1 lint enforces the four invariants.**
  `tools/lint-spec-status.py` checks each `docs/specs/*/spec.md` (the header
  `- **Status:**` field only; `plan.md` status is out of v1 scope):
  - **(i) status vocabulary.** The lint extracts the **leading status token** —
    the first whitespace-delimited word after `Status:`, stopping at the first
    ` (`, ` →`, or `<!--` — and matches *that* against the canonical frozenset
    `{Draft, Approved, Implementing, Shipped, Archived}`. This passes Frozen
    annotated statuses like `Shipped (2026-05-26)` and `Approved → Shipped (…)`
    (leading token `Shipped`/`Approved`) while still flagging a true out-of-vocab
    token such as `Drafting`. Hard invariant (exit non-zero).
  - **(ii) ACs at the ship transition** (diff-triggered). Diff against
    `origin/<default-branch>` (this repo's `main`); a spec whose header Status
    *changes to* `Shipped` in the diff must have every AC `[x]` or carrying
    `(deferred: <anchor>)`. Specs already `Shipped` on the base are grandfathered.
    **If no base ref is resolvable** (shallow clone, detached HEAD), invariant
    (ii) is skipped with a warning and never fails. Hard invariant when it runs.
  - **(iii) dangling intra-repo doc references** — reported **warn-only** (never
    exit non-zero); doc-refs only in v1 (code paths deferred to v1.1 per RFC-0016).
  - **(iv) deferral anchors resolve.** Every `(deferred: <anchor>)` in a spec
    resolves to a heading anchor in `docs/backlog.md` (GitHub slug rules). Hard
    invariant (exit non-zero).
- [x] **AC10 — lint is catalogue-only.** `tools/lint-spec-status.py` is invoked
  from the Makefile `build-check` target and is **absent** from
  `packs/core/.apm/hooks/pre-pr.py` (and its projection `tools/hooks/pre-pr.py`).
- [x] **AC11 — lint passes the live corpus.** After normalization, running
  `python tools/lint-spec-status.py` over this repo exits 0; a construction
  self-test exercises each invariant red-and-green.
- [x] **AC12 — ADR records the decision.** An ADR records "doc drift — prevented
  by construction + judgment for adopters; mechanically gated only as catalogue
  governance," citing RFC-0016.
- [x] **AC13 — RFC-0016 is Accepted.** `docs/rfc/0016-doc-drift-mechanical-gate.md`
  status is `Accepted` with a closed date.

## Assumptions

- Technical: pack source → projection; edit `packs/**` then `make build-self`;
  self-host projects core + governance-extras + user-guide-diataxis
  (source: `packages/agentbundle/agentbundle/build/self_host.py` SELF_HOST_PACKS).
- Technical: `tools/hooks/pre-pr.py` is itself projected from
  `packs/core/.apm/hooks/pre-pr.py`, so the catalogue lint must be wired into the
  Makefile `build-check` target, never the hook (source:
  `packs/core/.apm/hooks/pre-pr.py`; `Makefile` build-check target).
- Technical: seeding `docs/backlog.md` requires both an `EXCLUDED_PATTERNS` entry
  (preserve-on-disk gate) and a `REQUIRED_PLACEHOLDERS` entry; mirrors the
  `docs/product/*.md` Manual-seed pattern (source: `self_host.py:_project_seeds`
  lines 479-487 + `EXCLUDED_PATTERNS`; `tools/lint-seeds.py:REQUIRED_PLACEHOLDERS`).
- Technical: canonical spec status vocabulary is
  `Draft | Approved | Implementing | Shipped | Archived` (source:
  `packs/core/.apm/skills/new-spec/assets/spec.md:3`).
- Process: RFC-0016 (Accepted 2026-05-29) authorizes the CONVENTIONS/template/seed
  changes as its named follow-ons; convention changes are otherwise RFC-gated
  (source: `docs/CONVENTIONS.md` § 3; RFC-0016 § Follow-on artifacts).
- Product: all five mechanisms + the Tier-1 lint ship in v1; open questions
  resolve to RFC defaults — copilot agent enablement is a separate follow-up,
  the token is the inline `(deferred: <anchor>)`, and invariant (iii) is
  doc-refs-only in v1 (source: RFC-0016 § Decisions requested, § Open questions).
- Process: the lint covers `spec.md` Status only in v1; `plan.md` status
  vocabulary (`Drafting | Executing | Done`) is intentionally out of v1 scope.
  The one live out-of-vocab *spec* status — `lint-packs-target-vocab` carrying
  `Status: Drafting` — is the falsifiable "≥1 live true-positive" the RFC names,
  and is normalized by T8 (source: `docs/specs/lint-packs-target-vocab/spec.md:3`).
- Process: the pre-existing RFC-0016 deferral in `docs/backlog.md` — stale `[x]`
  doc-surface ACs on the Frozen `skill-secrets` (AC32) and
  `credential-broker-contract` (AC42) specs after the `ROADMAP.md`→`backlog.md`
  rename — **stays deferred**; fixing it would edit Frozen spec bodies, which the
  `Never do` Boundary forbids (source: `docs/backlog.md` § Cross-spec).

## Changelog

- **2026-05-29 erratum (lint-work-loop-delivery / RFC-0016 erratum, Approver:
  eugenelim):** two `Never do` Boundaries here — "Add a pack `packs/` source for
  `tools/lint-spec-status.py` … No `seeds/` entry, no `.apm/` entry" and the
  framing that the lint is catalogue-only — are **superseded**. RFC-0016's
  erratum corrected its "linters don't project" premise: the lint now ships to
  adopters as a `work-loop` skill script at
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` (agent-invoked,
  not fail-closed), while the catalogue still runs it as a fail-closed CI gate
  via `make build-check`. The other `Never do` Boundary — never wire the lint
  into the *projected* `pre-pr.py` — **still holds** (pre-pr is a hook body that
  would mis-fire; the lint is invoked from the work-loop skill's finish-time
  checklist instead). AC9/AC10/AC11 bodies are unchanged (this spec is Frozen);
  the lint's new home and the code-reference invariant (iii) extension are
  specified in `docs/specs/spec-code-ref-lint/` and
  `docs/specs/lint-work-loop-delivery/`.
