# Spec: adopter-clean-enforcement-gate

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0015 (owns `lint-plan-deps.py` — not touched here), RFC-0013 (owns `add-credentialed-skill` — not touched here), RFC-0002 (self-host projection)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Shipped `core` primitives must not reference catalogue-internal tooling or break
on arrival in an adopter's repo — the hook/command analogue of issue #190's seed
bug. Today the shipped `pre-pr.py` **hard-crashes** an adopter (it shells out to
**8** repo-native checks that never install — 7 linters `lint-agents-md`,
`lint-agent-artifacts`, `lint-skill-spec`, `lint-knowledge`, `lint-build`,
`lint-seeds`, `lint_credentialed_skills` (underscore) plus a
`test-lint-credentialed-skills` self-test), the `new-spec`
`plan.md` template name-drops a repo-native `tools/lint-plan-deps.py`,
`session-start.py` hints at a repo-native linter, `max_iterations` is
double-sourced, and the shipped `CONVENTIONS.md` § Enforcement / repo `README.md`
describe a catalogue-internal CI gate as if it were the adopter's.

The unifying principle (recorded in `AGENTS.local.md`, not RFC-gated):
**adopter-facing materials ship; this repo's own projection artifacts and
repo-specific tooling stay local-only.** None of those catalogue checks are
adopter-generic — they enforce *this catalogue's* conventions on *this
catalogue's* artifacts — so the shipped enforcement gate ships **zero** of them.

Success: a fresh `core` install's `pre-pr.py` runs without crashing — it runs
only the genuinely-adopter-relevant `loop-cohort.py check` (the work-loop caps
gate, which ships) plus a commented "wire your own lint/test here" stub, and
degrades gracefully when nothing is present. This repo's full enforcement (the 8
catalogue checks) moves to a catalogue-only hook that never projects. The
template/hint/docs stop pointing adopters at repo-native paths, and
`max_iterations` gets one source of truth.

## Boundaries

### Always do

