# Spec: spec-code-ref-lint

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0016

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The catalogue's Tier-1 doc-drift lint (`packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`, shipped in
the `doc-drift-prevention` spec) checks four invariants over spec metadata.
Invariant (iii) — dangling intra-repo references — currently checks **doc
links only** (markdown links ending in `.md`) and is **warn-only**. RFC-0016
Open Question 3 deferred extending it to **code paths** to v1.1, "after the
warn-only rate is observed."

This spec is that v1.1. Success for the **catalogue maintainer**: when a spec
references a source file by its full repo-relative path (e.g.
`tools/lint-seeds.py`, `packages/agentbundle/agentbundle/build/self_host.py`)
and that file has since moved, been renamed, or been deleted, `make
build-check` surfaces a **warning** naming the spec, line, and dangling path —
so stale references to relocated code are visible instead of silently rotting.
The check stays **warn-only**: the shipped lint emits ~16 such dangling code
references today, almost all on Frozen specs whose bodies cannot be edited, so
failing the build on them is neither correct nor actionable. Promoting
invariant (iii) to a hard gate remains deferred — now with a measured baseline.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Extend the existing invariant (iii) inside `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`'s
  `check()` — one focused change, stdlib only, mirroring the existing
  doc-reference shape.
- Restrict code-reference detection to **full repo-relative paths**: the
  reference must contain `/`, be rooted at a real top-level directory
  (`packages/`, `tools/`, `packs/`, `docs/`, `apps/`, `.github/`), and end in
  a recognised code extension (`.py`, `.toml`, `.sh`, `.json`) after a trailing
  `:<line>` / `:<range>` / `#<anchor>` suffix is stripped.
- Add red-and-green construction tests for every detection/exclusion rule.

### Ask first

- Promoting invariant (iii) (doc or code) from warn-only to a hard
  (exit-non-zero) invariant — still gated on the observed warn rate per
  RFC-0016; this spec only adds the code-reference surface, it does not flip
  severity.
- Widening the recognised top-level roots or code extensions beyond the set
  above.

### Never do

- **Fail the build on a dangling code reference.** Invariant (iii) is
  warn-only; the code-reference extension inherits that exactly. It must never
  change the lint's exit code.
- **Flag bare basenames** (`install.py`, `scope.py` — no `/`), **placeholder
  paths** (containing `<` or `>`), or **globs** (containing `*`). These are
  unresolvable or intentional and would be false positives.
- **Edit Frozen spec bodies to silence a warning.** The surfaced stale
  references are the feature working; fixing them (where the spec is editable)
  is separate, out-of-scope work.
- **Change the existing doc-reference (`.md`) behavior**, or introduce a new
  dependency, module, or top-level directory.

## Testing Strategy

- **Code-reference extraction + resolution (AC1, AC2, AC3) — TDD.** The
  detection rules are pure logic over spec text with crisp accept/reject
  boundaries; each rule gets a red-and-green case in the lint's existing
  subprocess self-test (`packs/core/.apm/skills/work-loop/scripts/test-lint-spec-status.py`).
- **Warn-only severity (AC3) — TDD.** A fixture with a dangling code reference
  must leave the exit code at 0 — asserted directly.
- **Live-corpus behavior (AC5) — goal-based.** `python packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`
  over this repo still exits 0, and emits the code-reference warnings; verified
  by a one-liner (run it, assert exit 0, eyeball the warning count).
- **Docstring/header accuracy (AC6) — goal-based.** `grep` that the lint's
  module docstring describes invariant (iii) as covering code references.

## Acceptance Criteria

<!-- A deferred criterion uses: - [ ] <outcome> (deferred: <backlog-anchor>) -->

- [x] **AC1 — code references are detected and resolved.** Invariant (iii) in
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` scans each spec for full repo-relative code paths
  (in backticks or markdown links): contain `/`, rooted at one of
  `packages/ tools/ packs/ docs/ apps/ .github/`, ending in `.py`/`.toml`/`.sh`/
  `.json`. **Suffix strip:** once the recognised extension is found, everything
  from the first `:` or `#` after it to end of token is stripped (so
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:42`, `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:42:10`, and
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py#L42` all resolve to the same real file). If the
  resolved path is not a file, it emits a warn-only
  diagnostic naming the spec, line, and path. **Scope of the two scans:** the
  code-ref scan covers only the four code extensions above; the pre-existing
  `.md` doc-reference scan (markdown links only) is unchanged and is *not*
  widened to backticked `.md` paths — the boundary between the two is
  deliberate, not a gap.
- [x] **AC2 — false-positive shapes are excluded.** Bare basenames (no `/`),
  placeholder paths (containing `<` or `>`), globs (containing `*`), and
  brace-expansion shorthand (containing `{` or `}`, e.g.
  `adapters/{claude_code,kiro}.py`) are never flagged.
- [x] **AC3 — warn-only, doc behavior unchanged.** A dangling code reference
  never changes the lint's exit code; the existing `.md` doc-reference check
  (its targets and resolution) is unchanged.
- [x] **AC4 — construction self-test covers each rule.**
  `packs/core/.apm/skills/work-loop/scripts/test-lint-spec-status.py` gains cases asserting: a resolving full path
  → no warning; a missing full path → warning (exit still 0); a bare basename →
  no warning; a placeholder path → no warning; a glob → no warning; a path with
  a `:line` suffix that resolves after stripping → no warning.
- [x] **AC5 — live corpus stays green.** `python packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` over
  this repo exits 0; it emits one or more dangling-code-reference warnings
  (baseline ~16 measured post-implementation — a sanity check, **not** a pinned count, since the
  corpus drifts) without failing the run.
- [x] **AC6 — docstring reflects the widened invariant.** The lint module
  docstring in `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` describes invariant (iii) as covering
  dangling **doc and code** references, warn-only.
- [x] **AC7 — register updated.** The `docs/backlog.md` RFC-0016 follow-up item
  for invariant (iii) is updated: code-reference detection shipped (warn-only);
  promote-to-hard remains deferred, now annotated with the measured baseline
  (~16 corpus warnings, mostly on Frozen specs).

## Assumptions

- Technical: the resolvable code-reference subset is full repo-relative paths;
  bare basenames cannot be located (probe: 281 full-path of 467 backticked
  `.py` refs across `docs/specs/*/spec.md`, 2026-05-29).
- Technical: code references appear overwhelmingly in backticks, not markdown
  links (~467 vs ~13), so the extractor must scan backticked spans; `:line` /
  `#anchor` suffixes and `<placeholder>` / `*glob` forms must be handled (probe).
- Technical: `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` invariant (iii) is warn-only today and
  scans `.md` markdown links only (source: `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` `check()`,
  the `(iii)` block).
- Product: v1.1 = add the code-reference surface, keep warn-only; promote-to-hard
  stays deferred (source: RFC-0016 § Open questions Q3; observed baseline ~16
  warnings, mostly Frozen specs, probe 2026-05-29 — confirms hard is premature).
- Process: surfaced stale references are not fixed in this PR (Boundary: no
  Frozen-body edits; the cleanup is separate work). Most of the ~16 are
  `.sh`→`.py` ports and files removed in the credential-broker migration.
