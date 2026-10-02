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
- A retrieval-dated Claude Code reference profile exists. Every operative capability
  claim has a first-party source and a current verification record, and the shipped
  four-state lifecycle and three-value roll-up remain the admission mechanism for
  later profiles contributed as open extensions.
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
- Portable capability floors and a retrieval-dated Claude Code reference profile for
  subagents, hooks, skills, plugins, and agent/plugin packaging, with the shipped
  lifecycle and roll-up mechanism available to later open-extension profiles.
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

One to two quarters, delivered as dependency-ordered slices across M0–M5. A
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
governs same-pack OKF compilation.
[ADR-0097](../../adr/0097-knowledge-access-capability-detected-provider-mediated.md)
is Accepted and governs the provider-mediated cross-pack knowledge boundary — the
first new ADR owned by this programme, recorded in slice 0 and first consumed by
slice 4. The planned
[agent skill engineering architecture](../../architecture/agent-skill-engineering.md)
describes the target state but remains `PLANNED` until M5 verifies every section.

## Shipped so far

Eight of the twelve committed delivery slices below are delivered. The `Spec
map` carries the seven spec-backed slices; slice 0 is the delivered governance
and compiler-prerequisite slice and has no child delivery spec.

| Slice | Delivered |
| --- | --- |
| 0 — governance and compiler prerequisites | ADR-0097 recorded and Accepted. Both named OKF compiler prerequisites — `okf-index-title-interpolation-unescaped` and `okf012-nondeterminism-guard-untested` — were closed by `docs/specs/okf-follow-ons/spec.md`, so this slice inherited them satisfied. |
| 1 — foundation | The portable pack with `frame`, `create` and `update` modes, the review/optimize workflow, the deterministic generated router, and the foundational corpus with its activation and behaviour evaluations. |
| 2a — corpus and skill patterns | Census-backed pattern topics, governed corpus admission, topology accounting, the retrieval baseline, and the `knowledge-provider` authoring mode. |
| 2b — languages and execution economics | Python/pytest and TypeScript/Node depth for skill scripts, evaluations and pack verification, plus execution-economics topics for local runs, CI, worktrees, locks, shared hosts and load detection. |
| 3a — composition floors and pilot profile | The three portable composition floors (skills-plus-subagents, hooks, plugin package), the runtime capability-claim ledger, and the retrieval-dated Claude Code pilot profile — three probed capabilities and four sourced-but-unprobed. |
| 3c — subagent and plugin concepts | The portable worker-context, delegation-boundary and Agent Plugins v1 core concepts, taught in the vocabulary used by Claude agent and skill authors, with other runtime profiles retired to open extension. |
| 3e — composition behavior fixtures | The subagent-composition and hook/plugin-design behavior fixtures, each seeding defects a shipped composition floor governs and each graded blind against a retained transcript. With these two, every representative task fixture RFC-0097's Gate 2 M2 expanded measure names carries a recorded result. |
| 4 — consumer integrations | `work-loop` and `architect-design` each reach the installed provider through a bounded step that inlines its own request, addressed by contract version because ADR-0097 forbids a consumer naming a generated router. The seam's seven-value diagnostic vocabulary reaches an installed surface, both packs declare the seam, and `catalogue-authoring-standards.md` § 11 carries the obligation for the next consumer. |

Slice 3b is discarded rather than shipped; its row below is the canonical record
and states where each of its four residuals went. Four committed slices remain:
3c-r, 3d, 5 and 6. Their on-disk materialization state, current gating and
pre-spec evidence are recorded below.

## Confirmed delivery slices

The accepted RFC confirms this dependency-ordered cut. Sub-cuts within a confirmed follow-on are owner delivery-cut variances, each recorded in [INI-009](../initiatives/ini-009-agent-skill-engineering.md). Each slice materializes through
`new-spec`, back-links this brief, and remains non-dispatchable until its canonical spec
and plan are approved and registered under `ini-009`.

