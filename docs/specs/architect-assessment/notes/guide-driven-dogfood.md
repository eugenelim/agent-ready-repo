# Guide-driven architecture-assessment dogfood

Date: 2026-08-21

Method: the request from
`guides/architect/how-to/assess-a-repository.md` was used verbatim against three
committed fixture repositories. The optional profiler ran read-only with Git
history disabled and wrote JSON only under
`/private/tmp/architect-assessment-dogfood/`. Its `partial` status is retained:
history was deliberately unavailable. The assessor then applied the documented
Map, Focus, Investigate, Act, and Close method manually; no repository code was
executed.

Request for every run:

> Assess architecture and provide an action plan.

These captures are methodological pressure tests, not claims about a production
system. The fixtures make evidence small enough for every assertion to be
inspected.

## Run A — small Python library, no enterprise surface

Target: `packs/architect/tests/skills/architect-assess/testdata/repos/small-library/`

Primary intent: baseline/understanding

Mode: standard

Enterprise mode: none detected

### Bottom line

The fixture is a single-package library with a narrow public contract and clear
internal signing boundary. The main attention area is not file structure or
coupling; it is negative-path contract confidence. The implementation contains
explicit invalid-signature and unsupported-version behavior, while the only
test exercises a successful round trip. No production defect is established.

### Conceptual current state

- Context: callers use `token_codec.encode` and `token_codec.decode`; no network
  or external runtime is present.
- Deployable/runtime: one Python library, not a service or distributed system.
- Module/capability: `__init__.py` exposes the codec; the codec owns version
  framing; signing owns HMAC mechanics.
- Data/interaction: strings and caller-supplied key bytes remain in process.
- Delivery/operations: `pyproject.toml` and a pytest directory exist; CI,
  release automation, runtime configuration, and operations are not present.
- Trust/identity: key handling crosses the public API; storage and rotation are
  caller responsibilities and outside this fixture.

Map checkpoint correction: **accepted with `continue`**. The initial hypothesis
that `src/` and `tests/` were separate components was rejected; they are source
and verification surfaces for one library.

### Evidence coverage

| Surface | Status | Pointer / limit |
| --- | --- | --- |
| Documentation | observed | `README.md` |
| Source | observed | four Python modules/files |
| Tests | observed, thin | `tests/codec_contract.py`; round trip only |
| Manifests/dependencies | observed | `pyproject.toml` |
| CI/CD | missing | no definition |
| Deployment/release/IaC | not applicable / missing release evidence | library shape |
| Schemas/migrations | not applicable | no durable data |
| Runtime configuration | not applicable | caller supplies key |
| Operational evidence | not applicable | no service runtime |
| Read-only history | unavailable by test choice | profiler ran with `--git-commits 0` |

### Attention heat map

| Area | Consequence | Pressure | Concentration/coupling | Verification weakness | Ops/data/security exposure | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Public codec contract | medium | low | medium | high | medium | high |
| Signing implementation | high | low | low | medium | high | high |
| Packaging/release | medium | unknown | low | unknown | low | moderate |

Legend: heat selects drill-down priority. It is not proof of a defect and is
not finding severity.

Focus checkpoint correction: **accepted H-1, public codec contract; removed a
proposed “large signing module” hotspot** because the profiler showed only 448
bytes and no concentration consequence.

### Hotspot drill-down

H-1 role: public compatibility and integrity boundary.

Signals: the exact AST path is public API → codec → signing. Source explicitly
raises for invalid signatures and versions; the test observes only round-trip
success. Counter-evidence: the implementation uses `hmac.compare_digest` and
keeps signing behind the codec. Scenario: corrupted, forged, or future-version
token reaches `decode`. Unknown: release compatibility policy and key lifecycle.

### Findings, strengths, and unknowns

F-A1 — **Negative public-contract behavior is unverified.** Classification:
change-safety risk. Mechanism: invalid signature and unsupported-version
branches can change without a failing contract test. Consequence: callers may
receive incompatible failure behavior or accept a regression at the integrity
boundary. Severity: minor; confidence: high. Counter-evidence: branch behavior
is explicit and simple. Smallest safe response: add focused invalid-signature,
malformed-token, and unsupported-version contract tests before changing the
wire format.

Strengths retained: narrow public exports, one-directional internal imports,
constant-time signature comparison, and no invented distributed architecture.

