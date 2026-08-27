# Plan: OKF follow-ons

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** RFC-0087 D2/D4/D6/D7;
  `ARCHITECTURE.md` pack-source ownership;
  `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`;
  `packs/catalogue-curation/tests/skills/compile-okf/test_render.py` and
  `test_apply.py`; `packs/core/okf/security-checklists/index.md` plus production
  OKF discovery tests. Deviation: the user explicitly authorized the shipped
  predecessor-spec edit that `docs/CONVENTIONS.md` otherwise freezes.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence changes while its
> status is `Drafting` or `Executing`.

## Approach

Deliver two independently reviewable pack units. The catalogue-curation unit
first adds exact-byte hostile metadata coverage, then implements one small
display-field helper and adds a mutation-proven `OKF012` construction test before
performing its release bump. The architect unit then repairs the authored OKF
root, recompiles only generated output, and performs its own release bump. Run
focused gates per unit, then the repository CI chain, security/adversarial
review, finding adjudication, and quality review over the integrated intent.

## Constraints

- RFC-0087 keeps compilation deterministic and offline, compiler output
  confined, knowledge metadata inert, the diagnostic registry fixed, and the
  source bundle root hand-authored.
- ADR-0093 keeps the shipped OKF surface reference-only and same-pack.
- Pack source and release coupling follow `packs/AGENTS.md` and
  `packs/AGENTS.local.md`; generated self-host or router projections are updated
  only by their owning commands.
- The managed profile permits repository file writes but no Git index/ref
  writes, so commits, PR creation, and merge are a supported-profile handoff.

## Construction tests

- **Integration tests:** production discovery for all three managed packs;
  `agentbundle show architect --format json`; architect compilation followed by
  `tools/check-okf-managed-packs.py`; pack/plugin/changelog parity.
- **Manual verification:** inspect the pre-fix exploit index and the fixed
  exact-byte hostile fixture; inspect `git diff` to confirm no source-root or
  unrelated generated write.

## Pre-EXECUTE gates

- The `security-reviewer` runs in secure-design mode over the untrusted
  metadata/index-rendering boundary with the injection, path-and-file,
  llm-agent, and agentic-skills checklists inlined. Its report and the
  adversarial spec/plan report each pass through independent finding
  adjudication and return `Clean — ready to commit.` before T1 begins.

## Design (LLD)

### Design decisions

- A private compiler helper applies AC1's canonical bound and contextual
  Markdown encoding to every metadata display-field value. Path-derived index
  display text uses the same escaping, while canonical link destinations are
  URL-encoded without changing their source-path sort keys. Traces to AC1–AC3.
- Escaping preserves the existing success/diagnostic contract and keeps hostile
  metadata inert without opening the closed registry. Rejecting metadata was
  declined because it changes exit behavior and requires diagnostic ownership.
- The two pack units share this spec but remain separable by pack ownership,
  release metadata, focused verification, and review target. Traces to AC8–AC9.

### State & control flow

- `compile_pack` renders each declared bundle twice before any output
  application; unequal `files` returns `OKF012` at exit 2. The construction test
  snapshots the entire synthetic catalogue before invocation and compares it
  afterward. Traces to AC4–AC5.

### Behavior & rules

- Human-readable metadata fields are escaped and capped. Path-derived directory
  display text is escaped, canonical filename and directory destinations are
  URL-encoded, and root-index entries are **changed** to sort by normalized
  source path rather than by rendered line bytes. That is a conformance repair,
  not new scope: frozen `okf-authoring-projection` AC11 already requires every
  managed index to sort "entries by NFC-normalized POSIX relative-path bytes",
  which the previous rendered-bytes key violated. It is also load-bearing for
  this change — escaping the directory display text alters the rendered line, so
  a rendered-bytes key would make ordering depend on escaping (`concepts\(a\)`
  sorts after `concepts0` where raw `concepts(a)` sorts before it). The reorder
  is disclosed to adopters, with its recompile obligation, in the
  catalogue-curation release entry. The compiler therefore cannot fabricate a
  target or reorder entries from attacker-controlled data. Traces to AC1–AC3.
- Architect's source root declares discovery metadata and tells maintainers that
  generated output is emitted beneath the router and manifest paths, matching
  the core root's authored-source wording. Traces to AC6–AC7.

### Failure, edge cases & resilience

- AC1's input bound is applied before encoding so an escape sequence is never
  partially cut. Empty/falsy metadata keeps the
  existing fallback behavior. Repeated escaping is not applied because source
  metadata is rendered once per compile. Traces to AC1–AC2.
- The mutation verification changes the real guard only long enough to observe
  the new focused test fail, then restores the exact source bytes before any
  broader gate or review. Traces to AC5.

### Quality attributes (NFRs)

