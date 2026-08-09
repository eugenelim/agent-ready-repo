# Plan: catalogue test carve-out

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The expensive part of this work is deciding, not moving. Roughly a hundred
modules are candidates; the automated signal that finds them cannot decide any of
them, because reading `packs/` and testing `packs/` are different things. So the
plan front-loads classification as its own task with its own deliverable — a
recorded owner per module — and treats relocation as the mechanical consequence.

The shape of the work is not what RFC-0082 first assumed, and the plan follows
the corrected picture. No module in `tests/build_pipeline/` (formerly `agentbundle/build/tests/`) is a standalone rule-shaped
conformance test. The rule-shaped material exists, but embedded as classes inside
three engine modules. So the shipped conformance suite is assembled by
**extraction**, not by moving files, and that is T3 rather than a footnote.

Five positive allowlists gate the destination. None of them is a filter to relax
— each excludes a repository-root `tests/` by construction, and the tree cannot
even be created until `RFC_AUTHORISED_DIRS` admits it. Four are grouped in T2; the
fifth, `_SYNC_PAIRS`, lands in T5 alongside the scaffold template it registers,
because registering a file that does not exist yet is not a coherent commit.

Riskiest part: the portability claim. A conformance suite that passes here proves
nothing about an adopter's catalogue, because here the roster it might
accidentally depend on is satisfied. The only honest check is to scaffold a
catalogue and run the suite against it, so that is written as a task and not as a
review step.

## Constraints

- **ADR-0075** — the ownership taxonomy, its four homes, class-level
  granularity, and per-owner inclusion.
- **RFC-0082** — the proposal and its measured evidence; D7 is the portability
  rule this plan implements.
- **ADR-0071** — `packs/<pack>/tests/` is where pack tests live; this plan adds
  to that tree and changes nothing about it.
- **`engine-export-boundary` spec must land first** — it makes the export
  boundary real, so relocations here cannot silently re-enter an artifact.
- **`Engine-Change-RFC:` trailer** on commits touching non-carved-out
  `packages/agentbundle/` paths; `/tests/` and `build/recipes/` are carved out
  (`tools/lint-catalogue-curation-guard.py:100-115`).
- **New `tools/` scripts are pure-stdlib Python.**

## Construction tests

**Integration tests:**

- Every suite green from its new home: engine, `tests/conformance/`,
  `tests/roster/`, and each pack suite that gained modules.
- `make ci` green, including the new root tree's runner.

**Manual verification:**

- `agentbundle catalogue init` into a temp directory, then run the materialised
  conformance suite against the scaffolded catalogue — for the default preset and
  for `--preset self-hosted` in both `--tooling` modes. This is the portability
  proof and cannot be replaced by inspection.
- Build a `catalogue package` archive in both flavours; confirm
  `tests/conformance/` is present.

## Design (LLD)

`Shape: mixed`. Three sub-sections earn their place.

### Component decomposition

Traces to AC2, AC4, AC5. The root tree splits by *shippability*, not by test
kind:

```
tests/
├── conformance/   rule-shaped; ships to every catalogue
└── roster/        pins this repository's content; never ships
```

That split is the mechanism behind D7. Shipping becomes a directory rule rather
than a per-file judgement someone has to remember, and it is reviewable in a diff.

### Interfaces & contracts

Traces to AC6, AC7, AC8. Three shipping channels, and they share no code:

- `catalogue package` — widen `_DEFAULT_INCLUDE_DIRS` and `_SOURCE_INCLUDE_DIRS`.
- `catalogue init --preset self-hosted` — copies from a source catalogue.
- `catalogue init` (default preset) — materialises the bundled scaffold, so the
  scaffold itself gains a `tests/conformance/` template.

The scaffold template is inert content that lives *inside* the engine's export
boundary by design. The artifact gate must exempt
`_data/catalogue-scaffold/**`, and `build_zipapp.py`'s ignore pattern must
already have been narrowed by the engine spec — otherwise the zipapp strips the
template and `catalogue init` aborts on manifest verification.

### Data & schema

Traces to AC8. The scaffold manifest is hash-verified at init time, so a template
file that is not registered in `_SYNC_PAIRS` gets no manifest entry, is never
materialised, and surfaces only as a non-blocking INFO. That is a silent
shipping-nothing failure, which is why AC8 names `_SYNC_PAIRS` explicitly.

## Tasks

### T1 — Classify every candidate module, and record the owner

- **Implements:** AC13 (Testing Strategy: goal-based, human-reviewed). Gates
  every other task.
- **Depends on:** none

**Tests:**

- Every module in the candidate set has a recorded owner. The check is
  completeness of the record, not correctness of each call — correctness is a
  review judgement by construction.
- The three genuinely open contested calls each have a recorded disposition. The
  fourth — granularity — is closed by ADR-0075 and needs only its per-module
  application recorded.

**Approach:**

