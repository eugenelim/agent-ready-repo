# Brief: Deliver agent skill engineering

- **Slug:** `agent-skill-engineering`
- **Received:** 2026-08-26
- **Owner:** Repository maintainers (`ini-009`)
- **Status:** Executing

## Outcome

Agent-skill authors and agent loops can use one portable, progressively disclosed
engineering system to frame, create, update, evaluate, review, and optimize skills.
The system combines focused workflows with a governed same-pack OKF corpus, supports
Python and TypeScript/Node practice, and exposes reusable knowledge to CI,
architecture, and other agent loops through explicit provider-mediated routing.

The repository self-hosts the pack and replaces duplicated explanatory guidance only
after cold-agent parity and retrieval measurements show that the new owner is at least
as usable and safe. AgentBundle manifests, projections, versions, self-host commands,
admission, and publication remain external delivery mechanics rather than becoming
portable doctrine.

## Success metrics

- The initial portable workflows provide `frame`, `create`, and `update` modes plus a
  review/optimize workflow; activation and behavioral evaluations pass for each mode.
- A deterministic generated router retrieves task-relevant topics without exposing raw
  OKF or silently crossing pack boundaries, and fails closed on missing or ambiguous
  topics.
- The corpus accounts for the current 131-skill pack census and documents applicability
  limits rather than promoting every observed local pattern to universal guidance.
- Separate Python/pytest and TypeScript/Node topics cover skill-script and evaluation
  contracts, while execution-economics topics cover local scripts, pack-level tests,
  skill/evaluation CI, multiple worktrees, state locks, shared hosts, and machine-load
  detection.
- Retrieval-dated profiles exist for Claude Code, Codex, GitHub Copilot, Cursor, Kiro
  IDE, Kiro CLI, Gemini CLI, and Google Antigravity. Every operative capability claim
  has a first-party source and a current verification record.
- Subagent, hook, and plugin guidance separates a portable capability floor from
  runtime-specific composition and degradation behavior.
- Work-loop and architect-design can invoke the installed provider when appropriate;
  absence of the optional pack degrades cleanly and never triggers raw-corpus lookup.
- Self-host adaptation measurably reduces duplicated catalogue-curation, tooling,
  `AGENTS.local.md`, scoped-guidance, and author/maintainer-guide content without
  deleting mechanical enforcement or always-loaded safety rules.
- An external non-AgentBundle pilot demonstrates that the workflows and compiled
  references remain useful without catalogue tooling assumptions.
- Authentication material stays outside model context; the portable pack names the
  isolation and bounded-authority contract without depending on a repository-specific
  credential implementation.

## Scope / Non-goals

**In scope:**

- A portable `agent-skill-engineering` pack with progressive author/update modes and a
  review/optimize workflow.
- A governed same-pack OKF corpus, deterministic compiler inputs, generated reference
  router, provenance, applicability limits, and retrieval dates.
- Skill framing, triggers, instruction density, progressive disclosure, deterministic
  helpers, portability, dependency detection, exit contracts, evaluation, fixtures,
  isolation, and observed-failure-led optimization.
- A census-backed pattern taxonomy covering knowledge providers, router/search skills,
  plugin packaging, user-profile distribution, progressive authoring modes,
  orientation/workspace resumption, and result-presentation usability.
- Python/pytest and TypeScript/Node depth where it directly serves skill scripts,
  evaluations, pack-level verification, or skill/evaluation CI.
- Execution economics at local-tool, pack, CI, multiple-worktree, managed-sandbox,
  state-lock, shared-host, and machine-load boundaries.
- Runtime-neutral security, untrusted-input handling, least authority, authentication
  isolation, and bounded tool execution.
- Portable capability floors and runtime profiles for subagents, hooks, skills,
  plugins, and agent/plugin packaging across the eight named enterprise runtimes.
- Optional integrations for work-loop and architect-design, with an explicit path for
  additional knowledge consumers.
- Self-host installation, guide migration, guidance reduction, backlog disposition,
  and an external portability pilot.

**Non-goals:**

- Moving AgentBundle manifests, adapters, projection rules, pack versions, self-host
  commands, catalogue admission, or publication policy into the portable pack.