| Slice | Ships | Dependency rule |
| --- | --- | --- |
| 0 — governance and compiler prerequisites | Provider-mediated knowledge ADR; resolution of the two named OKF compiler guard prerequisites; approved delivery contracts | — |
| 1 — foundation | Portable pack; `frame`, `create`, and `update` modes; review/optimize workflow; secure deterministic router; foundational corpus and evaluations | Slice 0 |
| 2a — corpus and skill patterns | Census-backed pattern topics, governed corpus admission, topology, retrieval baseline, and `knowledge-provider` authoring mode | Slice 1 |
| 2b — languages and execution economics | Python/pytest and TypeScript/Node depth; CI, worktree, sandbox, lock, shared-host, and load-management practice | Slice 2a |
| runtime-package — deferred capability | `runtime-package` remains unavailable until its package-lifecycle claims and runtime-profile gates are complete. Delivered by slice 3d. | RFC-0097 D1, M2 availability rule |
| 3a — composition floors and pilot profile | Portable skills-plus-subagents, hooks, and plugin-package floors; the runtime capability-claim ledger with its four lifecycle states and profile roll-up; and a retrieval-dated Claude Code pilot profile | Slices 1–2 |
| 3b — runtime profiles | **Discarded 2026-09-01**, drafted and reviewed clean across five rounds but not shipped, against a D3 charter then under correction (RFC-0097 § Errata, 2026-09-01). Its four residuals are re-homed with none orphaned, so each Follow-on that names this row resolves here: the seven remaining runtime profiles → **open extension**, not a committed slice; the router's per-claim state and roll-up reporting with its provider response-contract change → **slice 3c-r**; the subagent-composition and hook/plugin-design behavior fixtures → **slice 3e**; the `runtime-package` mode and its corpus leaf → **slice 3d**. Those rows state the full scope of each. **This row is retained, not deleted:** the frozen `agent-skill-engineering-composition-floors` spec's ticked AC26 and its four Follow-ons resolve through it. | Slice 3a |
| 3c — subagent and plugin concepts in the authored vocabulary | The portable concepts a skill author actually needs: isolated context and what does **not** cross back out of a worker, delegation and worker boundaries, and the standardised plugin core the specification already fixes — root manifest, confinement, versioning, component failure isolation. Taught in the vocabulary this audience writes, Claude agents and Claude skills. Runtime divergence is stated as a bounded caveat where it changes an authoring decision, not as a per-vendor matrix. | Slice 3a |
| 3c-r — claim-state reporting for the shipped ledger | The router's per-claim state and roll-up reporting, and the provider response-contract change it needs, scoped to the ledger slice 3a shipped rather than to eight profiles. **Retained deliberately:** the frozen composition-floors spec's `Contract:` field assigns this obligation to "the slice that completes the eight profiles", a phrase the de-scope below orphans, so this row is where that Follow-on now resolves. | Slice 3c |
| runtime profiles beyond Claude Code — open extension, not a committed slice | The profile mechanism, four lifecycle states and roll-up that slice 3a shipped stay in place, so a later contributor can add a runtime profile without a charter change. Per-runtime compatibility stays **AgentBundle's** adapter concern, where it is already measured and tested under `packages/agentbundle/agentbundle/build/adapters/`. Duplicating it as eight maintained corpus profiles is the over-scope this row retires. | — |
| 3d — runtime-package mode | The `runtime-package` authoring mode and its `compatibility-and-runtime-package-patterns` corpus leaf, whose recorded admission condition is the runtime profiles that make packaging claims verifiable | Slice 3c — its package-lifecycle rows narrow to the one shipped profile's runtime, so Claude plugin packaging is what it can verify |
| 3e — composition behavior fixtures | The subagent-composition and hook/plugin-design behavior fixtures RFC-0097's Gate 2 M2 measure names | Slice 3a |
| 4 — consumer integrations | Optional work-loop and architect-design invocation, explicit provider contract, clean absence behavior, and extension path for other loops | Slices 1 and 3a |
| 5 — self-host and footprint adaptation | Repository self-host install; author/maintainer-guide updates; skill/pack creation journey changes; measured collapse of duplicated guidance, tooling rationale, and catalogue-curation footprint | Slice 4 (shipped) and slice 3c — guidance is not collapsed before the concepts that replace it exist |
| 6 — pilot and closeout | External non-AgentBundle portability pilot; backlog disposition; maintenance ownership; freshness policy; architecture verification and `CURRENT` promotion | Slices 3c-r, 3d, 3e, and 5 — closeout asserts M2 complete and promotes the architecture to `CURRENT`, which requires claim-state reporting, the `runtime-package` mode, the composition behavior fixtures, and the footprint adaptation to exist |

