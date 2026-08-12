# Plan: Governance guide reference cleanup

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Build the guard from its black-box CLI contract first, then use it to inventory and scrub the shipped guides. Keep deterministic checks mechanical: parse Markdown link destinations and textual governance tokens line by line, derive real spec slugs from `docs/specs/`, and apply one narrow inline suppression rule. Review every candidate spec slug against the task's rubric so pending records the tool cannot know about are still removed. Migrate the same scrub-touched guides to required frontmatter, removing their transitional navigation-baseline entries. Wire the clean guard into documentation CI and run the complete requested gate sequence.

## Constraints

- New `tools/` code is pure-stdlib Python and introduces no dependency.
- Only the file surfaces named in the spec Boundaries are writable for this change; `tools/lint-plugin-route-docs.py` is included only to align an existing `build-check` guide assertion with the deprecated-stream rename.
- The guard is a regression fence for real spec directories, not a substitute for human judgment about pending specs.
- Guide prose continues to follow `guides/AGENTS.md`; no new guide or navigation structure is introduced.
- The existing user-owned `.codex/config.toml` modification is unrelated and remains untouched.

## Construction tests

**Integration tests:** run the lint CLI as a subprocess against temporary `guides/` and `docs/specs/` fixture trees, then run it against the repository's real `guides/` tree.

**Manual verification:** review pending-spec candidates and the named kept examples; inspect changed Markdown for empty targets, orphaned labels, and damaged prose.

## Design (LLD)

### Design decisions

- Keep one repository-only CLI script rather than adding a reusable package; it has one caller surface and no second consumer requiring an abstraction. Traces to AC1–AC6.
- Match real spec slugs from the repository root inferred from the script location when scanning the default tree, and from the fixture root inferred from `--guides-root` when tests provide a sibling `docs/specs/`. Canonicalize each allowed root, refuse symlink or junction directories before descent, record resolved directories before processing, and reject resolved children outside their root. Traces to AC1 and AC4.
- Emit one diagnostic per violating line and reason, in stable path order, so CI output stays actionable without defining a machine-readable format. Traces to AC2–AC6.

### Behavior & rules

- Link detection examines Markdown inline-link and reference-definition destinations and classifies normalized slash-delimited path segments; changelog matching is case-insensitive.
- Token detection uses the exact two-to-four-digit ADR/RFC boundary from the contract.
- Spec citation detection excludes angle-bracket placeholders before comparing the first slug segment with the runtime directory set.
- Allow markers suppress all reasons on their own line or the immediately following line and carry a human-readable reason.

### Failure, edge cases & resilience

- A missing or escaping guides/spec root is a usage error rather than a false clean scan; resolved files and spec directories must remain under their canonical allowed root.
- Recursive guide discovery refuses symlink and junction directories before descent and records each resolved directory before processing so cycles and aliases fail closed.
- Catch `OSError` and `RuntimeError` from path resolution and fail closed with a concise diagnostic.
- Files are decoded as UTF-8 and scanned deterministically; malformed input surfaces as a concise CLI error.
- Pending spec slugs remain a documented limitation and are handled by the one-time judgment scrub.

### Dependencies & integration

- The tool uses only Python's standard library (`argparse`, `dataclasses`, `os`, `pathlib`, `re`, and `sys`).
- `.github/workflows/docs.yml` calls the script directly and reruns when the shipped guides or guard change.

## Tasks

### T1: The guard's black-box contract passes for forbidden and preserved references

**Depends on:** none

**Touches:** tools/lint-guides-no-repo-only-refs.py, tools/test_lint_guides_no_repo_only_refs.py

**Verification mode:** TDD

**Tests:**
- `tools/test_lint_guides_no_repo_only_refs.py` invokes the absent CLI against fixture trees and asserts each `adr`, `rfc`, `specs`, and changelog link class fails with line-addressed output (AC2).
- The same test file asserts an `RFC-0071` token and a citation matching a fixture `docs/specs/real-record/` directory fail (AC3–AC4).
- Passing cases cover `spec/plan`, `spec/loop`, `spec/slice`, `docs/specs/<feature>/`, `work-loop docs/specs/<slug>/`, and absent `docs/specs/webhook-retries/` (AC4).
- Escape markers on the same and immediately preceding lines, `--help`, clean output, and exit codes are asserted through the CLI (AC1, AC5–AC6).
- Symlinked guide files, guide directories, and spec directories are rejected; cycle/junction traversal and resolution errors fail closed (AC1).
- `stub: true` — the compilable red test file is materialized during PLAN with `# STUB: AC1-AC6`; it fails because the CLI does not yet exist.

**Approach:**
- Implement the smallest line-oriented scanner satisfying the red CLI tests.
- Keep rule reasons distinct and deterministic; document the escape hatch and pending-spec limitation in the module header.

