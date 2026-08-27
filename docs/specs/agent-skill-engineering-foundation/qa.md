# Agent Skill Engineering Foundation — QA record

## Local evidence

| Surface | Result |
| --- | --- |
| Compiler prerequisite red/green cases | 6 passed after the implementation; hostile title/type values escape or refuse and a forced second-render divergence reports `OKF012` without retained output. |
| Compiler render suite | 23 passed after the final explicit-provider description hardening. |
| Full compiler suite | A cleanup-capable outer run passed all 135 tests. A later local run after description hardening passed 131 tests; the same 4 filesystem-mutation cases were prevented by managed `rename`/`rmtree` denial before their assertions. Tests were not changed or skipped, and the affected render suite passed separately. |
| Provider-capability compiler regressions | Three focused cases passed: valid metadata is rendered deterministically, an invalid declaration is refused before generation, and Unicode format metadata is rejected consistently by schema and compiler. |
| OKF profile schema | 42 contract fixtures passed, including acceptance of the bounded optional provider capability and refusal of implicit invocation or Unicode format characters. This extends the existing machine-consumed build profile; it does not add a serialized provider-envelope or skill-behavior schema. |
| Foundation pack tests | 31 passed, covering workflow construction, six exact unsupported-mode refusals, four behavior fixtures, independently reviewed defect findings, digest-bound activation evidence, exact router scoring, generated corpus/router, staged source independence and read confinement, provider cases, language seams, and pack boundaries. |
| Router precision | An independent read-only sub-context routed all 24 predeclared cases. The durable result is bound to the exact router and generated-tree bytes and records 24 exact set matches, including all six no-topic integration and near-miss cases; measured precision and recall are both 100%, with at most three topics returned. |
| Activation | The supported in-harness grader passed 18/18 independently classified queries: 8/8 positive workflow queries selected the target, 10/10 negative queries selected neither workflow, and there were no exclusivity violations. A durable artifact binds every expected and actual classification to the exact query fixtures and skill descriptions. The report is labelled `fidelity=reported`, not headless-observed. A first cleanup-capable headless run then found three error-independent positive misses plus two errored positive runs. The activation descriptions were hardened and the generated provider description now forbids direct user selection; construction tests bind those properties. A final cleanup-capable headless rerun remains required because the managed local rerun produced harness errors on all 18 queries and no reliable rates. |
| Behavior | The supported B-lite in-harness grader passed 4/4 cases. It re-derived required output markers from prepared workspaces and combined them with independent assertion judgments. All four results are durable and source-digest-bound; the two review candidates report all ten seeded defect identifiers, and the hostile helper was inspected but never executed. |
| OKF generated drift | `OKF000 check clean packs/agent-skill-engineering`. |
| Skill structure | Both user-facing skills and the generated router passed `quick_validate.py`. |
| Catalogue lint | Standard lint passed. Deep lint passed with warnings only; the new warning is the compiler-owned `references/okf/index.md` depth also present on the architect router. |
| Manifest | Strict validation passed after using canonical category vocabulary. |
| Static quality | Repository Ruff, mypy, Python compilation, and `git diff --check` passed. |
| Spec/documentation | Spec-status lint passed with repository-wide warn-only legacy references. README claims were checked against `pack.toml`, both user-facing skills, the provider contract, and generated router. The README has no local links to break. |

## Outer-loop evidence retained without weakening

A cleanup-capable verification run produced the following results without
changing the worktree:

- the full compile-OKF suite passed all 135 tests;
- an all-target render completed in a fresh `/private/tmp` directory, emitted
  the complete APM package plus an empty marketplace, and removed only that
  guarded temporary root;
- self-host check reported four expected projection drifts for the two changed
  compile-OKF source files under `.claude/` and `.agents/`;
- pack-scoped catalogue verification reported only `CAT-V-015`, the same
  repository-wide self-host drift, and no foundation-pack-specific error;
- headless activation iteration 4 reported three error-independent positive
  misses, two additional errored positive runs, and one generated-reference
  exclusivity violation.

The misses and exclusivity issue drove a source repair: both user-facing
descriptions now lead with their exact user requests, and generated provider
routers explicitly say they must never be selected directly for a user request.
The compiler, focused render suite, foundation pack suite, generated drift
check, and digest-bound fixtures pass after that repair.

The managed local runtime still denies deletion or atomic rename inside
tool-created trees. One `make build-self` attempt reached that boundary while
replacing an unrelated projected skill; its four partially removed tracked
files were restored byte-identically from their canonical pack source, and the
denied operation was not retried. A later headless iteration 5 produced harness
errors for all 18 queries and could not remove its temporary projection, so it
provides no reliable activation rates. The four unchanged compiler
filesystem-mutation tests likewise remain locally unexecutable. Final release
evidence therefore still requires one cleanup-capable `make build-self`, clean
self-host and catalogue verification, and one clean headless activation run
against the repaired descriptions. Tests and thresholds remain unchanged.

## Security and failure evidence

The local provider matrix covers absence, ambiguity, stale contract, malformed
ownership, authority widening, identity conflict, over-cap results, prompt
injection, credential-shaped diagnostics, malformed/generic/overbroad requests,
and an eligible independent provider whose selected reference is absent from
its ownership manifest. Accepted responses carry compiled guidance, exact
contract and provider provenance, profile dates where applicable, and bounded
warnings. Every refusal continues the baseline and records zero topic-content
reads. The generated router exposes deterministic discovery metadata for the
v1 capability while retaining explicit-only invocation and generated-manifest
ownership. Skill instructions keep authentication external, require
confinement before candidate reads and writes, and prevent provider output from
changing authority.