## Open slices and pre-spec evidence

The focused filesystem probe on 2026-10-01 checked every
`docs/specs/agent-skill-engineering-*` directory and every `spec.md` carrying
the `brief:agent-skill-engineering` back-link. No spec, plan, or
`["ini-009".work]` registration exists for any open slice. The table is the
current materialization and gating record: a ready row is ready for `new-spec`
authoring only, and slice 6 is not ready to author until its predecessor and
owner-input gates are true.

| Slice | Gating | `spec.md` on disk | `plan.md` on disk | Next action |
| --- | --- | --- | --- | --- |
| 3c-r — claim-state reporting | Ready to materialize: predecessor `3c` is satisfied by the Spec map | Absent | Absent | Author and approve a spec and plan, then register the spec under `ini-009` |
| 3d — `runtime-package` mode | Ready to materialize: predecessor `3c` is satisfied by the Spec map | Absent | Absent | Author and approve a spec and plan, then register the spec under `ini-009` |
| 5 — self-host and footprint adaptation | Ready to materialize: predecessors `4` and `3c` are satisfied by the Spec map | Absent | Absent | Author and approve a spec and plan; freeze the Gate 4 baseline before changing a route |
| 6 — pilot and closeout | Not ready to author: predecessors `3c-r`, `3d` and `5` still need shipped child evidence; predecessor `3e` is satisfied by the Spec map | Absent | Absent | Owner-select the admitted pilot candidate and obtain the outstanding architect-owner review while predecessors deliver; materialize the slice only when its implementation inputs are explicit |

### 3c-r probe — the missing response channel is bounded

The shipped ledger already has a pure, tested resolver for the four claim
states and three profile roll-ups. The missing surface is the provider
response. Its exact v1 validator permits only `profile`, `retrieved_at` and
`verified_at` in each `profile_provenance` item, and it requires every non-`ok`
response to carry no `topic_ids` or `guidance`. The fixture named
`stale-profile` currently exercises a **provider contract-version mismatch**;
it does not exercise a selected stale capability claim.

The spec must settle whether this is an additive v1 response change or a new
contract version; the claim identifier, claim state and profile roll-up field
shape; the identifiers-and-provenance-only response for a stale selected claim;
and the consumer compatibility cases. It must not restore the seven retired
runtime profiles.

### 3d probe — the mode and its evidence are both absent

`runtime-package` is still an explicit `unavailable` case in the author
workflow, and `compatibility-and-runtime-package-patterns` remains in the
compiled declared-absent register. The Claude Code ledger has seven current
composition rows but no complete package-lifecycle set for scope and
precedence, namespace and collision behavior, provenance or integrity,
install/update/disable/uninstall recovery, managed policy, and
authentication/secret handling. Its evidence was retrieved on 2026-08-31, so
on this probe date it is 31 days old and remains inside the declared 90-day
window.

The spec must define the mode's user-visible result, the exact Claude Code
package-lifecycle rows and probes, the topic-admission evidence, the activation
and behavior fixtures, the removal of the unavailable-mode case, and whether
any part of the mode consumes the 3c-r response rather than the ledger directly.

### Slice 5 probe — routing prerequisites are visible, parity evidence is not

The three pack skills are not present in either repository self-host projection,
`guides/agent-skill-engineering/` does not exist, the guide-index check passes
only because `agent-skill-engineering` remains in `GUIDE_OPTIONAL_PACKS`, and the
site still points at `/docs/guides/`. The Draft
[`agent-skill-engineering-guide-slice`](../intents/agent-skill-engineering-guide-slice.md)
already owns the dedicated guide, guide-index link, exemption removal and
`docsUrl` change; slice 5 should absorb or cite it rather than create a second
owner.

