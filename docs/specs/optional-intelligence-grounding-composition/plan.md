# Plan: Optional intelligence in repository grounding

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/core/.apm/skills/new-spec/scripts/explore-grounding.py`; `packs/core/tests/skills/new-spec/test_explore_grounding.py`; `packs/core/tests/skills/new-spec/test_repository_grounding_evals.py`; `packs/core/.apm/skills/project-knowledge/SKILL.md` and `packs/core/tests/skills/project-knowledge/` as precedent for a reusable Core inquiry owner and its construction tests; `packs/AGENTS.md#version-bump-rule`; `docs/architecture/loop-contract.md`; `docs/rfc/0079-codebase-context-pack.md`; uncertainty resolved by the confirmed `repository-grounding` owner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Extract the existing path-seeded explorer into a narrow public
`repository-grounding` skill while preserving its command behavior and tests.
The script remains the repository-native probe; the skill owns the agent-level
decision to consider an already-exposed capability, invoke it in its native
shape, carry caveats, verify load-bearing claims, or deliberately fall back.
`new-spec` delegates its existing grounding step to this owner and never learns
provider identities or lifecycle. Behavior evaluations prove paired provider
and no-provider outcomes, then the normal Core build verifies adapter parity.

## Constraints

- RFC-0079 owns exposed-capability discovery, native provider shapes,
  attribution, fallback, authority, and locator safety.
- `packs/AGENTS.md` and `packs/AGENTS.local.md` own version derivation and the
  complete pack release pipeline.
- ADR-0037 keeps optional grounding presence-checked and inside the existing
  grounding gate rather than creating a parallel front door.
- Core must install and pass without `packs/code-intelligence`, Wicked Estate,
  an index, or any other provider.
- The repository-native Python explorer never becomes a provider broker and
  accepts no normalized provider payload.
- Canonical `.apm` sources move first; generated projections are rebuilt rather
  than edited.

## Construction tests

**Integration tests:** one paired behavior evaluation asks the same grounding
question with a useful exposed capability and with no provider; a second matrix
covers poor fit, refusal, malformed output, source conflict, and unsafe
locators. Core build checks prove all declared adapters contain the new skill.

**Manual verification:** inspect a built Core-only installation and confirm the
grounding inquiry completes without provider messaging; inspect a provider-fit
run and confirm the consuming `new-spec` procedure contains no provider step.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `packs/core/.apm/skills/repository-grounding/` | T1, T2 | Baseline tests and behavior evaluations | Built-adapter parity and shipped skill inventory |
| Core release pipeline surfaces | T1, T4 | Version-rule derivation, manifest parity, generated marketplace, changelog, and Highlights-disposition checks | Required release surfaces agree on the target and consumer outcome |
| `packs/core/.apm/skills/new-spec/SKILL.md` | T3 | Delegation and absence assertions | Main-flow review finds no provider lifecycle branch |
| `packs/core/README.md` | T3 | Documentation assertions and link check | Public description matches shipped behavior |
| Reusable-learning disposition | T4 | Capture receipt or explicit no-capture note | Closeout records one disposition |

## Design (LLD)

### Design decisions

The new skill is an inquiry owner, not a router. It receives the repository
question and seed bounds already owned by its caller, runs the baseline, and may
add provider evidence when an exposed native action directly helps. The
provider branch lives in skill guidance and evaluations, not in the baseline
Python script. This keeps provider transports out of Core code and lets host,
skill, repository-guidance, and user-selected surfaces retain their native
invocation forms. Traces to AC-0001, AC-0002, AC-0003, AC-0004, AC-0005,
AC-0006, AC-0007, AC-0008, and AC-0009. Owned by T1-T3.

### Interfaces & contracts

The existing `explore-grounding.py --root <root> --phase <phase> <seed...>` CLI
and its always-report behavior remain stable after relocation. `new-spec`
invokes the public `repository-grounding` method with its discovery seed paths;
there is no provider request or response interface. Evidence returns through
the inquiry's ordinary report with source class, attribution, and material
limits. Traces to AC-0007, AC-0008, and AC-0009. Owned by T1 and T3.

### Failure, edge cases & resilience

No exposed capability, poor semantic fit, refusal, timeout, malformed or
incomplete output, and unavailable indexes all converge on the baseline.
Conflicting derived evidence remains visible but cannot satisfy the question.
Before any provider locator is dereferenced, the repository's blessed
`agentbundle.catalogue_tooling.file_safety` confinement contract—or a tested
equivalent only when that helper is unavailable—enforces no-follow open,
regular-file and root-containment checks, hard-link refusal, byte bounds, and
pre/post-open identity comparison. Refusal returns to baseline without hiding
the unsafe result. Traces to AC-0001, AC-0003, AC-0004, AC-0005, and AC-0006.
Owned by T2.

### Dependencies & integration

`repository-grounding` depends only on Core and the Python standard library.
Optional providers are discovered from the active authorized surface at run
time; none is installed, imported, registered, or version-matched by Core.
`new-spec` is the sole consumer changed in this slice. Traces to AC-0006,
AC-0007, AC-0008, AC-0009, and AC-0010. Owned by T3.

## Tasks

### T1: The path-seeded baseline has one public grounding owner without behavior drift

**Depends on:** none