- Building a generic CI, pytest, Node, Git, worktree, or developer-productivity pack.
- Performing runtime OKF lookup, dynamically interpreting raw OKF, permitting direct
  cross-pack raw-corpus resolution, or making the corpus executable.
- Treating Claude, Codex, or any other runtime's extension model as universal.
- Claiming adapter support merely because a runtime knowledge profile exists.
- Removing mechanical enforcement, repository governance, or always-loaded safety
  rules before measured replacement parity is established.

## Appetite

One to two quarters, delivered as seven dependency-ordered slices across M0–M5. A
slice that broadens the pack into generic developer productivity, embeds AgentBundle
mechanics in portable guidance, or requires hosted retrieval leaves this programme
until an approved amendment changes the boundary.

## Assumptions and risks

- **Broad practice is not automatically doctrine.** Local experience is rich enough
  to seed the corpus, but promotion requires repeated evidence, provenance, and an
  applicability statement.
- **Retrieval precision is a product property.** A large handbook with weak routing
  would recreate the context-load problem; router evaluation and disclosure budgets
  are delivery gates.
- **Runtime profiles decay quickly.** Every external source records its retrieval date,
  exposed version or update date, verification date, and revalidation state. Stale
  operative claims are withheld rather than guessed.
- **Composition expands the trust boundary.** Subagents, hooks, plugins, search, and
  packaged knowledge can transfer authority or untrusted content. Profiles must state
  capability, consent, isolation, and degradation behavior separately.
- **Optimization can hide correctness failures.** Test selection, caching,
  parallelism, load shedding, and lock management preserve deterministic exit and
  isolation contracts before reducing elapsed time.
- **Self-host deletion can remove orientation.** Guidance collapses only after a named
  replacement, link and retrieval checks, cold-agent task parity, and a rollback owner
  exist.

## Rabbit holes

- Do not turn work-loop into a generic knowledge retriever. It invokes a declared,
  installed provider workflow and remains useful when that provider is absent.
- Do not encode current AgentBundle paths or commands as portable engineering
  principles. Those mechanisms remain in catalogue and maintainer guidance.
- Do not merge Python and TypeScript details into a lowest-common-denominator topic;
  route to language-specific depth after establishing shared contracts.
- Do not generalize every CI optimization. Admit only patterns tied to skills,
  evaluations, packs, or their execution environments, and retain ordinary CI
  engineering with its current owner.
- Do not distribute raw credentials or credential-resolution details through the
  corpus. Teach isolation, least authority, indirection, and redaction contracts.
- Do not remove local safety guidance merely because a searchable topic exists.
  Frequently required invariants remain always loaded.

## Instrumentation

- Activation, behavioral, router-precision, disclosure-budget, determinism, path,
  dependency, exit-contract, and failure-mode evaluations for the portable workflows.
- Baseline and post-change measurements for local, pack-level, and CI elapsed time;
  process count; CPU and memory pressure; cache behavior; lock contention; retry rate;
  and test isolation.
- Multiple-worktree and shared-host fixtures covering unique state roots, stale locks,
  bounded concurrency, load detection, cleanup, and supported-profile fallbacks.
- A pattern inventory recording source packs, repeated observations, counterexamples,
  applicability limits, and promotion state.
- Runtime-profile freshness checks and a verification record naming runtime, version,
  surface, OS, date retrieved, verification date, evidence, and limitations.
- Before/after footprint accounting plus cold-agent authoring, maintenance,
  orientation, and incident-response tasks for every proposed guidance deletion.
- External-pilot evidence that distinguishes portable workflow value from the
  AgentBundle route used to distribute it.

## Decision authority

[RFC-0097](../../rfc/0097-agent-skill-engineering.md) is Accepted and governs the
product boundary, ordered follow-on cut, and acceptance conditions.
[ADR-0093](../../adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md)
governs same-pack OKF compilation. The provider-mediated cross-pack knowledge boundary
is the first new ADR owned by this programme. The planned
[agent skill engineering architecture](../../architecture/agent-skill-engineering.md)
describes the target state but remains `PLANNED` until M5 verifies every section.

