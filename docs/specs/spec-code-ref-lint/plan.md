# Plan: spec-code-ref-lint

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

One focused change to `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`: factor a pure
`code_references(text)` helper that extracts candidate repo-relative code paths
(backticked spans + markdown links), applies the accept/reject rules, and yields
`(lineno, path)`; then call it inside invariant (iii) alongside the existing
`.md` doc-reference scan, resolving each against the repo root and emitting a
warn-only diagnostic on a miss. The riskiest part is false positives — bare
basenames, placeholders, globs, and `:line` suffixes — so the helper is pure and
gets exhaustive red/green tests before it's wired in. Severity is unchanged
(warn-only), so the live corpus must still exit 0; the ~16 known dangling refs
become visible warnings, not failures.

## Constraints

- **RFC-0016** § Open questions Q3 — v1.1 extends invariant (iii) to code paths;
  promote-to-hard stays deferred (observed baseline now ~16 warnings).
- The lint is invoked from the Makefile `build-check` target, never the projected
  `pre-pr.py`. (Delivery note: the co-landing `lint-work-loop-delivery` spec
  relocates the lint to a projecting `work-loop` skill script — see RFC-0016
  § Errata / ADR-0007; this v1.1 change is invariant-logic only.)

## Construction tests

**Integration:** `make build-check` exits clean (the lint runs, emits code-ref
warnings, exits 0). **Manual verification:** none.

## Tasks

### T1: extract + resolve repo-relative code references (warn-only)

**Depends on:** none

**Tests:**
- TDD (AC1/AC2/AC3): new cases in `packs/core/.apm/skills/work-loop/scripts/test-lint-spec-status.py` driving
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` as a subprocess over fixture specs. **Each
  exclusion case is paired with a shape-matched accepting control** so a no-op
  extractor (that matches nothing) fails the suite rather than passing every
  reject vacuously —
  - a backticked full path that resolves → no warning, exit 0;
  - a backticked full path that does **not** resolve → a `(iii)` warning, **exit 0**
    (the positive control for the reject cases below);
  - bare basename `install.py` → no warning, **paired with** `tools/install.py`
    (missing) → warning;
  - placeholder `packages/<pkg>/x.py` → no warning, **paired with**
    `packages/real/x.py` (missing) → warning;
  - glob `tools/lint-*.py` → no warning, **paired with** `tools/lint-missing.py`
    → warning;
  - suffix strip: `tools/x.py:42`, `tools/x.py:42:10`, and `tools/x.py#L42` all
    resolve (after stripping) when `tools/x.py` exists → no warning; and
    `tools/missing.py:42` → warning (strip then resolve, still missing);
  - a markdown-link code target `[t](../../tools/x.py)` that misses → warning;
  - **no-regression:** the pre-existing `case_invariant_iii_warn_only` (dangling
    `.md` link, warn-only) still passes after the refactor.

**Approach:**
- Add a module-level `_CODE_REF_RE` for backticked spans and reuse `_LINK_RE`
  for links; a pure `code_references(text)` generator applies: must contain `/`;
  first path segment ∈ `{packages, tools, packs, docs, apps, .github}`; ends in
  `.py`/`.toml`/`.sh`/`.json` after stripping a trailing `:<...>` or `#<...>`;
  reject if it contains `<`, `>`, or `*`.
- In `check()`'s invariant (iii) block, after the existing `.md` link scan, call
  `code_references(text)` and resolve each against `root` (and spec-relative, as
  the doc check does); append a warn-only diagnostic on a miss. Reuse the
  existing warn list — never touch `hard`.

**Done when:** all T1 self-test cases pass — including the paired accepting
controls and the pre-existing `case_invariant_iii_warn_only` (no `.md`
regression) — via `python packs/core/.apm/skills/work-loop/scripts/test-lint-spec-status.py`.

### T2: live corpus stays green with code-ref warnings

**Depends on:** T1

**Tests:**
- Goal-based (AC5): `python packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` exits 0; its stderr shows
  the code-reference warnings (≈16; the count is a sanity check, not a pinned
  assertion — the corpus drifts).

**Approach:**
- Run the lint; confirm exit 0 and that the warnings name real dangling paths
  (`.sh`→`.py` ports, removed `creds/loader.py`, etc.). Do **not** edit any
  spec to silence them (Boundary).

**Done when:** `make build-check` exits 0 with the code-ref warnings present.

### T3: docstring + register update

**Depends on:** T1

**Tests:**
- Goal-based (AC6): `grep` the `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` module docstring for
  invariant (iii) described as covering **doc and code** references.
- Goal-based (AC7): `grep` `docs/backlog.md` — the invariant-(iii) follow-up item
  reflects code-refs shipped (warn-only) + promote-to-hard still deferred with
  the measured baseline.

**Approach:**
- Update the docstring's `(iii)` line.
- Update the `docs/backlog.md` RFC-0016 invariant-(iii) follow-up bullet.

**Done when:** both greps pass.

## Rollout

Big-bang within the catalogue, fully reversible (additive warn-only logic + tests
+ doc text). (The lint itself ships to adopters once the co-landing
`lint-work-loop-delivery` relocation lands; this v1.1 change adds only the
invariant-(iii) code-reference logic.)

## Risks

- **False positives flood build-check stderr.** Mitigated by the strict
  full-path/rooted/extension filter and the exclusion rules, all unit-tested;
  warn-only means worst case is noise, never a red build.
- **An over-broad extractor matches prose.** Mitigated by requiring a known
  top-level root segment + code extension, and rejecting placeholders/globs.

## Changelog

- 2026-05-29: initial plan (RFC-0016 invariant-(iii) v1.1 follow-up).