- Security: after display-field normalization no concept metadata value can
  choose a link target, add an index entry, or add a heading in compiler-owned
  output, and neither `\r` nor `\n` survives. This is link-and-entry-forgery
  scope, not display fidelity: the confirmed escape set covers link and newline
  delimiters only, so the three display-integrity residuals recorded in the
  spec's Assumptions — GFM autolinks, exotic line separators, and code-span
  swallow — remain open under *Ask first*. Traces to AC1–AC3.
- Determinism: normalization is pure and the repeated-render mismatch retains a
  mutation-sensitive test. Traces to AC4–AC5.
- Maintainability: release tests assert cross-file invariants rather than
  pinning version literals. Traces to AC8.

## Tasks

### T1: Hostile index metadata remains bounded data

**Depends on:** none

**Touches:** `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`, `packs/catalogue-curation/.apm/skills/compile-okf/evals/evals.json`, `packs/catalogue-curation/.apm/skills/compile-okf/evals/files/catalogue/packs/demo/okf/demo/concepts/hostile-title.md`, `packs/catalogue-curation/tests/skills/compile-okf/fixtures/render/rich/concepts/hostile-title.md`, `packs/catalogue-curation/tests/skills/compile-okf/test_render.py`, `docs/specs/okf-authoring-projection/spec.md`

**Verification mode:** TDD.

**Tests:**

- Add a compilable red exact-byte assertion for the hostile-title fixture that
  covers title injection, plus an exact generated-entry assertion whose title,
  status, and non-string type collectively cover AC1's complete bound,
  coercion, and encoding contract (AC1–AC2; `stub: true`).
- Assert the generated root concept count and complete concepts index bytes so
  an extra entry or altered filename target cannot hide behind substring checks
  (AC2; `stub: true`).
- Assert the percent-encoded destination for a concept filename carrying an HTML
  character reference and for one carrying a space, proving a source path cannot
  render an attacker-chosen `href` (AC1; `stub: true`).
- Extend the shipped compile-okf eval with a hostile-title input and require the
  agent to inspect and report the single escaped canonical index entry (AC2).
  The eval grades the canonical entry through its semantic assertion and the
  negative `output_excludes` string only; the exact escaped line is not a
  deterministic post-condition because `output_contains` is matched against
  captured run output, so requiring it would fail an agent that summarises the
  index rather than quoting it.

**Approach:**

- Add one `_index_display_value` helper and apply it independently to title,
  status, and type before interpolation.
- Restore the fabricated-source-path clause in predecessor AC17 and remove its
  temporary boundaries paragraph under the confirmed convention exception.

**Done when:** The red fixture becomes green, the isolated exploit cannot emit a
second link target or physical newline, and predecessor AC17 remains checked.

### T2: Removing the repeated-compile distinction fails a focused test

**Depends on:** T1

**Touches:** `packs/catalogue-curation/tests/skills/compile-okf/test_apply.py`, `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py` (temporary mutation only)

**Verification mode:** TDD plus mutation verification.

**Tests:**

- Monkeypatch `render_okf_bundle` to return differing `files` on its second call,
  assert `exit_code == 2`, diagnostic codes exactly `["OKF012"]`, and the
  synthetic catalogue snapshot remains unchanged (AC4; `stub: true`).
- Temporarily replace the real second render with `second = first`, run only the
  new test and record its assertion failure, restore the real code, then rerun
  green (AC5).

**Approach:**

- Reuse `_make_catalogue` and `_snapshot`; construct the differing immutable
  render result with `dataclasses.replace` so the test exercises `compile_pack`
  without coupling to unrelated renderer details.

**Done when:** The focused test is green normally, red under the guard-removal
mutation, green again after restoration, and no final compiler mutation remains.

### T3: Catalogue-curation release metadata follows invariant-shaped tests

**Depends on:** T1, T2

**Touches:** `packs/catalogue-curation/pack.toml`, `packs/catalogue-curation/.claude-plugin/plugin.json`, `packs/catalogue-curation/tests/pack/test_compile_okf_pack.py`, `docs/product/changelog.md`

**Verification mode:** TDD plus goal-based release checks.

**Tests:**

- Replace both `0.4.2` assertions with pack/plugin parity and a topmost
  catalogue-curation changelog-heading assertion (AC8; `stub: true`). The
  construction stub temporarily asserts the requested 0.4.3 target to earn
  red; EXECUTE removes that temporary literal while retaining both invariants.
- Run catalogue-curation's focused skill and pack tests (AC8–AC9).

**Approach:**

- Bump catalogue-curation to 0.4.3 and add a free-standing release entry with a
  consumer-outcome `Highlights` subsection because generated indexes become
  safe to traverse with hostile metadata.

