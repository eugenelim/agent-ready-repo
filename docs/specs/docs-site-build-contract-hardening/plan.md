# Plan: Docs-site build contract hardening

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Pin the false token dependency with a construction fixture before deleting it,
then give the pure rehype transform a focused Node built-in test suite. Wire
that suite into the DEPLOY workflow, and pin its posture from a required context
through a workflow construction contract. Finish with the canonical combined build and emitted table, route,
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
  plus the plugin's already declared runtime import. The DEPLOY workflow runs the
  focused command after package installation and before artifact upload; required CI
  runs only the posture check that pins that arrangement. Traces to:
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
- TDD (`stub: true`): run generation in an isolated fixture with no marketing token
  file and assert success plus absence of a docs token copy (AC1, AC2).
- TDD (`stub: true`): seed a reintroduced read/copy/failure branch and prove the
  fixture fails (AC1, AC2).

**Approach:**
- Isolation mechanism, named because it is not obvious: `REPO_ROOT` in
  `tools/build-site.py` is module-level, and the token copy lives inline in
  `main()`, so calling `main()` in-process would read the real
  `web/src/styles/tokens.css` and write into the real
  `docs-site/src/content/docs/`. Instead copy `build-site.py` plus `site.toml`
  into a temp tree and run it as a SUBPROCESS there, which makes `REPO_ROOT` the
  fixture. Measured on the current script: it exits 1 with
  `error  web/src/styles/tokens.css missing`, which is the red state T1 pins.
- Host the test in `tools/test_build_site_routing.py`, which is already wired
  into the Makefile test target and `gate-main` — note it calls individual
  functions (`mirror_guides`) and never `main()`, so this adds the first
  subprocess case there rather than extending an existing one. Update its
  docstring test count in the same edit.
- Observe file reads/writes and process outcome at the generation boundary.

**Done when:** the new construction test fails against the current copy/error
contract and passes only when generation is independent of both token paths.

### T2: Generation and docs guidance have no marketing-token dependency

**Depends on:** T1

**Touches:** tools/build-site.py, docs-site/AGENTS.md, docs-site/.gitignore, .gitignore

**Tests:**
- Goal-based (`no stub (mode)`): run the focused generator tests and verify no
  generated docs token appears (AC1-AC2).
- Goal-based (`no stub (mode)`): no living-guidance file still claims generation
  copies marketing tokens, or that docs CSS imports them. Targets the CLAIM, not the
  substring: the corrected guidance legitimately still contains the string
  `tokens.css` inside its negation ("Nothing copies … and nothing imports it"), so a
  bare `! grep -q "tokens.css"` can never pass. The check is
  `! grep -qE "(still copies|tokens\.css copy|copy is vestigial|imports .*tokens\.css)"`
  over `docs-site/AGENTS.md`, `guides/AGENTS.md`, and `tools/build-site.py` (AC3).
- Goal-based (`no stub (mode)`): run generation and the docs contrast checker from
  a normal checkout (AC2, AC9).

**Approach:**
- Remove the docstring claim, copy operation, and false missing-source error.
- Correct the stale token-copy wording in docs-site guidance — TWO mentions, the
  styling section and the Development block. The file is 148 lines against a
  150-line CI cap, so the rewrite must be net-shortening; add no explanatory prose.
- `docs-site/.gitignore` ignores `src/styles/tokens.css`, a rule for a file nothing
  will generate once the copy is gone; remove it in the same change.
- `web/src/design-system.md` also claims Starlight imports `tokens.css` at build
  time. Already false today, and out of this task's concern — defer with a register
  entry rather than widen the diff.

**Done when:** generation succeeds without either token path and living guidance
matches the self-contained palette contract.

### T3: The rehype table transform has mutation-sensitive built-in unit tests

**Depends on:** none

**Touches:** docs-site/package.json, docs-site/src/plugins/rehype-scrollable-tables.test.ts, docs-site/src/plugins/rehype-scrollable-tables.ts, Makefile, AGENTS.md

