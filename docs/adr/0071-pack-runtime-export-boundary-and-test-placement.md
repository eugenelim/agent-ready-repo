# ADR-0071: `.apm/` is the runtime export boundary; pack tests live at `packs/<pack>/tests/`

- **Status:** Accepted
- **Date:** 2026-08-06
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer, quality-engineer
- **Supersedes:** none
- **Related:** ADR-0002 (install scope per pack), `docs/specs/pack-test-boundary/spec.md`

## Decision summary

- **Decision:** Three boundaries, each owned by a different thing. The **pack** is
  the ownership and test-execution boundary. **`.apm/`** is the runtime export
  boundary — only content intended to be installed, projected, or executed.
  A **skill** is the evaluation-fixture boundary. Deterministic implementation
  tests live at `packs/<pack>/tests/`, laid out `tests/skills/<skill>/`,
  `tests/hooks/`, `tests/pack/`, `tests/fixtures/`. Runtime skill evals stay at
  `.apm/skills/<skill>/evals/`.
- **Because:** the separation must be structural, not incidental. Tests survived
  under `.apm/` only because the installer reads `seeds/` and `.apm/` and copies
  each skill directory wholesale — an implicit exclusion no adapter is obliged to
  preserve. An adapter that projected `.apm/**` faithfully would ship our test
  suites into every adopter's tree.
- **Applies to:** every pack in this catalogue, every projection adapter, and the
  packaging path.

## Context

`docs/knowledge/patterns.jsonl` is seeded into an adopter's repo, but the linter
that validates it lived in `tools/` — catalogue-local, never installed. The
seeded README told adopters to run a script they had never been given, and
nothing gated a file we hand them. Fixing that meant moving the linter into the
core pack, which meant its test needed a home, which surfaced the absence of any
boundary: every core-pack test sat under `.apm/skills/*/scripts/`.

Nothing enforced a rule either way. `lint_packs._PACK_SUBTREES` walks only
`seeds/` and `.apm/`; `verify.py:_step_primitive_layout` returns no diagnostics;
`pack.schema.json` constrains `pack.toml`, not the directory tree. The layout was
whatever the last author chose.

## Options considered

**A — leave tests under `.apm/`, rely on the installer ignoring them.** Zero work.
Rejected: it is the status quo that produced the defect, and it makes correctness
depend on an adapter's incidental behaviour rather than on structure. The rule
"do not put tests here" cannot be checked when tests are already there.

**B — a repository-root `tests/` tree mirroring `packs/`.** Conventional in many
repos. Rejected: it separates a test from the pack it validates, so a pack
extracted from the catalogue — the point of a distributable pack — arrives with
no way to verify itself. It also gives cross-pack tests and pack-owned tests the
same home, which is the ambiguity we are trying to remove.

**C — `packs/<pack>/tests/`, chosen.** The pack stays self-contained and
independently verifiable; the runtime payload stays clean; and where cross-cutting tests live stays open. This
catalogue declines a root `tests/` — a new top-level directory is RFC-gated
here — and keeps catalogue-wide behaviour in the engine's own suite.

**Evals: keep at `.apm/skills/<skill>/evals/`.** A pack-root `evals/` was
considered and rejected. An eval fixture only means anything beside the skill it
exercises, and the linter already enforces skill-local placement — it looks for
`eval_queries.json` and `evals.json` under `<skill>/evals/` and requires one for
every skill named in `[pack.evals].skills`. Evals are runtime-adjacent content
that projects with the skill; a test suite is not.

## Consequences

**Catalogue archives carry tests; installers do not install them.** `package.py`
walks `packs/**`, so `tests/` lands in a source archive. That is wanted —
downstream verification, auditing, security review, testing an extracted release.
Projection adapters read only `.apm/` and `seeds/`, so nothing reaches an
installed environment. Catalogue inclusion does not imply runtime installation.

**The boundary is now checked, not asserted.** `packs/core/tests/pack/test-runtime-boundary.py`
fails when test content appears under `packs/core/.apm/`, and — separately and
positively — when it appears in a projected core skill. The second check exists
because inferring "no tests are installed" from "the installer ignores those
paths" is the reasoning that let the violation persist.

**Migration is partial and the gap is visible.** Only `core` has moved. The other
packs still hold tests under `.apm/skills/*/scripts/`; the boundary test is
scoped to `core` so it fails on regressions rather than on deferred work.
Tracked as `pack-test-boundary-remaining-packs` in `workspace.toml [backlog].open`.

**Relocated tests target the pack source, not the projection.** They resolve
`parents[N] / ".apm" / ...` rather than `.claude/skills/...`. Projection fidelity
is separately gated by the self-host drift check, so this is not a coverage loss,
but it does mean the drift check is now the sole guard on that seam.
