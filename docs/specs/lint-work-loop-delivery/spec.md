# Spec: lint-work-loop-delivery

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0016 (§ Errata)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

RFC-0016 shipped the spec-metadata lint (then under `tools/`) as
**catalogue-only**, on the premise that "linters don't project." That premise
was wrong — corrected in RFC-0016 § Errata: a skill's `scripts/` folder is a
first-class projecting surface that already carries governance Python helpers to
all four adapters (`new-adr`/`new-rfc`'s `next-ordinal.py`, `work-loop`'s
`loop-cohort.py`).

This spec delivers the lint **the correct way**: relocate it into the
`work-loop` skill's `scripts/` folder so it projects to adopters, invoked by the
agent at the work-loop's finish-time checklist (available and agent-invoked, the
same model as `loop-cohort.py`). The catalogue keeps running it as a fail-closed
CI gate via `make build-check`. Success for the **adopter**: a runnable
spec-metadata check on every adapter that has Python — no longer
construction+judgment alone. Success for the **catalogue maintainer**: the lint
keeps its CI gate, and source↔projection stays drift-checked. This is a
**relocation + wiring** change only: the lint's invariant logic is unchanged here
— the invariant-(iii) code-reference extension already shipped under
`spec-code-ref-lint` (it co-lands in this PR but is not part of *this* change's
contract).

## Boundaries

### Always do

- `git mv` the lint and its self-test (preserve history) into
  `packs/core/.apm/skills/work-loop/scripts/`, then `make build-self` to project.
- Keep the lint's behaviour byte-for-byte except the self-test's path to the
  linter (which must point at its new sibling).
- Keep the catalogue's fail-closed CI gate: `make build-check` still runs the
  lint and its self-test.

### Ask first

- Choosing a different owning skill than `work-loop` (work-loop is chosen: the
  lint mechanises its finish-time drift checklist).
- Promoting any invariant from warn-only to hard, or changing invariant logic —
  out of scope here.

### Never do

- **Wire the lint into the projected `pre-pr.py`.** That Boundary from
  `doc-drift-prevention` still holds — `pre-pr.py` is a hook body that would
  mis-fire in adopter trees. The lint is invoked from the work-loop skill's
  finish-time checklist and from the Makefile gate, never the hook.
- **Change the lint's invariant logic** (i/ii/iii/iv). Relocation + wiring only.
- **Introduce a new dependency, module, or top-level directory.** It moves into
  an existing skill's existing `scripts/` folder.
- **Leave a copy at `tools/`** — the move is complete, not a fork.

## Testing Strategy

- **Relocation correctness (AC1, AC2) — goal-based + TDD.** The self-test
  (relocated) is the TDD artifact — it must stay green from the new path; a
  goal-based `git ls-files` / `test -f` confirms the files moved and no `tools/`
  copy remains.
- **Wiring (AC3, AC4, AC5) — goal-based.** `grep` that `work-loop` SKILL.md names
  the finish-time invocation; that the Makefile runs the projected copy; that
  `pre-pr.py` still does not reference the lint.
- **Projection + catalogue gate (AC7) — goal-based.** `make build-check` exits 0
  and is drift-clean (projected `.claude/skills/work-loop/scripts/` matches
  source).

## Acceptance Criteria

- [x] **AC1 — lint + self-test relocated and projecting.**
  `lint-spec-status.py` and `test-lint-spec-status.py` live at
  `packs/core/.apm/skills/work-loop/scripts/`; no copy remains under `tools/`;
  both project to `.claude/skills/work-loop/scripts/` after `make build-self`.
- [x] **AC2 — behaviour preserved.** The self-test passes from the new location
  (its path to the linter updated to the sibling); the live corpus result is
  unchanged (exit 0 with the same warn-only code/doc references).
- [x] **AC3 — work-loop invokes it at finish-time.**
  `packs/core/.apm/skills/work-loop/SKILL.md` instructs the agent to run
  `scripts/lint-spec-status.py` at the finish-time checklist, framed as the
  mechanical companion to the four drift invariants (available on every adapter
  with Python; the catalogue also gates it in CI). The prior "catalogue-only —
  an adopter has no such file" framing is replaced.
- [x] **AC4 — Makefile gate uses the projected copy.** `make build-check`
  invokes `.claude/skills/work-loop/scripts/lint-spec-status.py` and its
  self-test; the old `tools/` invocation is removed.
- [x] **AC5 — still not in pre-pr.** Neither `packs/core/.apm/hooks/pre-pr.py`
  nor its projection references the lint.
- [x] **AC6 — governance reconciled across all three artifacts.** RFC-0016
  carries an Approver-signed § Errata correcting the projection premise and
  Decision #1; the `doc-drift-prevention` spec carries a matching Changelog
  erratum superseding its catalogue-only Boundaries; and **ADR-0007** is recorded
  (Accepted), narrowing ADR-0006's "mechanically gated only as catalogue
  governance" sub-claim while leaving its construction+judgment core intact (ADRs
  supersede via a new ADR, not errata — CONVENTIONS § 2).
- [x] **AC7 — catalogue gate green + knowledge updated.** `make build-check`
  exits 0 and drift-clean; knowledge entry K-0009 is corrected (the spec-status
  lint now ships as a work-loop skill script — no longer "no `packs/` source").

## Assumptions

- Technical: skill `scripts/` folders project to all four adapters and already
  ship governance Python (source: `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`,
  `packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py`).
- Technical: the lint discovers the repo root via `git rev-parse --show-toplevel`,
  so it works unchanged from a skill `scripts/` location (source:
  `lint-spec-status.py` `_repo_root()`).
- Process: RFC-0016 § Errata (Approver eugenelim, 2026-05-29) authorises shipping
  the lint to adopters; the `doc-drift-prevention` catalogue-only Boundaries are
  superseded by that erratum (source: RFC-0016 § Errata; doc-drift-prevention
  spec § Changelog).
