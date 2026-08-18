# Plan: guide typed asides test gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

## Approach

Two decisions, deliberately not conflated: what the assertions should say, and which
of them a gate should enforce.

**The assertions.** `assert version == "0.37.1"` compared the *current*
`pyproject.toml` version to a literal, so it failed on every release. Bumping it to
`0.37.2` was rejected: the surrounding assertions then require the 0.37.2 release
notes to claim a change 0.37.2 did not make. `CHANGELOG.md` retains every release
section, so the durable form names the shipping release in a constant
(`STANDARD_RELEASE`) and anchors the typed-asides wording to *that* section.

**Which of them to gate.** The original plan wired the whole file in. Review proved
that harmful: the file pins a frozen 165-row blockquote ledger across 193 `guides/**`
files, there is no regenerator, and `build-check.yml` carries no `paths:` filter — so
adding one blockquote to any guide would redden a required check. An unrelated PR
(`8476fc63`, tracker-intake adapters) had already been forced to hand-edit that
ledger. Separately, the `README-pypi.md` current-release assertion is a release
obligation nothing else enforces: 12 of the last 25 commits that bumped
`pyproject.toml` did not touch that file.

So the file is **split**. The live invariants — those that hold at every release and
that no routine unrelated change can redden — move to a new gated file. The archival
conversion record stays where it is, deliberately unwired, with a docstring saying so
and a register slug behind it. That converts "an unwired test never gates" from an
accident into a decision for the archival half, while actually gating the half that
encodes a live contract.

## Construction tests

**Integration tests:** none — every assertion reads committed files.
**Manual verification:** each assertion in the gated file mutated against a fixture
and observed red, with a positive control and the harness committed beside the
results in [`notes/falsifiability.md`](notes/falsifiability.md).

## Tasks

### T1: the live invariants are gated, and every one of them can fail

**Depends on:** none · **Verification mode:** TDD

**Touches:** tools/test_guide_authoring_standard.py, tools/test_guide_typed_asides.py, docs/specs/guide-typed-asides-test-gate/notes/falsifiability.md

**Tests:**
- `tools/test_guide_authoring_standard.py` passes: the authoring standard's fixed
  aside contract, the packaged scaffold copy's byte-equality, its manifest digest,
  and `CLI_VERSION` ↔ `pyproject.toml`. Verifies AC1, AC2.
- `tools/test_guide_typed_asides.py` passes, with no assertion comparing the current
  version to a literal. Verifies AC1.
- One falsifiability probe per assertion in the gated file, plus a positive control on
  the unmutated fixture. The harness rebinds **every** import-time path constant, not
  just `REPO_ROOT` — `AUTHORING_STANDARD` and `SCAFFOLD_ROOT` are derived at import
  and would otherwise still point at the live worktree. Verifies AC3.
- No gated assertion pins incidental formatting: each compares against
  whitespace-normalised text, so a markdown reflow cannot redden a required check.
  Verifies AC2 and the first "Always do".

**Approach:**
- Create `tools/test_guide_authoring_standard.py` holding only the live invariants.
- Narrow `tools/test_guide_typed_asides.py` to the archival record; give it a module
  docstring stating it is deliberately unwired, why, and how to run it directly.
- Delete the constants the split orphans.
- Anchor the historical heading to exactly one `## [<release>]` match and
  whitespace-normalise the wording assertion.

**Done when:** both files pass, and every gated assertion has been observed red.

### T2: the gated file is wired, and the archival file is not

**Depends on:** T1 · **Verification mode:** goal-based check

**Touches:** Makefile, .github/workflows/build-check.yml, workspace.toml

**Tests:**
- `tools/test_guide_authoring_standard.py` appears exactly once in the Makefile `test`
  target and once in the `build-check.yml` step carrying the parallel pytest list.
  Verifies AC5.
- `tools/test_guide_typed_asides.py` appears in **neither**, asserted rather than
  grepped by hand, so re-wiring it is detected. Verifies AC5.
- Every excluded assertion resolves to a `workspace.toml [backlog].open` slug.
  Verifies AC6.
- `make ci` passes. Verifies AC7.

**Approach:**
- Append **only** `tools/test_guide_authoring_standard.py` to both lists, keeping them
  identical.
- Do **not** append `tools/test_guide_typed_asides.py`. Wiring it in is the change this
  spec exists to refuse; `spec.md`'s "Ask first" boundary covers it and
  `guide-blockquote-ledger-has-no-regenerator` records why.
- Register `guide-blockquote-ledger-has-no-regenerator` and
  `readme-pypi-whats-new-unenforced`.

**Done when:** the wiring assertions hold and `make ci` passes.

## Rollout

Single PR. **Cross-spec ordering:** the Makefile and `build-check.yml` lists this
change touches are also appended by `spec/marketplace-generator-single-source`, whose
gate additionally asserts the two lists are identical. That spec lands first; this one
follows on a branch stacked on it, so neither PR carries the other's wiring line and
`make test` never references a file its own branch does not contain.

## Risks

- **A future maintainer re-wires the archival file.** `workspace.toml`'s
  `tools-test-runner-boundary` entry lists this file among tests "invoked by nothing",
  whose stated fix is to give every test a runner. That entry is amended to name this
  file as a sanctioned no-runner case; the file's own docstring and
  `guide-blockquote-ledger-has-no-regenerator` are the other two signposts.
- **The archival file rots.** It is not gated, so nothing catches it going stale. That
  is the accepted cost of not reddening a required check for unrelated work; the slug
  carries the condition under which it becomes gateable (a ledger regenerator).

## Changelog

- 2026-08-17: initial plan — fix the version pin, wire the whole file into the gate
  chain.
- 2026-08-18: split the file after light-mode review, on the two measured findings
  recorded in the Approach above. The live invariants are gated; the archival record is
  deliberately unwired and registered. Also applied: whitespace normalisation on the
  wording assertions (one had pinned an incidental line wrap), the historical heading
  anchored and counted (`"## [0.37.1]" in changelog` was also satisfied by a `###`
  subheading), the README message no longer claims a section scope it does not enforce,
  and the missing manifest-digest probe added — the earlier scaffold probe failed at the
  byte comparison first, so the digest assertion had never been observed red.