**Tests:**
- TDD (`stub: true`): cover wrapping, a table nested in a blockquote/aside,
  idempotence, a root-level table with no parent or index, nested heading text,
  duplicate labels, and per-document reset (AC5).
- TDD (`stub: true`): mutate each accessibility attribute and wrapper guard to
  prove a focused test fails (AC6).
- Goal-based (`no stub (mode)`): `git diff` shows no change to
  `docs-site/package.json` dependencies or `docs-site/package-lock.json` (AC4).

**Approach:**
- Construct minimal typed HAST fixtures with Node strict assertions.
- Expose one `test:plugins` script invoking `node --test` on the focused
  TypeScript file, relying on built-in type stripping per the canonical
  `engines` floor. Import the plugin with an explicit `./rehype-scrollable-tables.ts`
  extension: `astro.config.ts` imports it extensionless, which Vite resolves and
  Node does not.
- Wire `npm run test:plugins --prefix docs-site` into the Makefile test target.
  Without it `make ci` stays green with a red plugin suite, which is the same
  orphan class the register tracks as `tools-test-runner-boundary`.
- Correct the plugin's own docstring, which says the config file has no test
  runner and cites a stale generated-page count — both false after this task.

**Done when:** the clean suite passes with no added dependency and each seeded
mutation is caught.

### T4: The deploy workflow blocks on plugin unit-test failure, and a required context pins it

**Depends on:** T3, spec:site-ci-contract-closure/T3

**Touches:** .github/workflows/pages.yml, tools/test-pages-workflow.py, Makefile, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:**
- TDD (`stub: true`): assert the focused command is present in the `build` job,
  ordered after the docs dependency install and before artifact upload, and not
  neutered; each proven by seeded deletion or reordering (AC7).
- TDD (`stub: true`): assert the `paths:` filters cover the plugin, the docs
  package/configuration, and the workflow itself — proven by seeded REMOVAL, since
  `pages.yml:5-12` already covers `docs-site/**` and the workflow, so a presence
  assertion would not detect a deletion (AC7).
- Goal-based (`no stub (mode)`): seed a failing plugin test and prove the
  workflow-equivalent command exits non-zero (AC6, AC7).

**Approach:**
- A NEW `pages.yml`-scoped posture module is required, and the "reuse rather than
  add another parser" instruction cannot be followed: `tools/test-build-check-workflow.py`
  is `build-check.yml`-shaped end to end — its `WORKFLOW` constant, its
  aggregator/`gate-*` job model, its pinned aggregator step roster — and
  `tools/lint-ci-parity.py` scopes `pages.yml` explicitly out. A second parser is
  accepted here because the two workflows have genuinely different job models.
- The new module must be wired somewhere or it runs nowhere: add it to the Makefile
  test target and to a `gate-main` step, the same failure `tools/test_build_site_dry_run.py`
  demonstrates (invoked by no target and no workflow, tracked as
  `tools-test-runner-boundary`). A new `gate-main` step also needs its
  `STEP_DISPOSITION` row in `tools/lint-ci-parity.py`, which fails closed otherwise.
- Update `lint-ci-parity.py`'s recorded reason for holding `pages.yml` out of scope
  once that workflow carries a blocking gate, mirroring the
  `release-agentbundle.yml` precedent.
- Run the command after the existing docs dependency install and before build
  artifact upload/deployment.

**Done when:** construction tests and the local workflow-equivalent command
prove the focused suite cannot be skipped or tolerated.

### T5: Combined emitted docs behavior remains unchanged

**Depends on:** T2, T4

**Touches:** docs/specs/README.md (status row, on shipping)

**Tests:**
- Goal-based (`no stub (mode)`): run the canonical generator, marketing build, and
  docs build, then `web/src/test/rendered-output.test.ts` — which already asserts
  the emitted table wrapper contract and is run by `pages.yml`'s `npm test --prefix web`.
  This task must NOT edit it: AC8 requires it to remain unchanged (AC8, AC9).
- Goal-based (`no stub (mode)`): route-set diff against the pre-change inventory
  (membership, not count — a rename preserves a count), plus
  `tools/check-rendered-site-links.py` and `tools/check-docs-contrast.py` (AC9).