**Touches:** `packs/core/.apm/skills/repository-grounding/**`, `packs/core/.apm/skills/new-spec/scripts/explore-grounding.py`, `packs/core/tests/skills/new-spec/test_explore_grounding.py`, `packs/core/tests/skills/new-spec/test_repository_grounding_evals.py`, `packs/core/tests/skills/repository-grounding/**`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`, `docs/architecture/loop-contract.md`

**Verification mode:** TDD regression checks plus goal-based release-pipeline
checks; targeted baseline test output, the single-implementation reference
audit, generated marketplace output, and release records are the evidence
artifacts.

**Tests:**
- Relocated baseline tests preserve every current phase, outcome class, bound,
  and confinement case (AC-0009).
- A compatibility assertion finds no second editable copy of the explorer
  implementation (AC-0009).
- Pack metadata checks prove `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the target derived under
  AC-0013; `FORCE=1 make build-self` regenerates matching marketplace metadata,
  and the release entry records the required Highlights disposition.

**Approach:** Move the implementation and its tests under the new owner, then
update repository references in one change; keep a compatibility wrapper only
if a bounded reference audit proves an external published path needs it.

**Done when:** the grounding test suite is green from the new owner, every
tracked reference resolves to the single implementation, and the AC-0013
release surfaces and disposition pass their checks.

### T2: Optional evidence preserves baseline, authority, and locator safety

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/repository-grounding/SKILL.md`, `packs/core/.apm/skills/repository-grounding/references/**`, `packs/core/.apm/skills/repository-grounding/scripts/**`, `packs/core/.apm/skills/repository-grounding/evals/**`, `packs/core/tests/skills/repository-grounding/**`

**Verification mode:** TDD matrix plus goal-based behavior evaluation; test
output, native provider-shaped results, and the confined-read audit are the
evidence artifacts.

**Tests:**
- Table-driven tests cover provider-fit, absent, poor-fit, refused, timed-out,
  malformed, incomplete, conflicting, and unsafe-locator cases
  (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006).
- A discovery-surface evaluation and bounded absence scan prove AC-0006 uses
  only exposed authorized surfaces and never probes hidden configuration,
  credentials, endpoints, pack directories, or arbitrary executables.
- Behavior evaluations reject provider authority and any normalized capability,
  request, result, provenance, freshness, confidence/completeness/error, or
  workflow-state representation while preserving native invocation language
  (AC-0002, AC-0004, AC-0007).
- A positive provider-fit fixture requires an authoritative source, test,
  contract, or record check even when no conflict is apparent; an unavailable
  check leaves the claim unresolved and unable to satisfy the acceptance
  condition alone (AC-0012).
- Disclosure fixtures prove AC-0011 for both request and retained-result paths,
  including provider output containing prohibited or unrelated context that
  cannot enter passing evidence or the verification ledger.
- Confinement tests accept safe native absolute and URI locators and use real
  parent escapes, symlinks, hard links, non-regular and oversized files, and
  pre/post-open identity-change simulation for refusal cases; the test proves
  use of the blessed helper or equivalence of the fallback contract and accepts
  a file at `MAX_READ_BYTES` while refusing one byte above it (AC-0005).

**Done when:** every case reaches either attributed advisory evidence or the
same repository-native acceptance question, and no provider result can widen
scope or pass an acceptance condition alone.

### T3: New-spec delegates grounding and Core documents the optional seam

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/README.md`, `packs/core/tests/skills/new-spec/**`, `packs/core/tests/pack/**`

**Verification mode:** Goal-based integration and build checks; delegation,
Core-only install, documentation, and adapter outputs are the evidence artifacts.

**Tests:**
- Static and behavior tests prove `new-spec` delegates the existing inquiry but
  contains no provider identity, setup, invocation, freshness, or fallback
  branch (AC-0008).
- A Core-only install and every declared adapter expose `repository-grounding`
  and pass its absence path (AC-0001, AC-0010).
- Documentation checks pin the optional, provider-neutral, native-shape story
  without naming the golden provider as a requirement (AC-0007, AC-0010).

**Done when:** `new-spec` uses the owner at its existing grounding step, the
Core README describes the seam, and adapter parity checks pass.

### T4: The complete grounding contract passes repository gates and closeout

**Depends on:** T1-T3

**Touches:** `docs/specs/optional-intelligence-grounding-composition/notes/**`, `workspace.toml`

**Verification mode:** Goal-based repository gates; the verification ledger is
the task's evidence boundary.

**Tests:**
- Targeted grounding, new-spec, pack, and adapter suites pass
  (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013).
- Evidence-output fixtures prove prohibited provider-returned context is not
  retained (AC-0011).
- The provider-fit verification fixture records the authoritative check or the
  unresolved result required by AC-0012.
- Release verification records the baseline versions, version-rule derivation,
  matching manifest and marketplace target, free-standing changelog entry, and
  Highlights disposition required by AC-0013.
- Spec/plan status, traceability, link, and workspace checks pass.
- The local lint/type gate passes or its environment blocker is recorded.

**Done when:** the verification ledger maps every acceptance criterion named in
this task to green evidence, the workspace entry reflects the shipped state
when authorized, and closeout records the reusable-learning disposition.

## Rollout

This ships as a normal Core skill and a delegation at the existing `new-spec`
grounding step. No feature flag, infrastructure, service, credential, or
provider installation is needed. Reverting the delegation and restoring the
prior script path restores the earlier behavior; provider results create no
persistent state or migration.

## Risks

- Moving the explorer may break untracked consumers; the bounded reference
  audit determines whether a compatibility wrapper is necessary.
- Prompt-level capability selection may become vague; heterogeneous behavior
  evals must fail examples that merely say "use available tools."
- Locator safety may be described but not exercised; real filesystem fixtures
  are required rather than text-only assertions.
- The new owner may absorb workflow decisions; tests and review must keep it
  report-never-decide.

## Changelog

- 2026-10-04: spec approved by eugenelim as part of the CAP-0011 feature cohort.
- 2026-10-04: plan approved by eugenelim as part of the CAP-0011 feature cohort.