**Done when:** Generic parity and the 0.4.3 topmost changelog heading pass with
no literal version assertion.

### T4: Architect is discoverable without treating its source root as generated

**Depends on:** T1

**Touches:** `packs/architect/okf/architecture-lenses/index.md`, `packs/architect/.apm/skills/architecture-lenses-reference/**`, `packs/architect/.okf-generated.json`, `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, `packs/architect/tests/pack/test_architecture_lenses_corpus.py`, `tests/roster/test_okf_catalogue_discovery.py`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`

**Verification mode:** TDD plus manual CLI QA and goal-based generated-output
checks.

**Tests:**

- Run production discovery for core, architect, and cost engineering; invoke
  `agentbundle show architect --format json` (AC6).
- Exercise architect through the public `show.run` JSON/schema roster test and
  assert its licensed architecture-lenses knowledge record (AC6).
- Compile architect, inspect the source root remains authored, and run
  `tools/check-okf-managed-packs.py` (AC7).
- `test_architect_version_is_synchronized` in the architect pack suite verifies
  pack/plugin parity, and `test_okf_pack_releases_name_themselves_in_the_topmost_changelog_heading`
  in `tests/roster/test_okf_catalogue_discovery.py` verifies the topmost
  changelog heading for both released packs (AC8; `stub: true`). The changelog
  leg lives in the roster suite, not in either pack suite, because
  `tools/lint-pack-test-boundary.py` forbids a pack test from reading above its
  own pack and `docs/product/changelog.md` is repository-level. The construction
  stub temporarily asserts the requested 0.15.3 target to earn red; EXECUTE
  removes that temporary literal while retaining both invariants.

**Approach:**

- Add the shared content licence and rewrite the body from the core model to
  describe canonical authored input and generated router traversal.
- Compile through the source-owned compiler, bump architect to 0.15.3, and add
  a free-standing release entry. Include `Highlights` because users regain
  `agentbundle show` discovery for the shipped pack.

**Done when:** Architect discovery and show succeed, managed-pack checking is
clean, and only compiler-owned architect outputs plus release metadata change.

### T5: Both independently reviewable units satisfy repository gates

**Depends on:** T3, T4

**Touches:** all files named by T1–T4 plus `docs/specs/okf-follow-ons/**`, `docs/specs/README.md`, and `workspace.toml`

**Verification mode:** Goal-based integration checks and review.

**Tests:**

- Run focused OKF suites, pack tests, lint, typecheck, `lint-spec-status`, and
  `SKIP_SAST=1 make ci` as one chain; record SAST as incomplete rather than
  locally green (AC9).
- Run security review for untrusted metadata, adversarial review for contract
  and implementation correctness, quality review for mutation strength and
  maintainability, and adjudicate each raw report before acting (AC1–AC9).

**Approach:**

- Review catalogue-curation and architect as separate pack units, then review
  the integrated spec. Apply only sustained findings, return through gates, and
  iterate mandatory full-mode reviewers to adjudicated clean.
- Move the three delivered follow-on entries from `[backlog].open` to
  `[backlog].closed` with closure rationale tied to this spec.

**Done when:** Every AC is checked, every mandatory review is adjudicated clean,
the full non-SAST local gate chain passes, and the diff is ready for supported
Git/PR operations.

## Rollout

- **Delivery:** Two independently reviewable pack releases: catalogue-curation
  0.4.3 for compiler safety and guard coverage, architect 0.15.3 for discovery.
  No feature flag or migration is required; reverting each unit restores its
  prior behavior and version metadata.
- **Infrastructure:** None.
- **External-system integration:** None; compilation and discovery remain local
  and offline.
- **Deployment sequencing:** Land catalogue-curation first because it closes the
  security boundary and supplies the compiler used to regenerate architect.
  Architect may then land independently without a source dependency on the
  catalogue-curation pack.

## Risks

- A cap applied after escaping could split an escape sequence; the design caps
  input first and exact bytes pin the result.
- A hostile value could remain safe in link text but break trailing prose; the
  same normalizer covers title, status, and type.
- A mock-shaped `OKF012` test could bypass `compile_pack`; the test patches only
  the renderer seam and drives the real compiler entry point plus mutation.
- Manual compilation may create bytecode or stale generated files; inspect the
  diff, remove only task-created caches from approved targets, and rely on
  compiler ownership checks before broader gates.

## Changelog

- 2026-08-25: Initial plan authored from the three confirmed PR #1130
  follow-ons, with two pack release units and an explicit predecessor-spec
  exception.
- 2026-08-26: Pre-EXECUTE adjudication expanded AC1 to cover Markdown
  escape-control and HTML/autolink delimiters, made the secure-design gate
  explicit, materialized T1/T2 construction stubs, and named architect's
  release-metadata test.
