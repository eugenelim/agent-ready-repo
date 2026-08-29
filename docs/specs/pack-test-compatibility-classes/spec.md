# Spec: Pack-test compatibility classes

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0071 (the pack remains the ownership and
  test-execution boundary — unchanged by this spec), RFC-0082 (test ownership
  boundaries and per-surface inclusion)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A pack author adding a test suite gets process isolation by default and never
has to reason about whether their new `test_contract.py` will collide with
someone else's. A maintainer who has *proved* that several suites in one pack
share an interpreter safely can declare that fact once, in a typed and
mechanically checked place, and the repository's runners collapse those suites
into a single pytest process. The declaration carries the evidence; the gate
re-derives the safety on every run, so a class cannot quietly broaden when a
new file appears, and a suite that stops being safe returns to isolation with a
red gate rather than a green false negative.

The user-visible effect is a faster local `make test` with an unchanged
semantic test surface: every node ID that ran before still runs, exactly once.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the stable public authoring contract changes from an unconditional per-skill rule to default isolation plus explicit classes; the choice between declaration designs is expensive to reverse | `docs/adr/` (next free ordinal) | work-loop | ADR accepted, naming what it supersedes in the authoring standard, carrying the measured before/after | ADR exists, Accepted, and the authoring standard cites it |
| Maintainer/adopter guidance | Applicable — `guides/_shared/reference/catalogue-authoring-standards.md` § 4 states the unconditional rule | that guide **and its byte-identical scaffold projection** under `packages/agentbundle/agentbundle/_data/catalogue-scaffold/` | work-loop | § 4 revised; normative summary updated; projection regenerated | Guide states default isolation + class exception, and both identity obligations; projection has no drift. The guide **must not** name ADR-0098: it is projected into adopter repositories that have no `docs/adr/`, and `tools/lint-guides-no-repo-only-refs.py` refuses both the path and the `ADR-NNNN` token. The ADR is cited from repo-only surfaces instead — `Makefile`, the lint module, and this spec. |
| Current architecture | Applicable — runner topology is a system fact | `tools/pack_test_compatibility.py` docstring; `tools/lint-pack-test-boundary.py` docstring; the `Makefile` comment at 396-403; the two workflow comments that state the old rule | work-loop | Each file describes the shipped model | No living document states the unconditional rule |
| Interface compatibility | Not applicable — no published schema, catalogue contract, or `agentbundle` CLI behavior changes | — | — | — | — |
| Release history | Not applicable — `tools/**`, `docs/**`, and workflow files are not part of the released artifact surface | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Preserve the exact semantic test surface of standalone `make test` — the same
  node IDs, each executed exactly once.
- Preserve `test-after-build-check`'s shared-test ownership.
- Keep every compatibility class inside one pack.
- Make a new suite directory isolated by default.
- Treat test-module identity and subject-module identity as separate proofs.
- Keep runner commands explicit and readable; a grouped command lists its
  members and never names an ancestor directory.
- Preserve each collection floor by keeping its suite the sole target of its
  invocation.
- Leave `.apm/` runtime payloads and every `packs/*/tests/**` file
  byte-identical.
- Clean every `__pycache__`, `.pytest_cache`, and characterization fixture
  before completion.

### Ask first

- Adding or removing `__init__.py` solely to influence pytest import identity.
- Renaming any test module or production script.
- Changing code under any `.apm/` runtime payload.
- Making `--import-mode=importlib` the repository-wide pytest default.
- Consolidating any core suite, or any suite bearing a collection floor.
- Admitting into a class any member whose reachable import set mutates
  `sys.path`.
- Accepting a wall-time or peak-memory regression in exchange for fewer
  processes.
- Adding a dependency, or a shared repository-wide pack-test runner or plugin.
- Editing workflow files — **required by this spec** for two comment
  corrections and for the path triggers that make the new gates run.

### Never do

- Run a global `pytest packs/`.
- Group suites from different packs in one process.
- Use pytest-xdist, parallel workers, or background execution.
- Treat `--import-mode=importlib` as a fix for subject-module collisions.
- Resolve a collision by mutating global `sys.path` and deleting entries from
  `sys.modules` at large.
- Make a class safe only for the files that exist today.
- Suppress a test using a timestamp, SHA, cache, receipt, or prior-run state.
- Activate a reduced profile through an ambient environment variable.
- Force one process per pack as a quota.
- Rewrite the body of a shipped spec, an RFC, or an ADR.

## Testing Strategy

Every acceptance criterion below names its mode.

- **TDD**, with a mutation-shaped red control each: AC7, AC8, AC9, AC10, AC11,
  AC12, AC13, AC14, AC19, AC31.
- **Goal-based check** — a command whose output settles the question: AC1, AC2,
  AC3, AC4, AC5, AC6, AC15, AC16, AC20, AC21, AC22, AC23, AC24, AC25, AC26,
  AC27, AC28, AC29, AC30, AC32.
- **Characterization** (goal-based, exercised as an integration test that runs
  pytest as a subprocess and compares collected node IDs across orderings):
  AC15, AC16, AC17.