Unknowns: supported-version policy, packaging matrix, and caller key handling.

### Action waves

Wave A0 — prove the public failure contract. Includes F-A1. Prerequisite: decide
the supported exception and compatibility behavior. Completion proof: negative
contract tests fail on a planted acceptance/exception regression. Rollback:
tests only. Owner class: library maintainers. Non-goal: introduce services,
storage, or a generic architecture gate.

Next decision: define whether unsupported versions are permanently rejected or
need a migration decoder.

Pack knowledge used: foundations, baseline intent, library/SDK shape,
testability/change safety, and security/trust boundary concepts. Enterprise
context: none. Target evidence alone supports the observation.

## Run B — layered web/worker application, in-repo enterprise documentation

Target: `packs/architect/tests/skills/architect-assess/testdata/repos/layered-app/`

Primary intent: hardening/risk reduction

Mode: standard

Enterprise mode: in-repo `docs/architecture/reference.md`

### Bottom line

The fixture contains an API route and recovery worker sharing one order-store
adapter. The strongest hardening finding is the worker's explicit empty tenant
argument, which conflicts with both the store contract and the in-repo rule that
every order-store operation carry tenant context. The direct route-to-query
import is a separate medium-confidence control-bypass risk, not proof that a
service-class refactor is automatically correct.

### Conceptual current state

- Context/runtime: the web route and recovery worker are separate entry paths;
  the fixture does not prove separate processes or a deployed database.
- Module/capability: route and worker both call `data.queries.save_order`.
- Data/trust: `save_order` requires `tenant_id`; the route supplies one and the
  worker supplies an empty value.
- Delivery: CI invokes pytest. Deployment, schema, transaction, and operations
  evidence are absent.

Map checkpoint correction: **the phrase “three-layer runtime” was corrected**.
Folders express intended code organization; only two entry paths and one store
interface are observed. The corrected map was accepted with `continue`.

### Evidence coverage

| Surface | Status | Pointer / limit |
| --- | --- | --- |
| Documentation | observed | README and `docs/architecture/reference.md` |
| Source | observed | route, worker, query adapter |
| Tests | observed, partial | `tests/orders_contract.py`; route happy path only |
| Manifests/dependencies | observed | `pyproject.toml` |
| CI/CD | observed | `.github/workflows/ci.yml` |
| Deployment/release/IaC | missing | no topology proof |
| Schemas/migrations | missing | store implementation absent |
| Runtime configuration | missing | no environment evidence |
| Operational evidence | missing | no row counts, logs, incidents, or recovery exercise |
| Read-only history | unavailable by test choice | profiler `--git-commits 0` |

### Attention heat map

| Area | Consequence | Pressure | Concentration/coupling | Verification weakness | Ops/data/security exposure | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Recovery worker → order store | high | medium | medium | high | high | high |
| Route → order store | high | medium | medium | medium | high | moderate |
| Store behavior | high | unknown | high | high | high | low |

Legend: heat selects drill-down priority, not proof or severity.

Focus checkpoint correction: **investigate the recovery path first; retain the
route import as H-2 and do not broaden into all layering cleanup**.

### Hotspot drill-downs

H-1 recovery path: `recover(order_id)` calls `save_order("", order_id)`.
Counter-evidence: the adapter signature requires tenant context and the route
does supply it. Scenario: a recovery attempt for one tenant begins without a
tenant principal. Unknown: whether the real store rejects, no-ops, or mis-scopes
the operation; no schema or integration test can close that gap.

H-2 route path: the route imports the query adapter directly. The local
foundation says routes call application use cases. The target source proves the
bypass, while consequence remains inferred because authorization and transaction
behavior are not implemented in the fixture.

### Findings, strengths, and unknowns

F-B1 — **Recovery crosses the store boundary with missing tenant context.**
Classification: identity/isolation defect in the fixture contract. Mechanism:
the worker manufactures an empty tenant at the protected data call. Consequence:
the operation can fail silently, affect the wrong scope, or rely on undefined
adapter behavior. Severity: blocker for release; confidence: high that context
is missing, low on the exact store outcome. Validation gap: operation-specific
store/VPD integration behavior. Smallest safe response: reject empty context
before store access and carry immutable job tenant plus service/actor identity.