Start from `docs/rfc/0082-notes/first-cut-ownership-mapping.md`, which
hand-classifies `tests/build_pipeline/` (formerly `agentbundle/build/tests/`) and is explicitly provisional. Re-derive the
candidate set rather than inheriting a number: 82 under the quoted-directory
sweep, 103 under the path-form sweep, and both miss modules that locate the
repository root by walking for a marker instead of by index.

Decide from what each test **asserts**. Invoking engine code and asserting on its
output is engine-owned even when a live pack is the input; sweeping the pack tree
and asserting on its content is catalogue-owned even when engine code does the
sweeping.

Settle `contracts/adapter.toml`'s status once, for all modules, rather than
per-module — it is listed under *Ask first*.

### T2 — Create the root tree and widen the four packaging allowlists

- **Implements:** AC2, AC7, AC7b, AC11, AC11b, AC12, AC14 (Testing Strategy:
  goal-based). `_SYNC_PAIRS`, the fifth allowlist, lands in T5 with the scaffold
  template it registers.
- **Depends on:** T1

**Tests:**

- `tools/lint-build.py` accepts the new top-level directory.
- A `catalogue package` archive contains `tests/conformance/`, both flavours.
- The root tree is collected by `make test`.

**Approach:**

Four edits, none of them a filter relax:

- `tools/lint-build.py` — add `"tests",  # RFC-0082` to `RFC_AUTHORISED_DIRS`.
  Nothing else can proceed until this lands. Also fix the merge-base fallback to
  try `origin/main`: today `git merge-base HEAD main` fails on a CI checkout and
  the audit *skips and returns success*, so this gate has never actually run in
  CI (AC14). Expect that to redden other in-flight branches — it is a real
  behaviour change to a governance gate, which is why it carries a criterion.
- `catalogue_tooling/package.py` — scope to the **conformance** subtree, not to
  `tests`. Both constants are walked wholesale (`package.py:176-187` and
  `:825-833` do `os.walk` over each entry), so `("tests",)` /  `"tests"` would
  package `tests/roster/` too and violate D7 while AC7 still passed. Use
  `("tests", "conformance")` and the source-flavour equivalent.
- `Makefile` — add the root tree to the test target and to `SAST_DIRS`, or record
  the decision not to. `SAST_DIRS := tools packs packages` means a root `tests/`
  is outside Bandit and Semgrep entirely; `bandit.yaml`'s glob is not the
  mechanism and editing it would achieve nothing.
- `build-check.yml` — run the new tree, **and** add a `STEP_DISPOSITION` entry
  in `tools/lint-ci-parity.py` naming the `make` target that covers it locally.
  That gate is keyed by step name and fails on any added, renamed, or removed
  step in an in-scope workflow, so a bare step addition reddens it (AC11b).

The `Makefile` enumerates suites by explicit path with no globbing — `tools/`
tests are listed module by module, and only three pack suites run. So T4's
relocations into `tools/` and `packs/<pack>/tests/` need their own enumeration
edits here, or the relocated tests are never collected again (AC11).

Heed the `Makefile`'s existing warning about duplicate test basenames:
consolidating modules from three roots into one tree can collide, and pytest
refuses duplicates outright.

### T3 — Extract conformance classes from mixed modules

- **Implements:** AC1, AC4 (Testing Strategy: goal-based, integration surface)
- **Depends on:** T1, T2

**Tests:**

- Both halves green: the engine module after extraction, and the extracted
  classes in `tests/conformance/`.
- No module under `packages/agentbundle/tests/` resolves the live `packs/` tree
  to assert about its content, except under `tests/live-catalogue/` — the
  carve-out for engine tests that merely *borrow* a pack as input (AC1, AC9b).

**Approach:**

Three known instances, all in `tests/build_pipeline/` (formerly `agentbundle/build/tests/`), and the mapping warns to expect
more in the other roots:

- `test_adapter_gemini.py` — `GeminiShippedAgentToolCoverageTests` (sweeps
  `packs/*/.apm/agents/*.md`) and `GeminiAllPacksAdmissibleTests` (sweeps every
  `pack.toml`).
- `test_plugin_manifest_schema.py` — `SourcePluginJsonAuditTests` (globs
  `packs/*/.claude-plugin/plugin.json`).
- `test_shared_libs_projection.py` — `RealTreeInvariantTests` (globs
  `packs/*/.apm/skills/*/scripts/*.py`).

Extract the class, not the module. Watch for shared module-level setup the
extracted class depends on — that is the cost of class-level granularity and the
reason the alternative was considered.

These sweeps are already rule-shaped, so they seed the shipped conformance suite
rather than needing to be written.

### T4 — Relocate by owner

- **Implements:** AC1, AC3, AC5, AC11 (Testing Strategy: goal-based)
- **Depends on:** T1, T2, T3

**Tests:**

- Every suite green from its new home.
- No test in `tests/conformance/` names a specific pack.

**Approach:**

Rule-shaped → `tests/conformance/`; roster-shaped → `tests/roster/`, marked
non-shipping; pack-owned → `packs/<pack>/tests/`; tools-owned → `tools/`. Engine
tests stay put.