- **Failure injection** (goal-based, against temporary copies restored
  byte-identically): AC18.

No behavior in this spec needs visual or manual QA.

## Acceptance Criteria

- [ ] **AC1** The pack-test inventory — pack, suite path, runner, command,
      import mode, test basenames, and class membership — is derived
      mechanically across **every** file in the lint's `_RUNNER_FILES`, not
      from a checked-in copy of today's list, and not from the `Makefile`
      alone.
- [ ] **AC2** Baseline and final pack-scoped pytest launch counts are produced
      by a command named verbatim in the plan, and re-running it reproduces the
      reported numbers.
- [ ] **AC3** Every pack test suite directory is either named by a runner or
      declared unrun with a reason; `every-suite-dir-has-a-runner` keeps its
      fail-closed, non-vacuous behavior, and no `_NO_RUNNER` entry becomes
      self-contradictory.
- [ ] **AC4** Standalone `make test` executes the same set of pytest node IDs
      as before this change, each exactly once — proven by comparing collected
      node-ID sets, with raw count equal to unique count on both sides.
- [ ] **AC5** `test-after-build-check` removes from the pack surface exactly
      the three pack-side build-check-owned files
      (`work-loop/test_lint_spec_status.py`,
      `work-loop/test_lint_traceability.py`,
      `receive-brief/test_lint_brief_coverage.py`) via `$(1)`/`$(2)`, and the
      two `tools/` files via the empty `$(3)` slot, and nothing else changes.
      `tools/test_local_ci_shared_test_deduplication.py` must **pass**. Its
      approved roster and plan digests are re-pinned, because that guard exists
      precisely to force an explicit, reasoned update when the recipe changes —
      the same discipline its own constant comment already demands. An earlier
      draft of this criterion said "passes unmodified", which would have made
      any recipe change impossible; the real obligation is that the delta is
      verified and recorded, not that the file is frozen. The recorded delta is
      standalone 71 → 58 and composed 70 → 57 plan lines, exactly the −13 from
      folding eighteen pack lines into five.
- [ ] **AC6** Each floor-bearing suite remains **the sole target of its own
      invocation**, so the plugin's session-wide `len(items)` count equals that
      suite's count: `desk-research` ≥ 9 and `desk-research-project-start` ≥ 7.
      No floor-bearing suite joins a class, and no aggregate floor is
      introduced.
- [ ] **AC7** No compatibility class contains a suite path outside its declared
      owning pack; a cross-pack class fails the gate.
- [ ] **AC8** A pack test suite not named in any class declaration runs in its
      own pytest process. Adding a new suite directory does not place it in an
      existing class, and an ancestor-shaped broad invocation is rejected even
      when the destinations it covers today match a class exactly.
- [ ] **AC9** Every runner invocation covering more than one suite corresponds
      exactly to one declared class — same member set, no extra path, no
      missing member — and carries that class's required pytest arguments.
- [ ] **AC10** Class declarations cannot overlap (a suite in two classes fails),
      go stale (a member path that does not exist fails), be unused (a declared
      class no runner exercises fails), or be trivial (a class with fewer than
      two members fails).
- [ ] **AC11** For every declared class, duplicate test module basenames among
      its members are proven to collect distinctly — either the class requires
      `--import-mode=importlib`, or the colliding directories carry
      disambiguating `__init__.py` files while their shared parent does not, or
      no basename collides. A class satisfying none of these fails.
- [ ] **AC12** For every declared class, every subject-module load is
      **statically resolvable** and every module name maps to **exactly one
      path**. Resolution is defined as: a string literal at the
      `spec_from_file_location` call, or a name argument traced by
      intraprocedural constant propagation through a same-module helper to a
      literal at every call site. The gate fails when one name is used for two
      different paths — the silent-binding hazard — or when a name does not
      resolve. Two members loading the **same** path under the same name is
      accepted: it is idempotent and cannot mis-bind. (Verified case:
      `workspace_status_engine` is loaded under that literal by both
      `core/tests/pack/` and `core/tests/skills/workspace-status/`, and both
      resolve to `.apm/skills/workspace-status/scripts/workspace_status_engine.py`
      — a name-uniqueness rule would have failed it for no reason.)
- [ ] **AC13** The import-safety derivation reads pytest's actual import set for
      each member: the member's test modules, **every `conftest.py` from rootdir
      down to the member's directory** (including the member's own directory
      when the member is a file), and local modules imported from those. Fixture
      trees that pytest never imports are excluded explicitly, not by accident.
- [ ] **AC14** Introducing an unsafe subject import into a class member — a
      `sys.path` mutation anywhere in that import set, a duplicate or
      unresolvable `spec_from_file_location` name, or (in an `importlib` class)
      a bare import of a sibling test module — fails the gate, proven by a
      mutation control for each form.
- [ ] **AC15** For every declared class, the union of node IDs collected by
      running its members in isolation equals the set collected by the grouped
      invocation.
- [ ] **AC16** For every declared class, the grouped run's skip and xfail
      dispositions equal the isolated union's.
- [ ] **AC17** For every declared class, the grouped invocation passes in
      forward order, in reverse member order, and across repeated fresh
      processes.