F-B2 — **The route bypasses the documented application boundary.**
Classification: policy/transaction bypass risk. Mechanism: transport code calls
the store adapter without an observed use-case boundary. Consequence is not yet
proven. Severity: minor; confidence: moderate. Smallest response: characterize
the path, identify which authorization/transaction decisions belong in the use
case, then migrate only if that boundary does real work.

Strengths: tenant is an explicit store parameter; CI and a happy-path test
exist; in-repo intent is visible and is not mistaken for runtime proof.

### Action waves

Wave B0 — contain and prove tenant context. Includes F-B1. Add fail-before-store
validation and store-policy tests for missing, wrong, correct, and privileged
identities; assert expected affected rows. Completion proof: cross-tenant and
missing-context tests plus a duplicate recovery test. Rollback: disable recovery
or restore the prior worker while preserving a containment guard. Owner class:
worker/data maintainers. Non-goal: generic layering refactor.

Wave B1 — make entry context structural. Centralize background execution context
and pass tenant, actor/service principal, job/run, trace, and scope. Depends on
B0 evidence. Completion proof: every protected entry path rejects missing
context and emits correlated audit fields.

Wave B2 — modernize the route boundary by risk. Includes F-B2 only after
characterization. Completion proof: preserved HTTP, authorization, transaction,
and side-effect behavior. Non-goal: forwarding-only service classes or
file-count targets.

Enterprise context used: in-repo constraints/standards and local patterns.
Target evidence proves the missing argument; the document supplies intended
fitness, not the observation.

## Run C — agentic knowledge platform, authorized private retrieval fixture

Target: `packs/architect/tests/skills/architect-assess/testdata/repos/agentic-platform/`

Primary intent: hardening/risk reduction

Mode: standard

Enterprise mode: authorized connector-shaped fixture at
`testdata/enterprise/private-retrieval-response.json`

Authorization record: the surface identified its governed destination and
authorization boundary; the assessor proposed two areas—current system
landscape and local patterns/reference architectures—and the fixture user
explicitly authorized that bounded query before its contents were read. The
result remained attributed context and was not copied into the OKF corpus.

### Bottom line

The fixture's README calls the runs durable, but the implemented path is one
in-process function chain with no run/step persistence, recovery, retry,
cancellation, approval, or audit semantics. Knowledge retrieval accepts no
tenant context or provenance contract; model access carries no policy metadata;
tool execution has no observed authorization/approval boundary. This is an
agent-runtime and knowledge-platform assessment, not merely a backend layering
or raw-client audit.

### Conceptual current state

API → in-process run function → unscoped retrieval → raw model function → tool
executor. Tenant enters at the API and is passed only to the tool executor. No
durable state/store, worker, queue, model provider, knowledge index, credential
resolver, or telemetry backend is implemented in the fixture.

Map checkpoint correction: **“durable research run” was downgraded from observed
to reported**. The README is documentation; source shows an in-process chain.
The corrected map was accepted with `continue`.

### Evidence coverage

| Surface | Status | Pointer / limit |
| --- | --- | --- |
| Documentation | observed | README; private context separately attributed |
| Source | observed | API, run, knowledge, model, tool modules |
| Tests | observed, very partial | `tests/model_contract.py`; model happy path only |
| Manifests/dependencies | observed | `pyproject.toml` |
| CI/CD | missing | no definition |
| Deployment/release/IaC | missing | no runtime topology |
| Schemas/migrations | missing | no durable run/knowledge schema |
| Runtime configuration | missing | no model/tool/knowledge policy config |
| Operational evidence | missing | no traces, evals, incidents, recovery tests |
| Read-only history | unavailable by test choice | profiler `--git-commits 0` |

### Attention heat map

| Area | Consequence | Pressure | Concentration/coupling | Verification weakness | Ops/data/security exposure | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Run lifecycle/recovery | high | high | high | high | high | high |
| Knowledge retrieval | high | high | medium | high | high | high |
| Tool action | high | high | medium | high | high | high |
| Model access | medium | high | medium | high | high | high |
| End-to-end evaluation/trace | high | high | high | high | high | high |

Legend: heat selects investigation priority; it does not prove a defect or
assign severity.

Focus checkpoint correction: **retain all five agentic contracts, but investigate
the side-effect and cross-tenant paths before model-provider details**. Accepted
with `continue`.

### Hotspot drill-downs

