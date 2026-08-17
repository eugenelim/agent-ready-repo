# Plan: Docs-site build contract hardening

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Pin the false token dependency with a construction fixture before deleting it,
then give the pure rehype transform a focused Node built-in test suite. Wire
that suite into required site CI through the existing workflow construction
contract. Finish with the canonical combined build and emitted table, route,
link, fragment, contrast, and Starlight-behavior evidence.

## Constraints

- RFC-0089 owns the sibling-renderer and ordered single-artifact boundary.
- Implementation does not begin until RFC-0089 is Accepted.
- `docs-site/AGENTS.md` owns the independent palette and pinned Starlight
  touchpoints.
- Existing rendered-output coverage remains required integration evidence.
- Use Node's built-in test runner under Node 24; add no package or lockfile
  dependency.

## Construction tests

**Integration tests:** run generation without a token source in an isolated
fixture, then build marketing first and docs second and exercise emitted table,
route, link, fragment, contrast, and pinned-control checks.

**Manual verification:** none beyond the browser and physical-device evidence
owned by `site-browser-quality-gate`; this spec's behavior is deterministic.

## Design (LLD)

### Design decisions

- Remove the vestigial copy and false failure instead of preserving a no-op
  compatibility file. Traces to: AC1-AC3.
- Test the pure transform directly with `node:test`, while preserving the
  existing all-pages output assertion. Traces to: AC4-AC8.

### Dependencies & integration

- The generator remains stdlib Python. Plugin tests consume only Node built-ins
  plus the plugin's already declared runtime import. Required site CI runs the
  focused command after package installation and before deployment. Traces to:
  AC2, AC4, AC7.

### Interfaces & contracts

- `npm run test:plugins --prefix docs-site` is the focused local/CI entry point.
  Its exit code is blocking. Traces to: AC4, AC7.
- The table wrapper contract remains `.table-scroll`, `tabIndex=0`,
  `role=region`, and a unique contextual `aria-label`. Traces to: AC5, AC6,
  AC8.

### Failure, edge cases & resilience

- A table without a writable parent is left unchanged rather than raising.
- A table already inside the plugin's wrapper is not nested again.
- Repeated heading-derived labels are numbered within one document and the
  counter resets for the next transformer invocation. Traces to: AC5, AC6.

## Tasks

### T1: Generator construction tests reject the vestigial token dependency

**Depends on:** none

**Touches:** tools/test_build_site_routing.py, tools/build-site.py

**Tests:**
- TDD: run generation in an isolated fixture with no marketing token file and assert
  success plus absence of a docs token copy (AC1, AC2).
- TDD: seed a reintroduced read/copy/failure branch and prove the fixture fails
  (AC1, AC2).

**Approach:**
- Extend the existing generator test harness rather than asserting only on
  source text.
- Observe file reads/writes and process outcome at the generation boundary.

**Done when:** the new construction test fails against the current copy/error
contract and passes only when generation is independent of both token paths.

### T2: Generation and docs guidance have no marketing-token dependency

**Depends on:** T1

**Touches:** tools/build-site.py, docs-site/AGENTS.md

**Tests:**
- Goal-based: run the focused generator tests and verify no generated docs token appears
  (AC1-AC3).
- Goal-based: run generation and the docs contrast checker from a normal checkout (AC2,
  AC9).

**Approach:**
- Remove the docstring claim, copy operation, and false missing-source error.
- Correct only the stale token-copy wording in docs-site guidance.

**Done when:** generation succeeds without either token path and living guidance
matches the self-contained palette contract.

### T3: The rehype table transform has mutation-sensitive built-in unit tests

**Depends on:** none

**Touches:** docs-site/package.json, docs-site/src/plugins/rehype-scrollable-tables.test.ts

**Tests:**
- TDD: cover wrapping, idempotence, missing parent/index, nested heading text,
  duplicate labels, and per-document reset (AC5).
- TDD: mutate each accessibility attribute and wrapper guard to prove a focused test
  fails (AC6).

**Approach:**
- Construct minimal typed HAST fixtures with Node strict assertions.
- Expose one `test:plugins` script that invokes `node --test` for the focused
  TypeScript test file under Node 24's built-in type stripping.

**Done when:** the clean suite passes with no added dependency and each seeded
mutation is caught.

### T4: Required site CI blocks on plugin unit-test failure

**Depends on:** T3, spec:site-ci-contract-closure/T3

**Touches:** .github/workflows/pages.yml, tools/test_*.py

**Tests:**
- TDD: extend the workflow construction test to require the focused command, correct
  ordering, blocking failure behavior, and path-filter ownership (AC7).
- Goal-based: seed a failing plugin test and prove the workflow-equivalent command exits
  non-zero before deployment (AC6, AC7).

**Approach:**
- Reuse the site CI construction-test mechanism rather than add another
  workflow parser.
- Run the command after the existing docs dependency install and before build
  artifact upload/deployment.

**Done when:** construction tests and the local workflow-equivalent command
prove the focused suite cannot be skipped or tolerated.

### T5: Combined emitted docs behavior remains unchanged

**Depends on:** T2, T4

**Touches:** web/src/test/rendered-output.test.ts, tools/test_check_rendered_site_links.py

**Tests:**
- Goal-based: run the canonical generator, marketing build, and docs build; assert every
  emitted Markdown table retains the focusable wrapper contract (AC8, AC9).
- Goal-based: run route, page/fragment, contrast, and pinned Starlight-control checks (AC9,
  AC10).

**Approach:**
- Keep integration assertions behavior-based and run them after both renderers
  have emitted the combined artifact.
- Compare the existing route inventory and docs palette tokens before and after
  the change.

**Done when:** all focused, workflow-construction, build, emitted-output, link,
fragment, contrast, route, and pinned-control checks pass.

## Rollout

Land generator decoupling and plugin tests before requiring the new CI command.
The final change ships atomically with the blocking workflow step. Rollback is
a normal source revert; there is no data, dependency, or infrastructure
migration.

## Risks

- Node's TypeScript execution contract could be invoked with flags inconsistent
  with CI; the focused package command and workflow construction test pin one
  entry point.
- Unit fixtures can diverge from actual Starlight output; the existing all-page
  emitted assertion remains the second layer.

## Changelog

- 2026-08-17: initial plan after RFC-0089's direction and the built-in runner
  decision were confirmed; implementation remains blocked on RFC acceptance.