- [ ] **AC18** A failure injected into any single class member causes the
      grouped invocation to exit nonzero and to name that member's test path.
- [ ] **AC19** A collection error in a class member remains distinguishable
      from a test failure and cannot be reported as a pass.
- [ ] **AC20** Source-package resolution is unchanged: rootdir and configfile
      resolve identically for isolated and grouped invocations, and the root
      `[tool.pytest.ini_options] pythonpath` entries are untouched.
- [ ] **AC21** Every file under any `packs/*/.apm/` tree and every file under
      `packs/*/tests/` is byte-identical to its pre-change content, proven by
      `git diff --stat` over those paths being empty.
- [ ] **AC22** The pack boundary checks — `apm-carries-no-tests`,
      `projection-carries-no-tests`, `tests-live-in-the-pack-tree`, and
      `pack-tests-stay-in-pack` — are unchanged in behavior.
- [ ] **AC23** The Windows self-host runner is unmodified; its argv lists stay
      shell-free, and no grouped command introduces a shell construct.
- [ ] **AC24** Root and `tools/` pytest topology is unchanged; no invocation
      outside `packs/` is regrouped by this spec.
- [ ] **AC25** Coordination-lease behavior, run-slot policy, and concurrency
      limits are unchanged.
- [ ] **AC26** Process count, wall time, and peak resident memory are measured
      before and after with a stated method, a stated repetition count, and a
      stated uncertainty.
- [ ] **AC27** No class ships whose median wall time exceeds its members'
      isolated median. Peak resident memory may exceed the isolated maximum by
      at most **8 MiB**, measured as the median of three `/usr/bin/time -l`
      runs; a class exceeding that tolerance is dropped or re-scoped. The
      tolerance exists because single-digit MiB differences are within this
      measurement's noise.
- [ ] **AC28** The bodies of `docs/specs/pack-test-boundary-remaining-packs/`,
      `docs/specs/pack-test-boundary/`, RFC-0082, and ADR-0071 are unmodified;
      only permitted append-only Status annotations are added, and only where
      the conventions require one.
- [ ] **AC29** `git status --short` is clean and `git diff --check` passes at
      completion: no `__pycache__`, `.pytest_cache`, characterization fixture,
      benchmark output, or scaffold-projection drift remains.
- [ ] **AC30** At least one compatibility class with two or more members ships.
      If the pilot and every additional candidate is disproved, the initiative
      stops as a documented no-go and any compatibility infrastructure already
      landed is reverted.
- [ ] **AC31** A pytest invocation in any runner whose path arguments are not
      statically resolvable — a shell variable, a matrix expression, a composite
      action — is itself a finding, so grouping cannot be hidden behind
      indirection. The existing `for`-loop form in
      `catalogue-tooling-ci-gates.yml` is recorded as a declared exception with
      its reason, not silently tolerated.
- [ ] **AC32** Both new test modules are executed by a repository gate, and the
      declaration module's path triggers the workflow that runs the boundary
      lint; a change to `CLASSES` alone re-runs the gate that gives it meaning.
- [ ] **AC33** The golden baseline amendment is recorded, not silent. Replacing
      `runners-keep-suites-isolated` changes the boundary lint's observable
      output in **all 22** captured cases, which
      `docs/specs/lint-performance-p0/spec.md` routes to *Ask first*
      ("A required difference is a spec amendment, recorded with the reason and
      the new expected bytes — never a silently rebaselined golden file").
      Owner approval was given at the plan checkpoint. The corpus also grew
      from 22 to 32 cases, because each new rule needed a red control and the
      fixture registry is the corpus; that growth is part of the same amendment.
      Therefore:
      `PINNED_COMMIT` and `PINNED_BLOB_SHA256` in
      `tools/test-lint-boundary-golden.py` are repointed to the commit carrying
      the new lint; `tools/lint-boundary-golden.json` is regenerated from that
      pinned subject, never hand-edited to make a comparison pass; the reason is
      recorded here and in the new ADR; and
      `docs/specs/lint-performance-p0/spec.md` receives an append-only
      Status-line annotation naming the ADR that supersedes this part. The
      amendment is unavoidable for any honest implementation: the string
      `ok   [runners-keep-suites-isolated]` appears in every passing case, so
      renaming or replacing that check changes all 22 regardless of how many
      checks the lint ends up with.

## Assumptions

- pytest 9.0.3 is the version the gates run. `--import-mode=importlib` node IDs
  are path-based and match prepend-mode node IDs for the affected suites; both
  were verified on this worktree at commit `939147d6`.
- No `conftest.py` exists at the repository root, at `packs/`, at
  `packs/<pack>/`, or at `packs/<pack>/tests/`, so a member's conftest exposure
  is its own directory's file and nothing above it. Verified.
- Timing and memory figures are measured on a developer machine shared with
  several other worktrees; absolute numbers carry roughly ±30 % variance. The
  class-level direction of the effect is the claim.
- No adopter consumes the per-skill process rule as an executable contract; it
  is guidance in a published authoring standard, so revising it is a
  documentation and lint change, not a schema change.
