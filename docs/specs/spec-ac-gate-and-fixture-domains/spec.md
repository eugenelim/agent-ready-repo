# Spec: spec-ac-gate-and-fixture-domains

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. One linter becomes case-tolerant; one test corpus
  changes its placeholder domains.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. One risk trigger fires: structural / gate-behaviour change —
widening a linter's match changes what can merge, across 18 previously un-gated
specs. Blast radius was measured BEFORE the change (see AC2). The G-plan human
gates are satisfied by the operator's standing authorization for this run. -->

## Objective

Two hygiene defects, both of the same shape: something that looks checked and is
not.

## Acceptance Criteria

- [x] **AC1 — the AC-completeness invariant stops passing vacuously.**
  `lint-spec-status.py` matched `^##\s+Acceptance Criteria\b` case-sensitively,
  so a spec headed `## Acceptance criteria` collected zero criteria and invariant
  (ii) passed on a section it never read. The match is now case-insensitive.

- [x] **AC2 — the blast radius was measured before the change, not after.**
  Widening the match re-gates every previously-unread spec at once, so the
  question "does this turn the build red?" is answered first: all 18 affected
  specs have every AC checked (0 unchecked across all of them). No cascade.

- [x] **AC3 — the fix is mutation-verified.** Reverting the matcher to
  case-sensitive fails exactly the sentence-case and upper-case arms of the new
  parametrized test, and restoring it passes all five. The test rides the
  diff-triggered `born Shipped` harness the invariant actually uses — an earlier
  draft asserted against a non-diff fixture and failed on every arm including
  title-case, which showed the premise was wrong rather than the code.

- [x] **AC4 — the corpus is consistent.** All 18 lowercase headings are
  normalised, so `grep -rl '^## Acceptance criteria' docs/specs/*/spec.md`
  returns nothing and 323 specs carry the canonical form. The linter change is
  the load-bearing half; this stops a reader seeing two forms and guessing.

- [x] **AC5 — the missing-section half is split out, not silently dropped.** The
  original entry bundled two questions. Case handling is a bug in a regex; "should
  a spec with no Acceptance-Criteria section fail loudly?" is a policy call about
  what a spec must contain, and some specs may legitimately have none. Recorded as
  `spec-missing-ac-section-policy`.

- [x] **AC6 — test fixtures use reserved domains.** `corp.com` and `x.com` are
  *registered* domains; `catalogue-authoring-standards.md` § 4 and the repo
  privacy rule both ask for RFC 2606 reserved names. `corp.com` → `example.com`
  and `x.com` → `example.net` across 56 occurrences in 4 files. Two distinct
  source domains map to two distinct reserved names, because fixtures that assert
  on cross-domain behaviour need them to stay distinct.

- [x] **AC7 — the independent oracle is regenerated, not hand-edited.**
  `msgreader_baseline.json` is a committed capture from the Node `msgreader`
  package — a different implementation, which is what makes it a cross-check
  rather than a second copy of our own output. Editing its strings by hand would
  have quietly demoted it to a restatement of our own reader. It was regenerated
  with `regen_msgreader_baseline.py` against real Node.

  The regenerated file is byte-identical to what a plain rename would have
  produced — which *confirms* the domain is opaque payload rather than excusing
  the shortcut. Confirming that after the fact is the point; assuming it up front
  would have been the error.

- [x] **AC8 — the projected copy is back in sync.** `lint-spec-status.py` is
  authored in `packs/core/.apm/` and projected to `.claude/skills/`. Re-projected
  with `make build-self FORCE=1`; the two files are byte-identical.

- [x] **AC9 — the backlog is dispositioned.** Both entries removed, one new
  policy entry added.

## Boundaries

### Never do

- Never hand-edit `msgreader_baseline.json`. Regenerate it, or leave it.
- Never edit `.claude/skills/**` directly — it is projected output.

## Testing Strategy

- **TDD + mutation** for AC1/AC3. **Goal-based** for AC2, AC4, AC8, AC9.
- **Oracle regeneration** for AC6/AC7, with the full converter suite as the gate.
