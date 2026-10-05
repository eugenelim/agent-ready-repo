# Plan: Optional intelligence in repository exploration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/core/.apm/skills/bug-fix/SKILL.md`; `packs/core/.apm/skills/explain-diff/SKILL.md`; `packs/code-intelligence/.apm/skills/code-intelligence/SKILL.md`; `packs/code-intelligence/.apm/skills/code-intelligence/references/capability-map.md`; `packs/AGENTS.md#version-bump-rule`; `docs/rfc/0079-codebase-context-pack.md`; no existing reusable Core exploration owner.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Add a small standalone `repository-exploration` skill to Core. Its method is a
reasoning sequence—question, exposed capabilities, semantic fit, native action
or fallback, evidence limits, authoritative check, and stop—not a runtime
dispatcher. Build prompt-level evaluations from materially different native
surfaces and representative inquiry types, with deliberate poor-fit cases.
Do not edit consuming workflow procedures in this slice. Document the skill as
an optional utility and verify it in Core-only builds across adapters.

## Constraints

- RFC-0079 governs exposed-only discovery, native provider shapes, attribution,
  fallback, authority, safety, and non-mandatory use.
- `packs/AGENTS.md` and `packs/AGENTS.local.md` own version derivation and the
  complete pack release pipeline.
- RFC-0104 keeps Wicked Estate commands and current investigation patterns in
  the optional `code-intelligence` pack.
- ADR-0097 is precedent for capability-mediated selection but its knowledge
  request, result, corpus, manifest, and traversal contracts do not apply.
- No consuming workflow, provider schema, provider registry, shared runtime,
  new dependency, or fixed investigation taxonomy is introduced.
- Canonical `.apm` sources move first; generated projections are rebuilt rather
  than edited.

## Construction tests

**Integration tests:** a behavior matrix covers symbol definition and incoming
calls through editor/LSP-shaped metadata; transitive impact and dependency
paths through indexed CLI/MCP-shaped metadata; authority and co-change through
deliberate repository-native fallback; plus failure, conflict, and exposed-but-
poor-fit cases.

**Manual verification:** in a built Core-only installation, invoke the skill on
one debugging and one architecture question and confirm it can complete without
an optional provider or provider setup prompt.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `packs/core/.apm/skills/repository-exploration/` | T1, T2 | Skill tests and heterogeneous evaluations | Built-adapter parity and shipped skill inventory |
| Core release pipeline surfaces | T1, T4 | Version-rule derivation, manifest parity, generated marketplace, changelog, and Highlights-disposition checks | Required release surfaces agree on the target and consumer outcome |
| `packs/core/README.md` | T3 | Documentation assertions and link check | Public description matches shipped behavior |
| Reusable-learning disposition | T4 | Capture receipt or explicit no-capture note | Closeout records one disposition |

## Design (LLD)

### Design decisions

The skill is invokable as a bounded method by a human, an agent, or an
inquiry-owning skill. It does not auto-run and does not become a work phase. Its
shared content governs reasoning and evidence discipline only; native tool
descriptions and outputs remain unmodified provider data. The caller supplies
the question and owns the stopping rule and final decision. Traces to AC-0001,
AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, and
AC-0010. Owned by T1-T3.

### Interfaces & contracts

There is no machine provider interface. The skill reads whichever authorized
capabilities the active runtime already exposes, invokes the chosen action by
its native tool or skill contract, and returns ordinary attributed evidence to
the caller. Evaluation fixtures preserve the provider-shaped descriptions and
results rather than adapting them into a common envelope. Traces to AC-0002,
AC-0003, AC-0004, AC-0005, AC-0006, and AC-0009. Owned by T1 and T2.

### Failure, edge cases & resilience

Missing metadata, ambiguous fit, excess disclosure, excessive cost, unknown
freshness, refusal, timeout, malformed output, incomplete coverage, or conflict
routes to deliberate fallback or an explicit evidence gap. A second provider
is considered only for a named unresolved gap. Untrusted metadata and results
cannot issue instructions or widen authority. Provider-returned locators use
the repository's blessed `agentbundle.catalogue_tooling.file_safety`
confinement contract, or a tested equivalent only when that helper is
unavailable, before use. Safe native absolute and URI forms remain usable when
confinement succeeds; unsafe shape alone never decides the result. The skill
owns one internal `MAX_PROVIDER_READ_BYTES` ceiling and supplies it as
`max_bytes` for every file read; fixtures derive their boundary sizes from that
value rather than copying it.
Traces to AC-0002, AC-0003, AC-0005, AC-0006, AC-0007, AC-0008, AC-0011,
and AC-0012. Owned by T1-T2.

### Dependencies & integration

The skill has no provider or optional-pack dependency. The heterogeneous
fixtures are test inputs, not provider adapters. No current consumer is edited;
later inquiry owners may invoke the skill without changing its provider-neutral
contract. Traces to AC-0004, AC-0008, AC-0009, and AC-0010. Owned by T2-T3.

## Tasks

### T1: Repository exploration has a bounded provider-neutral method

**Depends on:** none