Normal path: API passes tenant/question; retrieval receives only question; model
receives question/chunks; tool receives tenant/action. The tenant, run, trace,
privilege, provenance, model version, and policy outcome are not carried end to
end.

Side-effect path: model output becomes a tool action with no declared
permission, approval, reversibility, allowed destination, credential class,
audit, or idempotency contract.

Failure/recovery path: no state transition exists before or after retrieval,
model, or tool activity; a process loss after an external action has no durable
record from which to decide whether replay is safe.

Private enterprise context says the local pattern requires a validated execution
context at model, knowledge, and tool boundaries and says vector retrieval must
use a shared tenant-scoped service. That context establishes local fitness. The
missing parameters and state are still proven from target source.

### Findings, strengths, and unknowns

F-C1 — **Reported durability has no implemented run-state mechanism.**
Consequence: process loss or redelivery cannot determine whether a side effect
occurred, so recovery may abandon or duplicate action. Severity: blocker for a
durability/readiness claim; confidence: high. Smallest response: define durable
run/step states and idempotency/lease semantics before enabling mutating tools.

F-C2 — **Knowledge access lacks tenant and provenance contracts.** Retrieval
accepts only a question and returns strings. Consequence: the boundary cannot
demonstrate tenant/ACL isolation, source/version provenance, deletion, freshness,
or prompt-injection trust classification. Severity: blocker for multi-tenant
readiness; confidence: high on missing contract, unknown on real backing service.

F-C3 — **Tool execution lacks an authorization and approval boundary.** Model
output flows directly to `execute`. Consequence: requested action and permitted
action are not independently decided or audited. Severity: blocker for mutating
tools; confidence: high. Smallest response: disable mutation or require an
allowlisted, audited policy decision and approval token.

F-C4 — **Model access has no observed policy middleware.** No tenant/run trace,
budget, safety/PII, timeout/cancellation, model/prompt version, or usage outcome
crosses the boundary. Severity: major; confidence: high for the fixture.

F-C5 — **No end-to-end evaluation or trace evidence exists.** The only test
asserts a fixed model result. Severity: major; confidence: high. Unknowns include
provider behavior, shared platform enforcement, credential resolution, and
operational controls outside the fixture.

Strengths: module boundaries make the missing contracts visible; tenant reaches
the tool call rather than disappearing entirely; the report refuses to turn
private context into target evidence.

### Action waves

Wave C0 — contain side effects. Includes F-C1/F-C3. Keep tools read-only or
disabled until authorization, approval, audit, and idempotency exist. Completion
proof: denied and duplicate-delivery tests cause no external mutation. Rollback:
restore the read-only capability set. Owner class: agent runtime/tool platform.

Wave C1 — introduce one validated execution context and durable run semantics.
Includes F-C1. Carry tenant, actor/service principal, run, trace, and privilege
scope through state transitions and leases. Fault-inject after action/before
persistence, duplicate delivery, cancellation, and lease expiry.

Wave C2 — enforce model, knowledge, and tool platform contracts. Includes
F-C2/F-C3/F-C4. Use the governed tenant-scoped knowledge service; return
provenance/freshness/ACL/trust fields; wrap model capability/provider paths in
common policy; resolve credentials at execution time.

Wave C3 — prove end-to-end behavior. Includes F-C5. Correlate request → run →
step → retrieval → model → tool decision → tool execution, and add isolation,
recovery, policy, provenance, and quality evaluations. Non-goal: broad file
splitting or provider-specific rewrites without decision evidence.

Next decision: whether mutating tool capability is required for the first
production boundary; that determines containment and approval depth.

## Cross-run pressure-test result

The same method produced materially different maps and actions:

- the library stayed at public-contract/change-safety altitude;
- the layered application prioritized a concrete identity-context path before
  boundary modernization;
- the agentic platform expanded into run, model, tool, knowledge, evaluation,
  and trace contracts rather than stopping at imports or client compliance.

All three runs kept profiler signals separate from findings, retained missing
evidence, used both correction points, and distinguished target evidence,
enterprise context, and pack knowledge. The generic prompt therefore did not
collapse into a docs, folder, dependency, code-smell, or compliance audit.

What remains documented but not exercised: a real private connector, production
runtime/operational evidence, stakeholder interviews, project-native analyzers,
and deep experiments. Those require an authorized environment and cannot be
simulated as completed evidence.