- Shipped primitives (anything under a pack's `.apm/` that projects to an adopter)
  reference **only** shipped/adopter-relevant tooling — never a repo-native
  `tools/lint-*` path.
- Keep catalogue-internal tooling (the 8 catalogue checks, the new catalogue-only
  hook) **repo-native and local-only** — it must never project to an adopter.
- Degrade gracefully: a shipped hook that finds nothing to run exits 0 with a
  notice, never a hard failure.
- Keep self-host projection consistent — run `make build-self` after editing any
  pack source so `make build-check` stays green.
- Record the deferred, other-spec-owned items as `docs/backlog.md` follow-ups.

### Ask first

- Any change to what `loop-cohort.py check` *does* (its caps semantics).
- Touching `add-credentialed-skill` / `example-credentialed-skill` (owned by
  RFC-0013's in-flight `credential-broker-contract` spec).
- Touching `lint-plan-deps.py` itself (owned by RFC-0015's `wave-scheduled-supervisor`).

### Never do

- **No new top-level directory and no new runtime dependency.**
- Never make the shipped `pre-pr.py` reference, or ship, any of the 8 catalogue
  checks (incl. the underscore `lint_credentialed_skills.py` and the
  `test-lint-credentialed-skills.py` self-test).
- Never delete or relocate another spec's owned primitive (`lint-plan-deps.py`,
  `add-credentialed-skill`, `example-credentialed-skill`) in this PR — route to
  the owning spec instead.
- Never codify the adopter-facing/local-only convention in `docs/CONVENTIONS.md`
  (that's RFC-gated) — it lands in `AGENTS.local.md`.

## Testing Strategy

- **B1 `pre-pr.py` adopter-clean + graceful** — **TDD.** The shipped `pre-pr.py`
  source matches none of `tools/lint[-_]` / `test-lint-credentialed-skills`; run it in an adopter-shaped tree
  (no catalogue linters; with and without an active `state.json`) and assert exit
  0 — it runs `loop-cohort check` when a spec state exists and skips gracefully
  otherwise, never crashing.
- **B2 catalogue-only hook** — **goal-based.** `make pre-pr` (→ the catalogue-only
  hook) runs the 8 catalogue checks (7 linters + the `test-lint-credentialed-skills`
  self-test) + delegates to the shipped `pre-pr.py`; this repo's gate
  (`make build-check` / CI) stays green.
- **B3 plan template** — **goal-based.** The shipped `new-spec` `plan.md` template
  references `loop-cohort.py schedule` and contains no `tools/lint-plan-deps.py`.
- **B4 session-start hint** — **goal-based.** `session-start.py` contains no
  `tools/lint-` adopter-facing path.
- **B5 `max_iterations` single-source** — **TDD.** A test pins that `loop-cohort.py`
  DEFAULTS carries no hard-coded `max_iterations` literal (it derives from the
  template), and that `loop-cohort` still resolves the cap from the template;
  the schema self-test (both blocks) stays green.
- **B6 doc honesty** — **goal-based + manual QA.** Shipped `CONVENTIONS.md` §
  Enforcement + `conventions-check.md` describe the adopter gate as `loop-cohort`
  + the adopter's own linters/tests (no catalogue-internal linters, no
  nonexistent CI job); repo `README.md` linter count is accurate; reviewer confirms.
- **B7 `AGENTS.local.md` direction** — **goal-based.** The local-only principle
  is recorded there.
- **B8 nothing catalogue-internal projects** — **goal-based.** `make build-check`
  self-host drift confirms `tools/pre-pr-catalogue.py` + the 7 linters don't project.

## Acceptance Criteria

- [x] **AC1** The shipped `pre-pr.py` source (`packs/core/.apm/hooks/pre-pr.py`)
      references **none** of the 8 catalogue checks — asserted by matching
      `tools/lint[-_]` **and** `test-lint-credentialed-skills` (the underscore
      variant `lint_credentialed_skills.py` must not slip a substring check) — and
      runs only `loop-cohort.py check` (against active spec `state.json`s) plus a
      commented "wire your own lint/test here" stub.
- [x] **AC2** Run in an adopter-shaped tree with **no** catalogue linters present:
      `pre-pr.py` exits 0 both with no active specs (skips) and with an active
      `state.json` (runs `loop-cohort check`); it never hard-fails on a missing linter.
- [x] **AC3** A catalogue-only hook (`tools/pre-pr-catalogue.py`, repo-native)
      runs the 8 catalogue checks (the exact ordered set the old `pre-pr.py` ran)
      and delegates to the shipped `pre-pr.py`. **Both** `make pre-pr` *and*
      `make build-check`'s direct hook invocation (`Makefile:74`) point at it, and
      the CI aggregator (`docs.yml` `hooks` job) is repointed — so this repo's full
      gate runs all 8 checks end-to-end. `tools/test-pre-pr.sh` is repointed at the
      catalogue hook and its existing regression guard (the layers it already
      corrupts: 4 linters + loop-cohort) still passes.
- [x] **AC4** The shipped `new-spec` `plan.md` template no longer references
      `tools/lint-plan-deps.py` (its `loop-cohort schedule` references already
      stand — this is a removal of the repo-native enforcement clause, not an addition).
- [x] **AC5** `session-start.py` contains no adopter-facing `tools/lint-*` path
      (hint generalized or removed).
- [x] **AC6** `max_iterations` has a single source of truth: it stays in the
      `state.json` template (the canonical, adopter-visible per-spec knob), and
      `loop-cohort.py` DEFAULTS **derives** its value from that template rather
      than hard-coding a duplicate literal — so an adopter changes the cap in one
      place. The `loop-cohort` schema self-test (`tools/test-loop-cohort.sh`'s
      `expected_keys` **and** `defaults-match-template` blocks) and `lint-agents-md`
      drift-watch #10a stay green **unchanged** (the template keeps the key).
- [x] **AC7** The shipped `CONVENTIONS.md` § Enforcement describes the adopter
      gate as `loop-cohort` + the adopter's own linters/tests — no
      catalogue-internal linters presented as the adopter's gate, no
      `.github/workflows/docs.yml` reference presented as the adopter's CI.
      `conventions-check.md` gets a one-line note that its named linters are *this
      catalogue's own* (adopters substitute their project's) — its graceful manual
      fallback already exists and stays. `tools/hooks/README.md`'s stale linter
      counts ("four/five/three") are corrected to the real set.
- [x] **AC8** `AGENTS.local.md` records the "adopter-facing materials ship;
      repo-specifics stay local-only" direction.
- [x] **AC9** `make build-check` passes; self-host drift confirms
      `tools/pre-pr-catalogue.py` and the 7 linters do **not** project to adopters.
- [x] **AC10** `docs/backlog.md` records follow-ups routed to their owning specs:
      RFC-0015 (`lint-plan-deps.py` unwired/orphaned) and RFC-0013
      (`add-credentialed-skill` / `example-credentialed-skill` adopter-shipping;
      the first-principles "the adopter artifact is the how-to" recommendation).

## Assumptions

- Technical: `pre-pr.py` hard-fails on the first missing linter (`_run` →
  `sys.exit(1)`); it runs **8** repo-native `_run` calls (6 `lint-*.py`,
  `lint_credentialed_skills.py`, `test-lint-credentialed-skills.py`) + loop-cohort;
  none ship (source: `packs/core/.apm/hooks/pre-pr.py:77-85`, grep).
- Technical: none of those checks are adopter-generic — `lint-agents-md` checks
  Diátaxis dirs + drift-watch against catalogue files + core-seed special-cases;
  `lint-agent-artifacts` enforces this catalogue's frontmatter conventions;
  `lint-knowledge` lints an optional Claude-Code-leaning feature (source:
  `tools/lint-agents-md.py`, `lint-agent-artifacts.py`, `lint-knowledge.py`).
- Technical: `loop-cohort.py check` is the one shipped, adopter-relevant gate (it
  caps the work-loop the adopter uses) (source: `loop-cohort.py`).
- Technical: `lint-plan-deps.py` (RFC-0015) and `add-credentialed-skill` /
  `example-credentialed-skill` (RFC-0013) are owned by other specs; the
  adopter-facing how-to + explanation for credentialed skills already exist
  (source: `docs/guides/{how-to,explanation}/*credential*`).
- Technical: `max_iterations` is double-sourced — `loop-cohort.py:55` DEFAULTS +
  `state.json:4`. The schema self-test's `defaults-match-template` block requires
  every DEFAULTS key to be in the template with a matching value, so the template
  must **keep** the key; single-sourcing therefore means DEFAULTS *derives* from
  the template (not the reverse). This leaves `expected_keys`, `defaults-match-template`,
  and drift-watch #10a unchanged (source: `tools/test-loop-cohort.sh`, `tools/lint-agents-md.py:222-231`).
- Process: the local-only direction lands in `AGENTS.local.md` (tracked), not
  `CONVENTIONS.md` (RFC-gated) (source: user confirmation 2026-05-30).
- Product: ship zero catalogue linters; `pre-pr` runs only `loop-cohort` + a
  stub; catalogue-only hook for the rest; one PR; reframe `conventions-check.md`
  (source: user confirmation 2026-05-30).