**Done when:** `python -m pytest tools/test_lint_guides_no_repo_only_refs.py -q` passes and a direct clean fixture invocation prints the exact AC6 message.

### T2: Shipped guides contain no Type-A or deprecated-stream references

**Depends on:** T1

**Touches:** guides/**/*.md

**Verification mode:** goal-based check + manual QA

**Tests:**
- `no stub (goal-based)` — the new guard exits 0 against the real `guides/` tree (AC7).
- `no stub (manual QA)` — focused searches and line-by-line review confirm pending real citations are gone and all named kept cases remain unchanged (AC7).
- `no stub (goal-based)` — `user-guide-diataxis` is absent from `guides/`, while `product-documentation` is present at each replacement site (AC8).

**Approach:**
- Inventory all mechanical candidates, classify spec-slug judgment cases against real directories and authority language, and patch only the Type-A pointer or citation clause.
- Delink or repoint deprecated-stream references without touching the compatibility pack.

**Done when:** the real guard is clean, focused searches show no stale stream name, and manual review records which real/pending spec citations were removed versus which examples were retained — recorded in [`notes/scrub-judgment.md`](notes/scrub-judgment.md).

### T3: Documentation CI runs the guard whenever its inputs change

**Depends on:** T1

**Touches:** .github/workflows/docs.yml

**Verification mode:** goal-based check

**Tests:**
- `no stub (goal-based)` — workflow inspection confirms a direct `python3 tools/lint-guides-no-repo-only-refs.py` step and both required pull-request path filters (AC9).
- `no stub (goal-based)` — `SKIP_SAST=1 make build-check` accepts the workflow and full catalogue gate chain (AC9–AC10).

**Approach:**
- Add the two path triggers beside the existing documentation/tool triggers.
- Add one named run step in the documentation job that owns guide validation, matching direct-Python invocation style.

**Done when:** all three workflow strings are present and the build gate passes.

### T4: The integrated documentation and lint surface is clean

**Depends on:** T2, T3, T5

**Verification mode:** goal-based check + manual QA

**Tests:**
- `no stub (goal-based)` — run every command in the task's Verify block without filtering output (AC10).
- `no stub (manual QA)` — inspect the diff for empty `]()` destinations, orphaned link labels, and damaged sentences (AC10).

**Approach:**
- Run narrow gates first, then guide validators, related regression suites, and finally the build-check chain.
- Fix implementation or guide content rather than weakening the guard or its tests.

**Done when:** every requested command exits 0 and the Markdown inspection is clean.

### T5: Every scrub-touched guide carries valid frontmatter

**Depends on:** T2

**Touches:** the 19 guide files changed by T2, guide-nav-baseline.toml

**Verification mode:** goal-based check + manual QA

**Tests:**
- `no stub (goal-based)` — `python tools/validate_guides.py` reports no errors for the migrated pages (AC11).
- `no stub (goal-based)` — the guide-site regression suite confirms frontmatter-driven labels do not regress navigation (AC11).
- `no stub (manual QA)` — the migrated guide set exactly matches the scrub-touched guide set, and each page's title, summary, pack, and kind match its content and location (AC11).

**Approach:**
- Add the four required schema fields above each changed guide without changing its visible H1.
- Remove each matching transitional entry that exists in `guide-nav-baseline.toml`.

**Done when:** all 19 touched guides validate with frontmatter and none retain a navigation-baseline entry.

## Rollout

The scrub and CI guard ship atomically in one reversible repository change. There is no deployment, data migration, infrastructure, feature flag, or external-system sequencing.

## Risks

- Regex-only Markdown parsing can miss exotic destination syntax or overmatch prose; black-box cases pin the requested syntax and manual diff review covers the edited corpus.
- A real spec citation may use a slug whose directory does not exist yet; the header names this limitation and the one-time human scrub handles known pending citations.
- Mechanical removal can damage teaching prose; changes remove only pointer clauses and retain surrounding explanation.
- Existing CI path filters currently name only `guides/AGENTS.md`; the new broad guide trigger intentionally expands documentation-job coverage.

## Changelog

- 2026-08-12: Initial full-mode plan.
- 2026-08-12: Added the user-authorized frontmatter migration for the scrub-touched guides and required navigation-baseline cleanup.
- 2026-08-12: Added reference-style Markdown link coverage after adversarial review and aligned CI verification wording.
- 2026-08-12: Added a narrow existing route-docs lint assertion update after `build-check` still required `user-guide-diataxis` in `install-routes.md`.
- 2026-08-12: Recorded the adopter-visible guide change in `docs/product/changelog.md` and widened the spec's `docs/` boundary to authorize it (AC12).
- 2026-08-12: Wrote the T2 spec-slug judgment record the Done-when required; it was the loop's one unwritten artifact.
- 2026-08-12: Added reference-style Markdown link coverage after adversarial review and aligned CI verification wording.