**Touches:** `packs/core/.apm/skills/repository-exploration/SKILL.md`, `packs/core/.apm/skills/repository-exploration/references/**`, `packs/core/tests/skills/repository-exploration/**`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`

**Verification mode:** Goal-based checks over skill construction tests, the
behavior-evaluation result, and the release pipeline; evidence stays in
targeted test output, generated marketplace output, release records, and the
verification ledger.

**Tests:**
- Construction tests require the ordered reasoning obligations while rejecting
  hidden probing, provider preference, common schemas, workflow-state ownership,
  and unbounded exploration (AC-0001, AC-0002, AC-0003, AC-0006, AC-0007,
  AC-0008, AC-0009).
- Absence, ambiguity, failure, and conflict cases end in explicit fallback or a
  named evidence gap without blocking the caller (AC-0005, AC-0006, AC-0007,
  AC-0008).
- Disclosure fixtures prove AC-0011 on both request and retained-result paths,
  including provider output containing protected or unrelated context that
  cannot enter passing evidence or the verification ledger.
- Real locator fixtures cover confined native absolute and URI inputs plus
  parent escapes, redirects, hard links, non-regular and oversized files, and
  pre/post-open identity changes; the test proves use of the blessed helper or
  equivalence of the fallback contract and accepts a file at the declared byte
  ceiling while refusing one byte above it (AC-0012).
- Pack metadata checks prove `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the target derived under
  AC-0013; `FORCE=1 make build-self` regenerates matching marketplace metadata,
  and the release entry records the required Highlights disposition.

**Done when:** the skill can accept a repository question, choose or decline an
exposed native action, return bounded attributed evidence, stop without owning
the caller's decision, and pass the AC-0013 release-surface checks.

### T2: Heterogeneous fixtures prove native selection without normalization

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/repository-exploration/evals/**`, `packs/core/tests/skills/repository-exploration/**`

**Verification mode:** Goal-based behavior evaluation; the provider-shaped
fixture results and evaluator verdicts are the evidence artifact.

**Tests:**
- Editor/LSP-shaped fixtures cover symbol definition and incoming calls; indexed
  CLI/MCP-shaped fixtures cover dependency paths and transitive impact (AC-0004).
- Authority and co-change fixtures select repository-native evidence and name
  what the exposed provider cannot establish (AC-0005).
- Debugging, review, implementation, architecture, and task-context cases each
  state their own question and stopping condition (AC-0001, AC-0007).
- A novel native action absent from the fixture vocabulary can still be chosen
  by meaning without editing an enum (AC-0009).

**Done when:** the behavior-evaluation matrix passes across both provider shapes
and the fallback cases without a shared provider payload or taxonomy.

### T3: Core publishes the exploration method without wiring consumers

**Depends on:** T1, T2

**Touches:** `packs/core/README.md`, `packs/core/tests/pack/**`

**Verification mode:** Goal-based documentation, absence-sweep, and adapter
build checks; command output is recorded in the verification ledger.

**Tests:**
- Documentation assertions distinguish optional utility, inquiry ownership,
  native shapes, and illustrative examples from a phase or broker (AC-0008,
  AC-0009, AC-0010).
- Core-only builds for every declared adapter expose the skill and pass its
  no-provider evaluation (AC-0010).
- A bounded search confirms no consuming main procedure gained provider
  discovery, setup, invocation, freshness, or fallback steps (AC-0008).

**Done when:** the README explains when to invoke the skill, every adapter ships
it, and the consumer-surface absence check is green.

### T4: The exploration contract passes repository gates and closeout

**Depends on:** T1-T3

**Touches:** `docs/specs/optional-intelligence-exploration-composition/notes/**`, `workspace.toml`

**Verification mode:** Goal-based repository gates; the verification ledger is
the task's evidence boundary.

**Tests:**
- Targeted skill, evaluation, pack, and adapter suites pass (AC-0001, AC-0002,
  AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010,
  AC-0011, AC-0012, AC-0013).
- Evidence-output fixtures prove prohibited provider-returned context is not
  retained (AC-0011).
- Release verification records the baseline versions, version-rule derivation,
  matching manifest and marketplace target, free-standing changelog entry, and
  Highlights disposition required by AC-0013.
- Spec/plan status, traceability, link, and workspace checks pass.
- The local lint/type gate passes or its environment blocker is recorded.

**Done when:** the verification ledger maps every acceptance criterion named in
this task to green evidence, the workspace entry reflects shipped state when
authorized, and closeout records the reusable-learning disposition.

## Rollout

The skill ships inert until invoked. It needs no flag, infrastructure, service,
credential, index, provider installation, or deployment order. Removal deletes
the optional method and its documentation without changing any consuming
workflow or provider.

## Risks

- A prompt-only method can collapse into vague advice; evaluations must require
  a concrete choice, native action or explicit fallback, caveat, check, and
  stopping point.
- Test fixtures can accidentally define a schema; they must remain independent
  provider-shaped scenarios with no shared parsed envelope.
- A public skill can be mistaken for a required phase; naming, README copy, and
  absence tests must keep invocation optional.
- The current matrix can freeze future exploration; the novel-action case must
  prove the method is semantic rather than enumerated.

## Changelog

- 2026-10-04: spec approved by eugenelim as part of the CAP-0011 feature cohort.
- 2026-10-04: plan approved by eugenelim as part of the CAP-0011 feature cohort.
