# Plan: Skill script exit-2 collision

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence changes. Substantial
> changes are recorded in the changelog below.

## Approach

Correct the caller contract at the source of every affected skill. Each skill
introduces one self-contained invocation rule: obtain the directory containing
the active `SKILL.md` from the harness or installer, canonicalize the expected
entry point beneath `scripts/`, require its resolved regular-file target to
remain confined there, then pass the resolved path as one argument while
retaining the project root as the working directory. Command examples, loaded
references, bounded remediation messages, and behavior evals use that rule
consistently. No exit-code number, credential resolver, client operation, or
renderer operation moves.

Work is divided by pack so the four source/version surfaces remain reviewable.
Atlassian, Figma, Linear, and Converters can be authored independently; a final
integration task regenerates projections, updates the living documentation and
release record, removes both closed backlog items, and runs the cross-pack
gates.

## Constraints

- RFC-0006, RFC-0013, and ADR-0003 preserve the boundary between skill prose
  and credential-bearing subprocesses.
- RFC-0035 and ADR-0026 preserve the SSO engine/consumer split. RFC-0084 and
  ADR-0080 keep headed capture operator-only and automatic recovery headless.
- `docs/specs/credentialed-cli-exit-code-contract/spec.md` keeps exit 2 in the
  credential/user-action band for credentialed CLIs; this change cannot
  renumber or reinterpret that runtime contract.
- `packs/AGENTS.md` requires pack-local tests/evals, patch version bumps for
  non-cosmetic content changes, and source edits under `.apm`.
- `packs/AGENTS.local.md` requires self-host projection after all source edits
  and prohibits direct edits to projected adapter skills.
- `docs/architecture/reference.md` is absent. The established stack is Markdown
  skill contracts, JSON eval assets, Python/pytest source-contract checks, and
  agentbundle catalogue projection.

## Construction tests

**Integration tests:**