## Confirmed delivery slices

The accepted RFC confirms this dependency-ordered cut. Each slice materializes through
`new-spec`, back-links this brief, and remains non-dispatchable until its canonical spec
and plan are approved and registered under `ini-009`.

| Slice | Ships | Hard predecessor |
| --- | --- | --- |
| 0 — governance and compiler prerequisites | Provider-mediated knowledge ADR; resolution of the two named OKF compiler guard prerequisites; approved delivery contracts | — |
| 1 — foundation | Portable pack; `frame`, `create`, and `update` modes; review/optimize workflow; secure deterministic router; foundational corpus and evaluations | Slice 0 |
| 2a — corpus and skill patterns | Census-backed pattern topics, governed corpus admission, topology, retrieval baseline, and `knowledge-provider` authoring mode | Slice 1 |
| 2b — languages and execution economics | Python/pytest and TypeScript/Node depth; CI, worktree, sandbox, lock, shared-host, and load-management practice | Slice 2a |
| runtime-package — deferred capability | `runtime-package` remains unavailable until its package-lifecycle claims and runtime-profile gates are complete | RFC-0097 D1, M2 availability rule |
| 3a — composition floors and pilot profile | Portable skills-plus-subagents, hooks, and plugin-package floors; the runtime capability-claim ledger with its four lifecycle states and profile roll-up; and a retrieval-dated Claude Code pilot profile | Slices 1–2 |
| 3b — runtime profiles | Retrieval-dated Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and Antigravity profiles; the router's per-claim state and roll-up reporting together with the provider response contract change it requires; the subagent-composition and hook/plugin-design behavior fixtures; and the `runtime-package` mode | Slice 3a |
| 4 — consumer integrations | Optional work-loop and architect-design invocation, explicit provider contract, clean absence behavior, and extension path for other loops | Slices 1 and 3b |
| 5 — self-host and footprint adaptation | Repository self-host install; author/maintainer-guide updates; skill/pack creation journey changes; measured collapse of duplicated guidance, tooling rationale, and catalogue-curation footprint | Slice 4 |
| 6 — pilot and closeout | External non-AgentBundle portability pilot; backlog disposition; maintenance ownership; freshness policy; architecture verification and `CURRENT` promotion | Slice 5 |

## Spec map

Status is derived from linked delivery specs rather than maintained independently
here. Remaining confirmed slices stay as typed programme work until `new-spec`
promotes and approves them.

| Spec | Status |
| --- | --- |
| `agent-skill-engineering-foundation` | Shipped |
| `agent-skill-engineering-corpus` | Shipped |
| `agent-skill-engineering-languages-and-execution` | Shipped |
| `agent-skill-engineering-composition-floors` | Implementing |

## Backlog and prerequisites

RFC-0097 owns the initial backlog disposition. Items classified as direct inputs move
into the relevant slice; conditional items remain with their current owners until a
spec demonstrates that they directly support skill scripts, evaluations, pack-level
verification, or the provider boundary. Catalogue-only and ordinary engineering work
does not move merely because the corpus can describe it.

The two foundation prerequisites were `okf-index-title-interpolation-unescaped` and
`okf012-nondeterminism-guard-untested`. Their canonical backlog records remain the
authority for exact ownership and closure, and both are now **closed** under
`[backlog].closed` by `docs/specs/okf-follow-ons/spec.md`, which bounded and escaped
compiler-owned OKF index metadata and added mutation-proven `OKF012` coverage. Slice 0
therefore inherits them satisfied rather than needing to resolve or amend them. Per
RFC-0097 D7 the canonical record wins over this planning map; the variance is recorded
in [INI-009](../initiatives/ini-009-agent-skill-engineering.md).

## Derived work

1. Record the provider-mediated knowledge ADR without reopening ADR-0093's same-pack
   build-time boundary.
2. Scaffold and approve the foundation spec and plan.
3. Materialize each later slice only when its hard predecessor and evidence inputs are
   explicit; register approved specs in `workspace.toml` through `work-intake`.
4. Keep `ini-009.work.queue` empty until an approved spec exists. A Ready brief is a
   decomposition target, not permission to dispatch implementation.