No Gate 4 baseline or cold-agent fixture artifact was found outside RFC-0097's
requirements. The spec must therefore record the fixed six-fixture baseline
before any routing edit, including correctness checklists, files and bytes
loaded, always-loaded line counts and predeclared severities; name the exact
self-host inclusion change and rollback; and separate per-surface routing from
the repository-wide comparison and collapse gate.

### Slice 6 probe — pilot selection and one owner review remain

A candidate has passed admission, but no owner selection has been recorded;
RFC-0097 leaves that choice with the INI-009 owner. The architecture remains
`PLANNED`. Of the thirteen legacy backlog identifiers in RFC-0097 D7, four are
closed with durable evidence and their review state recorded in the initiative:
the two slice-0 compiler prerequisites closed without a separate pre-move owner
sign-off, plus `security-checklists-okf-router-regression` and
`pre-existing-skill-spec-lint-warnings` closed with maintainer review. Eight
resolve through seven Draft intent artifacts. The architect licence defect is
fixed, but its owner review remains outstanding.

**Admission probe, 2026-10-01.** The candidate is
[`mthines/agent-skills`](https://github.com/mthines/agent-skills) at commit
`037498a077d8dae488ac0b00787a60fe69cfd499`. The probe inspected the Git tree,
MIT licence, root package manifest, all tracked skill paths, and the
`skills/authoring/create-skill` workflow, portable template, repository rules
and `validate-skill.mjs` helper. It did not execute downloaded code. The pinned
tree has 54 `SKILL.md` files, no tracked symlinks, no `AgentBundle` occurrence,
and nine skill-local `.mjs` helpers across five skill areas. The selected helper
is a zero-dependency Node 20 ESM validator: ordinary validation reads the target
and reports findings; only its separately invoked self-test creates and removes
fixtures under the operating-system temporary directory. No child-process or
network import was found.

**Verdict: admit with a bounded pilot route.** Use `create-skill`'s read-only
`review` mode against its explicit portable profile and keep its default
scaffold wiring out of scope. That default path updates this external
repository's `CLAUDE.md` and `README.md` inventories and manages a
`~/.claude/skills` → `~/.agents/skills` symlink chain, so treating it as portable
would invalidate the pilot. Slice 6 still needs the owner to select this admitted
candidate, pin the review fixture and expected findings, authorize any later
execution of the native validator in an isolated disposable copy, and define the
before/after retrieval and task-success measurements.

The eventual slice must record the owner's pilot selection, refresh the seven
Draft intents' current lifecycle states, obtain or explicitly disposition the
outstanding architect-owner review, publish the maintenance and profile-freshness
procedure, make the final M2 gate verdict, and record the verifying commit when
it promotes the architecture to `CURRENT` and closes the initiative. Do not write
the slice 6 spec until those owner inputs and predecessor delivery evidence
exist.

## The runtime-profile de-scope, and what it needs

**Owner decision, 2026-09-04.** This pack is about authoring reusable agent
skills. It is not a cross-vendor compatibility matrix, and no owner can hold
eight vendor surfaces current. Runtime profiles beyond the shipped Claude Code
one are therefore retired from committed scope and become an open extension.
Per-runtime compatibility stays with AgentBundle, which already tracks it for
its own delivery.

Subagents and plugins remain in scope, because a skill author cannot decide when
to hand work to an isolated worker without knowing that isolated context exists
and what does not come back from it. But that is a *concept*, and conceptually it
is the same across runtimes. The audience writes Claude agents and Claude skills,
so that is the vocabulary the corpus teaches; another contributor may add other
runtime guidance later.

**RFC-0097 anticipated this and chose the other remedy.** Its own drawbacks
section says: "The largest honest drawback is maintenance: a useful
runtime-profile corpus creates an obligation to track change. If no owner can
revalidate the eight initial enterprise surfaces, M1 may ship the portable
floor, but M2 remains incomplete." The RFC's fallback was to leave M2
permanently incomplete. This decision narrows the commitment instead, so M2 can
complete honestly rather than standing open against surfaces nobody is
revalidating.

### What this resolves

**The required-set tension dissolves rather than needing a fix.** The frozen
composition-floors spec's ticked **AC6** pins Claude Code's required set at
seven rows and is executably guarded — `test_runtime_capability_ledger.py`
asserts both `expected_count == 7` and `len(required["claude-code"]) == 7`,
built so that "deleting a capability from both the rows and the required set
fails rather than passing". Narrowing that set would have required amending a
frozen criterion. Under this de-scope the ledger simply is not grown, so AC6's
seven rows stay frozen and true and no amendment is needed. That is the cleanest
available resolution and it was not available under the previous cut.

**The maintenance obligation resolves.** One profile, for the runtime the
maintainers use daily, is revalidatable. Eight were not.

### How it was recorded

**RFC-0097 § Errata, 2026-09-04, Approver-signed.** The RFC is Accepted, so its
body is Frozen — `docs/CONVENTIONS.md` allows a status change but not a body
edit. Corrections are appended to § *Errata*, which is what the 2026-09-01 D3
narrowing did and what this de-scope did too: purely additive, no frozen text
altered. Four governed statements are superseded there by name rather than
rewritten in place:

| Location | Statement superseded |
| --- | --- |
| § *Decisions*, D3 cell | "profiles for eight initial enterprise runtime surfaces" |
| § *D3* | "M2 is not complete until all eight profiles are `complete-current`" |
| Gate 2 *Success* | "M2 additionally requires all eight profile documents to be `complete-current`" |
| Gate sequencing | "M2 remains incomplete until the eight-profile condition passes" |

The lifecycle apparatus is untouched: the four claim states, the roll-up values,
the verification window and the probe record still govern whatever profiles
exist. The initiative's M2 milestone row follows the erratum, and the
`rfc-candidates.md` entry that first raised this — logged as an owner challenge,
"this isn't browser compatibility" — records that the same argument has now been
carried from per-row scope to the commitment itself.

**The orphaned forward pointer is re-homed by that erratum.** The frozen
composition-floors spec's `Contract:` field assigns the router's claim-state
reporting to "the slice that completes the eight profiles", which will not
exist. The erratum re-points that obligation to the `3c-r` row above, scoped to
the ledger already shipped. The frozen spec's body is not edited; its Follow-ons
resolve through this brief's slice rows, which is the indirection built for
exactly this case.

### The divergence that justified profiling, and where it actually belongs

The per-runtime divergence is real — this repository's own adapters had to
survive it before any profile was written. Kiro IDE **silently** drops any agent
carrying a `hooks` key, so hook-wiring is replaced by a Kiro-only primitive;
Kiro CLI keeps hook-wiring and drops that primitive; Cursor and Gemini each
aggregate hooks into their own JSON with a per-runtime event-remap table, Gemini
failing closed on an unmapped event where Cursor does not; Copilot drops the
`command` primitive outright against upstream `copilot-cli#618/#1113`; and
subagent tool-allowlist models differ outright — Cursor has none, Gemini has a
real one, and Kiro ships two vocabularies for one vendor.

Skills, by contrast, project byte-equal across all six. That asymmetry is the
whole argument: the skill surface is standardised and portable, and the
divergence lives in delivery mechanics that AgentBundle already tests. The
corpus records the one authoring consequence — do not assume you can hand a
subagent a tool list — and leaves the matrix where it is maintained.

## Spec map

Status is derived from linked delivery specs rather than maintained independently
here. Remaining confirmed slices stay as typed programme work until `new-spec`
promotes and approves them.

| Spec | Status |
| --- | --- |
| `agent-skill-engineering-foundation` | Shipped |
| `agent-skill-engineering-corpus` | Shipped |
| `agent-skill-engineering-languages-and-execution` | Shipped |
| `agent-skill-engineering-composition-floors` | Shipped |
| `agent-skill-engineering-consumer-integrations` | Shipped |
| `agent-skill-engineering-composition-fixtures` | Shipped |
| `agent-skill-engineering-subagent-and-plugin-concepts` | Shipped |

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
4. Keep `ini-009.work.queue` empty until an approved spec exists. This brief is a
   coordination artifact, not permission to dispatch implementation.