- Goal-based (`no stub (mode)`): per-control Starlight checks — sidebar and
  pagination from `rendered-output.test.ts`'s existing assertions; title, search,
  and theme control by a diff-scope check showing no change to
  `docs-site/astro.config.ts`, `docs-site/src/components/**`, or
  `docs-site/src/styles/starlight.css` (AC10).

**Approach:**
- Keep integration assertions behavior-based and run them after both renderers
  have emitted the combined artifact.
- Capture the route inventory BEFORE the change; a post-change count alone cannot
  detect a rename.

**Done when:** all focused, workflow-construction, build, emitted-output, link,
fragment, contrast, route, and pinned-control checks pass.

## Rollout

Land generator decoupling and plugin tests before requiring the new CI command.
The final change ships atomically with the blocking workflow step. Rollback is
a normal source revert. Two local migrations DO apply, recorded here rather than
only in a PR description, which is not a durable home:
- Pre-existing worktrees keep an untracked `docs-site/src/styles/tokens.css` that
  nothing regenerates and nothing reads, because both ignore rules for it are gone:
  `rm -f docs-site/src/styles/tokens.css`. A stale copy of exactly this file is what
  made the first verification pass for the wrong reason.
- `make test` now requires `npm ci --prefix docs-site`; it fails with that remedy in
  the message rather than an `ERR_MODULE_NOT_FOUND`.

## Risks

- Node's TypeScript execution contract could be invoked with flags inconsistent
  with CI; the focused package command and workflow construction test pin one
  entry point.
- `node:test` has no type declarations in `docs-site` and AC4 forbids adding
  `@types/node`. Nothing typechecks `docs-site` in CI, so this is an accepted
  residual — recorded here so a missing editor or `astro check` type is not
  rediscovered later as a defect.
- Unit fixtures can diverge from actual Starlight output; the existing all-page
  emitted assertion remains the second layer.

## Changelog

- 2026-08-17: corrected again at implementation review, AFTER code. Two fail-open
  gates of mine were measured green and fixed: the job-level advisory/conditional
  checks scanned only the keys before the job's first blank line, so placing
  `if:`/`continue-on-error:` after the steps list defeated both; and nothing pinned
  what `test:plugins` IS, so replacing it with `true` left every gate green having
  run zero tests. Added a `shell:` neuter check, corrected `needs:` to test
  membership rather than the first element, taught the trigger parser the inline
  flow-sequence form, and moved the two real-tree checks out of `audit()` — a
  workflow-text mutation cannot flip them, so inside `audit()` they were decorative.
  Also corrected four surviving "required site CI" claims that contradicted the
  restated AC7, and replaced the Rollout section's denial of any migration.
- 2026-08-17: corrected at spec-stage review, before any code. AC7 conflated
  "required site CI" with a required status check: `pages.yml` is not one, and the
  only required workflow cannot carry the path-triggered behaviour AC7 also wants,
  so AC7 now describes a deploy-blocking gate and states that residual explicitly.
  T4's "reuse the site CI construction-test mechanism" was unsatisfiable — the only
  such mechanism is `build-check.yml`-shaped and `pages.yml` is scoped out of the
  parity linter — so a second, `pages.yml`-scoped parser is now the named decision,
  with the files needed to make it actually run. T4's `tools/test_*.py` glob became
  concrete paths. T1 gained the subprocess-in-temp-tree isolation mechanism, because
  `REPO_ROOT` is module-level and an in-process `main()` would write into the real
  tree. AC3 gained a verification artifact, AC5 the blockquote/aside case its
  register entry named (and a correction: a childless parent is unreachable through
  `visit`, so the criterion now names the root-level case a test can actually
  produce), AC10 per-control artifacts, AC4 a no-dependency check. Every TDD task
  now declares `stub: true` and every goal-based task `no stub (mode)`. Scope
  unchanged: no criterion dropped.
- 2026-08-17: initial plan after RFC-0089's direction and the built-in runner
  decision were confirmed; implementation remains blocked on RFC acceptance.