Roster-shaped tests are relocated and marked, **not** rewritten — rewriting them
into rules is a named follow-up. Rewrite only where it is trivial and obviously
correct.

The three tools-owned modules are `test_lint_agents_md_{diataxis,legacy,risk}_block.py`.
They import no engine code and test `tools/lint-agents-md.py`.

Path anchors change again for every relocated module, and the depth differs per
destination.

**Every destination needs a runner edit, because nothing globs.** The `Makefile`
lists `tools/` test modules by name and runs only three pack suites;
`build-check.yml` wires each pack suite by explicit path. A relocation into
`tools/` or into a `packs/<pack>/tests/` tree that is not already enumerated
leaves those tests permanently uncollected — green by absence (AC11).

### T5 — Ship the conformance suite through all three channels

- **Implements:** AC6, AC8 (Testing Strategy: goal-based, end-to-end)
- **Depends on:** T2, T4

**Tests:**

- `agentbundle catalogue init` into a temp directory, then run the materialised
  suite against the scaffolded catalogue: default preset, and
  `--preset self-hosted` in both `--tooling` modes.
- A suite that fails there is not portable, and the task is not done.

**Approach:**

The default preset and `--preset self-hosted` share no code, so each needs its
own wiring, in two different files:

- **Self-hosted** — `catalogue_tooling/initialise_self_hosted.py`'s in-memory
  content-plan block (near the pack and guide copies at `:807-845`) gains a call
  that collects `tests/conformance/` from the source catalogue. There is no such
  call site today.
- **Default preset** — `commands/catalogue_init.py`'s `_run_plain` path
  materialises the bundled scaffold via `scaffold.py`, so the work is the
  template plus its `_SYNC_PAIRS` entry in
  `tools/catalogue/sync_authoring_scaffold.py`. Without that entry the file gets
  no manifest hash, `list_files_with_hashes()` never yields it, and it is
  silently never materialised — surfacing only as a non-blocking INFO.

Each selected pack's `tests/` already ships through the self-hosted path today;
that needs no work, only to survive the engine spec's exclusion edit, which is
why that edit was scoped to the two vendored call sites.

### T6 — The sdist graft and the gate's presence half

- **Implements:** AC9, AC9b, AC10 (Testing Strategy: TDD)
- **Depends on:** T3, T4

**Tests:**

- A failing test first: extract a built sdist and **run** its suite. While
  catalogue assertions remain in the engine tree this fails on a missing
  `packs/` path — that failure is the point, and it is why the graft waited for
  this spec. Collect-only is not enough: a borrowing module collects fine and
  fails at run time.
- After: the suite runs green from the extracted copy, and the tree includes
  non-`.py` fixtures.
- `packages/agentbundle/tests/live-catalogue/` is absent from the built sdist.

**Approach:**

Add `MANIFEST.in` with an explicit `graft` of the engine test tree, including its
fixtures — `package-data` does not carry them, which is a second independent
reason today's shipped tests cannot run — **plus a `prune` of
`packages/agentbundle/tests/live-catalogue/`**. A `graft` is unconditional, so
any engine test still borrowing the live catalogue would otherwise ship and fail
at run time. Emptying `live-catalogue/` is this spec's exit condition and its
contents at ship time are the recorded remaining debt (AC9b).

Three traps: `MANIFEST.in` is order-dependent, so a `global-exclude` before a
`graft` does not apply to grafted files; a stale `.egg-info/SOURCES.txt` makes
setuptools reuse the old file list so edits silently do not take effect; and
`include_package_data = True` would promote the grafted tree into the wheel and
invert the rule. The package sets it nowhere today and must not start.

Extend `tools/check-artifact-contents.py` with the presence mode: extract and
collect, never count files. Presence-by-count is what let today's unrunnable
8-file slice look acceptable.

## Risks

- **The classification gets done with a grep because it is large.** This is the
  failure the whole spec exists to prevent. Mitigated by T1 producing a recorded
  owner per module as its deliverable, reviewable in the diff.
- **Extraction separates a class from shared setup and quietly weakens it.**
  Mitigated by requiring both halves green, and by treating a class that cannot
  be cleanly extracted as a contested call rather than forcing it.
- **The shipped suite is roster-shaped in practice and every adopter starts
  red.** Mitigated by T5's scaffold-and-run check, which cannot be satisfied by
  inspection.
- **Relocation re-enters an artifact** if this spec lands before the engine
  boundary. Mitigated by the ordering constraint.
- **`SAST_DIRS` silently leaves shipped code unscanned.** `tests/conformance/`
  ships to adopters; inheriting the default scan roots means it is never
  scanned. AC12 forces the decision rather than the default.

## Changelog

- **2026-08-08** — Initial plan, from RFC-0082 as Accepted and ADR-0075.
  Extraction (T3) is a first-class task rather than a footnote: applying the
  taxonomy to real code showed the rule-shaped material lives inside engine
  modules as classes, so the shipped suite is assembled by extraction rather
  than relocation. Roster rewriting is deliberately excluded and named as a
  follow-up.