- A source-contract scan covers every surface in the spec's
  [affected invocation roster](spec.md#affected-invocation-roster), rejects
  executable `python scripts/…`, `python3 scripts/…`, and
  `node scripts/…` forms, and classifies any retained bare-relative fixture
  text as inert.
- Per-skill tests check canonical containment, regular-file preflight, and
  structured argv or platform-specific quoted fallback behavior for install
  paths containing spaces, quotes, `$()`, backticks, and variable-shaped text.
  A shell-only surface that cannot quote a path safely refuses rather than
  interpolating it.
- Behavior eval validation covers a successful resolved-path invocation and a
  missing-entry-point refusal for each affected primitive; the refusal output
  excludes credential, re-authentication, `mmdc` installation, and Node-package
  guidance as applicable, plus absolute install/profile paths and raw
  interpreter/runtime diagnostics.
- Atlassian evals prove headed `check --register` and `setup_sso.py`
  commands are relayed for the operator, never run by the agent, and are not
  reached from a missing-script branch.
- Existing credentialed exit-code suites remain green after only their expected
  remediation command text adopts the resolved form, without edits to runtime
  constants, credential loaders, API clients, or renderer implementations.
- A new pack-local Mermaid Renderer regression test pins exit 0, 1, and 2 and
  the `mmdc`-missing remediation.
- `agentbundle catalogue lint --root . --deep`,
  `agentbundle catalogue verify --root .`, the self-host drift check, and the
  repository's non-SAST build gate pass after projection.

**Manual verification:**

- In self-hosted Claude Code and Codex sessions rooted at a project without a
  local `scripts/` directory, exercise Jira `--help`, Mermaid Renderer
  `--check`, and Markdown to HTML. These represent the credentialed Python,
  dependency-reporting Python, and Node classes; the other roster rows and
  adapters are source/eval/projection-only.
- Repeat each class with the expected entry point absent in a disposable
  install fixture. The bounded diagnostic names no absolute/profile path or raw
  runtime stderr and offers no credential, SSO-capture, or renderer-dependency
  remediation.

## Design (LLD)

### Design decisions

- Keep resolution in each skill's invocation contract. A shared helper or new
  runtime resolver would add machinery to solve an instruction-level defect.
  Traces to: AC1-AC10.
- Preserve all child-process exit codes. Preflight establishes that the intended
  script started before its status is interpreted, eliminating the ambiguity
  without breaking callers that depend on exit 2. Traces to: AC3, AC6-AC11.
- Treat `<skill-dir>` as documentation notation only. The agent substitutes the
  actual installer-supplied directory, canonicalizes the target, and passes the
  path as one argv element. Shell-only tools use a platform-specific quoted
  fallback or refuse an unrepresentable path; shell interpolation is not part
  of the contract. Traces to: AC1-AC5.

### Interfaces & contracts

The modified interface is the published command-invocation protocol in eight
`SKILL.md` files. It exposes no standalone API/schema contract. Each protocol
has four ordered states:

1. Obtain the trusted directory containing the active `SKILL.md`.
2. Canonicalize the named `scripts/<entry-point>`, require a regular file, and
   reject a resolved target outside the canonical skill-owned `scripts/` base.
3. Launch the interpreter/runtime with that path as one argument from the
   project root.
4. Interpret the entry point's exit status using the skill's existing table.

Traces to: AC1-AC10 · Contract: none.

### Failure, edge cases & resilience

- Missing skill-directory metadata, a missing expected file, a non-file target,
  a symlink escape, or an interpreter-level cannot-open result is a skill
  installation/invocation failure. It stops before credential or dependency
  remediation and reports only a basename or generic placeholder path.
- Paths containing spaces or shell metacharacters remain one argv element when
  structured invocation is available. Shell-only tools use the established
  platform-specific quoted fallback and refuse paths they cannot represent
  without interpolation.
- Project-relative inputs and outputs remain relative to the project root;
  resolving the executable never changes CWD to the installed skill.
- Secondary `setup_sso.py` references and user-relayed registration commands
  follow the same resolved-path rule as primary `check` and operation commands.
- Real exit 2 from a preflighted Python entry point retains its current meaning;
  real exit 1 from preflighted `render.js` retains its current meaning.

Traces to: AC2-AC9.

### Dependencies & integration

Four independently versioned packs feed multiple adapter projections through
agentbundle. Canonical source, tests, evals, paired manifest versions, product
changelog, marketplace metadata, living architecture, knowledge capture, and
the workspace backlog must land atomically at the final gate. No dependency is
added.

Traces to: AC10-AC12.

## Tasks

### T1: Atlassian's four skill contracts resolve and preflight their installed scripts

**Depends on:** none

**Touches:** packs/atlassian/.apm/skills/{jira,jira-align,confluence-publisher,confluence-crawler}/**, packs/atlassian/tests/skills/{jira,jira-align,confluence-publisher,confluence-crawler}/**, packs/atlassian/pack.toml, packs/atlassian/.claude-plugin/plugin.json

**Verification mode:** Goal-based source-contract tests and behavior evals.

**Spec mapping:** Objective and affected invocation roster; Testing Strategy
`Invocation resolution and preflight` and `Agent remediation behavior`;
AC1-AC7, AC10-AC12.

**Tests:**

- Add or extend one pack-local invocation-contract test per affected skill.
  Assert every Atlassian row in the canonical roster covers its skill body,
  loaded references, evals, and emitted remediation; defines the trusted
  `<skill-dir>` base; confines each regular-file target; contains no executable
  bare-relative form; and keeps exit-2 remediation behind successful preflight.
- Update each skill's behavior eval success rubrics to require an installed
  skill path and add a missing-entry-point case that excludes
  `credential-setup`, token regeneration, re-authentication, and SSO capture.
- Preserve and test the operator-only status of headed registration and setup
  commands; automatic recovery remains headless.
- Run one pytest process per affected skill test directory, then validate the
  four eval JSON files independently.
- Update the Jira and Confluence Crawler remediation-string assertions to the
  resolved `<skill-dir>/scripts/...` form while preserving the existing exit
  semantics and operator-only command-text guard; run both exit-code suites.

**Approach:**

- Add the invocation protocol before the first command in each source
  `SKILL.md` and update every agent-visible surface in the four Atlassian
  rows of the canonical roster to use the resolved base or a bounded generic
  remediation form.
- Keep content arguments relative to the project root and retain all security
  and user-confirmation rules.
- Patch-bump Atlassian from the then-current released version in both manifests;
  do not ride another in-flight version.

**Done when:** all four source contracts and evals distinguish entry-point
resolution from genuine exit 2, their targeted tests pass, and the paired
Atlassian versions match.

### T2: Figma resolves and preflights its installed client

**Depends on:** none

**Touches:** packs/figma/.apm/skills/figma/**, packs/figma/tests/skills/figma/**, packs/figma/pack.toml, packs/figma/.claude-plugin/plugin.json

**Verification mode:** Goal-based source-contract tests and behavior evals.

**Spec mapping:** Objective and affected invocation roster; Testing Strategy
`Invocation resolution and preflight` and `Agent remediation behavior`;
AC1-AC6, AC10-AC12.

**Tests:**

- Add an invocation-contract test covering every surface in the Figma roster
  row, the trusted-base definition, confinement and preflight ordering,
  discrete argv rule, bounded diagnostics, and absence of bare-relative
  executable forms.
- Update Figma behavior eval success rubrics to require the resolved entry point
  and add a missing-script case that forbids credential setup, token
  regeneration, and scope guidance.
- Run the existing Figma exit-code suite unchanged and validate both eval JSON
  files.

**Approach:**

- Add the common invocation protocol to Figma's source `SKILL.md` and rewrite
  check, dispatch-table, help, render, comment, variable, and raw examples to
  use the resolved `figma.py`.
- Preserve credential handling, network behavior, and all child exit meanings.
- Patch-bump Figma from the then-current released version in both manifests.

**Done when:** every Figma invocation is resolved and preflighted, missing
`figma.py` cannot route to credential guidance, targeted tests/evals pass, and
the paired Figma versions match.

### T3: Linear gains resolved invocation behavior and its required eval roster

**Depends on:** none

**Touches:** packs/linear/.apm/skills/**, packs/linear/tests/skills/linear/**, packs/linear/pack.toml, packs/linear/.claude-plugin/plugin.json

**Verification mode:** Goal-based source-contract tests, Tier-A activation
checks, and a primitive behavior eval.

**Spec mapping:** Objective and affected invocation roster; Testing Strategy
`Invocation resolution and preflight` and `Agent remediation behavior`;
AC1-AC6, AC10-AC12.

**Tests:**

- Extend `test_linear_primitive.py` or add a sibling invocation test covering
  every surface in the Linear roster row, path confinement and preflight,
  bounded diagnostics, the no-bare-relative rule, and exit-2 interpretation
  only after a launched script.
- Add the Linear pack's required Tier-A activation files for `linear`,
  `linear-brief-intake`, and `linear-brief-sync`, with should-trigger and
  near-miss cases that meet catalogue authoring standards.
- Add a `linear` behavior eval with successful resolved invocation and
  missing-script refusal cases; validate all new JSON assets.
- Run the existing Linear primitive suite unchanged for runtime behavior.

**Approach:**

- Add the invocation protocol and rewrite the check and dispatch commands in
  `linear/SKILL.md`.
- Register the complete user-triggered Linear skill roster in `[pack.evals]`;
  activation coverage for the two workflows is required pack hygiene, while
  their workflow bodies remain unchanged.
- Patch-bump Linear from the then-current released version in both manifests.

**Done when:** Linear no longer confuses a missing script with credentials, the
pack has compliant activation/eval registration, targeted tests pass, and its
paired versions match.

### T4: Both affected converters resolve their installed renderer entry points

**Depends on:** none

**Touches:** packs/converters/.apm/skills/{mermaid-renderer,markdown-to-html}/**, packs/converters/tests/skills/{mermaid-renderer,markdown-to-html}/**, packs/converters/pack.toml, packs/converters/.claude-plugin/plugin.json

**Verification mode:** Goal-based source-contract tests and behavior evals.

**Spec mapping:** Objective and affected invocation roster; Testing Strategy
`Invocation resolution and preflight` and `Agent remediation behavior`;
AC1-AC5, AC8-AC12.

**Tests:**

- Add one invocation-contract test directory per converter, checking every
  surface in its canonical roster row, the trusted-base definition, confinement
  and preflight ordering, bounded diagnostics, project-root content behavior,
  script-emitted help and usage, and absence of executable bare-relative forms.
- Update both behavior evals so successful commands use resolved renderer paths.
  Add missing-entry-point cases: Mermaid Renderer must not recommend `mmdc`;
  Markdown to HTML must not report missing Node packages.
- Add a pack-local Mermaid Renderer regression test pinning `EXIT_OK=0`,
  `EXIT_PARTIAL=1`, `EXIT_USER_ACTION=2`, and the `mmdc`-missing remediation;
  validate both converters' eval JSON.

**Approach:**

- Rewrite `render_mermaid.py` and `render.js` invocations in their canonical
  source skill bodies, eval expectations, and script-emitted help or usage using
  the established `<skill-dir>` contract.
- Keep the interpreter/runtime, renderer logic, and input/output path semantics
  unchanged.
- Patch-bump Converters from the then-current released version in both
  manifests.

**Done when:** both converter entry points launch from project-root sessions,
missing scripts produce only resolution guidance, tests/evals pass, and the
paired Converters versions match.

### T5: Cross-pack projections, living docs, release records, and backlog are coherent

**Depends on:** T1-T4

**Touches:** docs/architecture/binder-publishing/invocation.md, docs/knowledge/patterns.jsonl, docs/product/changelog.md, workspace.toml, marketplace.json, .claude/skills/**, .codex/**, .agents/**

**Verification mode:** Goal-based integration checks and recorded manual QA.

**Spec mapping:** Objective and affected invocation roster; all Testing Strategy
modes; AC1-AC12.

**Tests:**

- Run the cross-pack source-contract scan and all targeted pack test directories
  as separate pytest processes.
- Validate all affected eval JSON and run the catalogue's eval-shape checks.
- Regenerate self-host projections after every source/version edit, then run
  catalogue lint `--deep`, catalogue verify, the self-host drift check, Ruff,
  and the non-SAST build gate.
- Perform the six representative project-root launches and the three
  missing-entry class checks from `Construction tests`. Record only commands
  in generic `<skill-dir>` form, exit statuses, and bounded diagnostics; never
  record resolved install/profile paths, credentials, or protected paths.

**Approach:**

- Retcon the living invocation architecture and K-0039 knowledge entry to state
  the corrected caller protocol while retaining the general warning against
  bare-relative skill paths.
- Add one changelog entry per patch-bumped pack and regenerate marketplace plus
  adapter projections from canonical sources.
- Remove `converters-bare-relative-script-paths` and
  `skill-script-exit-2-collision` from `workspace.toml` only after all
  acceptance gates pass.
- Confirm generated output contains no user-specific filesystem path; examples
  retain the generic `<skill-dir>` notation.

**Done when:** AC1-AC12 are mechanically or manually evidenced, generated state
is drift-free, both backlog entries are closed, and the full targeted gate set
passes.

## Rollout

- **Delivery:** one coordinated change across four patch releases. The source
  instructions and their projections ship together; there is no feature flag.
- **Infrastructure:** none.
- **External-system integration:** no live Atlassian, Figma, or Linear calls are
  required. Existing credential and renderer integrations are unchanged.
- **Deployment sequencing:** T1-T4 may be authored independently. T5 runs only
  after all four are present so projections, marketplace metadata, changelog,
  and backlog closure describe one coherent release.
- **Rollback:** revert the four source/version changes and regenerate
  projections. No data migration or irreversible state exists.

## Risks

- A mechanical text replacement can miss prose, tables, multiline examples, or
  secondary setup commands. Per-skill tests cover every surface in the
  canonical roster rather than a single `check` example.
- A broad regex can rewrite user-supplied diagnostic examples that intentionally
  quote an old command. Source-contract tests distinguish executable
  instructions from inert fixture text; reviewers inspect each exception.
- The `<skill-dir>` notation can be mistaken for a shell variable. Each skill
  explicitly says it is replaced from harness metadata and never passed
  literally or shell-expanded.
- Changing executable resolution can accidentally change content-path
  resolution by changing CWD. The design keeps project-root CWD fixed and varies
  only the executable argv element.
- Linear lacks a current eval roster. Adding the convention-required activation
  surface increases T3's review size, but omitting it would ship a non-cosmetic
  pack change against the pack authoring rules.
- Generated projection and marketplace files converge only after all pack
  changes are present. T5 owns them once to avoid competing generated edits.

## Changelog

- 2026-08-11: Initial plan after confirmation that one spec covers the seven
  Python exit-2 collisions and Markdown to HTML's companion path defect.
- 2026-08-11: Completed T1-T5, including generated projections, manual
  project-root probes, five remediated findings rounds, and a unanimous clean
  implementation review.
