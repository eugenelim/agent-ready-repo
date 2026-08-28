# Work intake and artifact routing

## 1. Purpose and boundary

`work-intake` is the neutral local front door for raw, ambiguous, acquisition,
refresh, and intake-safety requests. Status and explicitly named artifact or
work-type requests route directly to their owner. For durable classified input,
it writes the canonical artifact before its lifecycle entry and dispatches only
after both are valid. An eligible explicit direct-light request remains
session-local.

Tracker adapters acquire and normalize; they do not classify artifacts or write
repository state. `workspace-status` reads and reconciles repository state and
owns the temporary reviewed migration transaction for accepted legacy entries.
Configured refresh processors compare tracker-origin artifacts and may apply
authorized local changes or separately confirmed coordination actions.

`work-loop` owns implementation and returns bounded completion evidence.
`close-work` owns the later inventory, whole-surface freshness audit, lifecycle
projection, disposition intent, initiative settlement, lifecycle records in
`docs/lifecycle/`, and any separately confirmed immediate effect. It is the only
writer of cooling state. `workspace-status` may project closeout blockers and
next actions, but it never distils context, selects policy, or mutates closeout
state.

The same boundary owns a shared read-only semantic-surface resolver. Callers
supply bounded candidates; the resolver applies repository policy and
established adopter conventions without assuming catalogue paths, requiring a
configuration file, or fetching external locators.

Architecture and governance workflows consume that boundary by semantic role,
not by catalogue filename. Proposed or future design requests
`architecture-design`; the implemented system and accepted boundary changes
request `current-architecture`; ADRs or equivalent records request
`decision-record`. These roles remain independent of product truth, user
documentation, and product or release history. Architect and governance own the
artifact methods after resolution; work intake owns only the shared repository
destination result.

An upstream shaping workflow may offer one optional closed handoff inside
`normalized-intake.v1`. The object adds boundaries, non-goals, dependencies,
design context, and delivery questions. Existing content and source fields keep
the outcome, assumptions, evidence, locator, revision, and proposed authority.
Absence of the object is standalone Core and follows the existing routes.

## 2. Entrypoints

- `work-intake` selects direct-light, intent, brief, spec, defect,
  Draft-with-gaps, remember, status, or refresh behavior.
- `intake-intent` creates or admits the minimum repository intent.
- `author-delivery-brief create` turns raw multi-spec or cross-repository input
  into a Draft coordination brief; `continue` makes an existing brief Ready and
  confirms spec slices.
- `workspace-status` reports canonical ready, active, blocked, shipped,
  authority, refresh, reconciliation, retained legacy state, and read-only
  closeout orientation.
- `close-work` pauses resumable work, verifies delivery evidence and durable
  semantic owners, recommends one of RFC-0096's six dispositions, and owns
  separately authorized coordination or immediate-disposal effects.
- Jira, Jira Align, GitHub, and Linear intake adapters emit the same strict
  normalized contract and delegate the route.
- Profile refresh processors resolve by exact profile ID/version and return a
  closed comparison/effect result.
- `capture-work` is a temporary compatibility alias that emits a deprecation
  notice and forwards to `work-intake` without separate semantics.
- `surface_resolver.py` resolves one semantic role from caller-supplied local or
  external candidates and returns provenance, capability, confinement, and
  independent authority facts without lifecycle effects.
- Architect consumers have four explicit modes. Chat-only writes nothing;
  personal-workspace confines writes to an exact user-confirmed root or file;
  compatible repository mode consumes the real resolver result; repository
  handoff mode names bounded evidence without claiming a Wave 1 result.
- `route_handoff` admits only a validated, resolved delivery brief or delivery
  contract. It returns an existing processor or a stable zero-effect stop; it
  does not materialize, register, or dispatch.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Canonical requirements and decisions | `docs/product/`, `docs/specs/`, and other registered artifact paths | Owning artifact workflow | Processors, reviewers, reconciliation |
| Lifecycle index | `workspace.toml` | `work-intake`, selected workflows, and reviewed migration/repair effects | `workspace-status`, execution, review |
| Tracker-origin authority | One closed `source-authority.v1` block in the canonical artifact, mirrored by structured workspace source fields | Accepted intake/refresh workflow | Refresh and reconciliation |
| Refresh receipts | Authority block plus guarded artifact/workspace pair | Exact configured refresh processor | Status and later refresh |
| Migration ledger | `.workspace-migrations.json` | Authorized `workspace-status` migration transaction | Recovery, rollback, audit |
| Selection and confirmation | Human-authored repository-relative JSON supplied out of band | Human reviewer/approver | Migration planner/effect only |
| Direct-light decision record | Active session only | `work-loop` | Requester and current session |
| Completion evidence handoff | Active closeout invocation or stable evidence owner named by the delivery run | `work-loop` produces bounded references; no closeout authority | `close-work` and reviewers |
| Pause overlay | Existing resolved writable shaping or build coordination surface | `close-work`, after exact write authority | Resume path and status projection |
| Dependency-scoped completion receipt | Existing compatible coordination surface while a live dependency cites it | `close-work`, after exact write authority | Dependent work and closeout |
| Cooling lifecycle record | `docs/lifecycle/<delivery_id>.json` | `close-work` | Day-30 review and status projection |
| Semantic-surface resolution result | Active invocation only | none; resolver is read-only | Requesting workflow and reviewer |
| Optional shaping handoff | Validated `normalized-intake.v1` envelope in the active invocation | Upstream producer owns offered content; Core owns validation and admission | `work-intake`, then the selected existing processor |

`workspace.toml` indexes artifacts and lifecycle facts. It is not a
requirements store. Target entries contain exactly `path`, `kind`, `source`,
`summary`, and `needs`; comments, summaries, order, labels, and hints cannot
select a route, satisfy a dependency, or authorize dispatch.

Durable product intent, rationale, user promises, current architecture,
interfaces, operations, maintainer procedure, release history, and reusable
learning remain in their established semantic owners. Specs and plans coordinate
delivery; code and tests prove executable capability. Neither is a universal
substitute for the other. A delivery record may leave only after `close-work`
verifies that every lasting fact has reached its owner and the affected human
surfaces remain coherent as wholes.

## 4. Dependencies and allowed edges

Source adapters may acquire and normalize external input. Only `work-intake`
classifies that input. Artifact processors receive the selected route after the
artifact and workspace state exist; they do not reconstruct a contract from
index prose. Refresh processors receive an existing registered artifact, exact
profile identity, lifecycle, authority, and revision pair.

Repository-origin work is locally authoritative. Tracker-origin work has a
closed per-field `source`/`local` ownership map and compared/accepted revisions.
Lifecycle locks and explicit decisions govern local refresh. A remote tracker
coordination action is a separate effect with its own fresh exact confirmation;
neither tracker content nor intake authorization can approve it.

Semantic candidate acquisition is caller-owned. The resolver accepts no more
than 32 closed candidates or four evidence records per candidate. Optional
configuration adapters normalize into that same record shape and gain no
authority merely by being configured. Only repository-path candidates enter
realpath confinement; external locators remain opaque and offline.

The architecture consumers keep a strict ownership edge:

| Semantic role | Content owner after resolution | Catalogue fallback is only evidence |
| --- | --- | --- |
| `architecture-design` | Architect design or future-proposal workflow | Per-effort design location |
| `current-architecture` | Architect current-state or repository adaptation workflow | `docs/architecture/` |
| `decision-record` | Governance `new-adr` workflow | `docs/adr/` |

`init-project`, `adapt-to-project`, `new-package`, and `generate-iac` may request
one of these destinations because their existing methods create or update that
artifact. They pass the complete result to the content owner rather than
copying resolver or authoring logic. A boundary change can therefore produce
separate current-architecture and decision-record handoffs without producing a
product artifact.

Product-engineering owns producing the optional bounded handoff only after its
existing confirmed delivery gate. It imports no Core implementation and has no
mandatory Core dependency. One independently shippable feature is a delivery
contract; multi-spec or cross-repository work is a delivery brief. Core owns
classification, resolution, admission, and the receiving processor. An
explicitly compatible invocation receives the machine object; older, unknown,
or absent Core receives portable rendered data from the producer.

Repository handoff content crosses one additional read boundary after
resolution: a confined regular-file read that rejects symlinks, reparse points,
multiple hard links, non-regular files, oversized content, post-resolution
identity changes, and paths outside the repository root. External handoff
content crosses no read boundary. It is reusable only when the current trusted
invocation already supplies bounded content at the matching pinned revision.

## 5. Primary flows

1. An adapter or local request produces validated normalized intake.
2. `work-intake` classifies the content. Direct-light stays session-local;
   durable routes materialize the artifact, then register its target entry.
3. `workspace-status` reconciles the artifact, membership, plan, provenance,
   authority, dependencies, and lifecycle. Only canonical ready or active specs
   may start or resume the work-loop.
4. Every workspace-dispatchable, queued, or resumable build item resolves to an
   existing durable `spec.md` and sibling `plan.md`; execution receives those
   files rather than tracker payloads or index comments. An explicit
   direct-light request is session-local, creates no workspace entry, and is
   ineligible for argless dispatch or fresh-session resumption.
5. Refresh resolves the exact configured processor, acquires and compares one
   source revision, presents field decisions, and applies guarded local changes
   only after authorization. Remote coordination remains separately confirmed.
6. A supported legacy membership stays visible and non-dispatchable until a
   human supplies a reviewed route selection. Planning is read-only; apply is
   ledger-first; rollback restores the exact legacy slice without deleting the
   canonical artifact.
7. A semantic destination request resolves an explicit destination first,
   unless mandatory repository policy rejects it; then declared repository
   policy or optional configuration, established repository convention, and an
   established external destination. Equally ranked non-equivalent candidates
   require confirmation. Contradiction or unsafe confinement is a refusal;
   absence offers destination selection or creation but performs neither. None
   of these outcomes changes lifecycle state.
8. An optional shaping handoff validates before content reads or effects. A
   resolved delivery contract continues through `new-spec`; a resolved delivery
   brief continues through `author-delivery-brief continue`. Those processors retain their
   assumption, Ready, slice-confirmation, spec, plan, and human approval gates.
9. Before implementation, a durable spec maps applicable lasting facts to
   resolver-selected owners and names stale current surfaces as plan work. A
   user-facing change drafts its established user documentation first when that
   surface exists.
10. `work-loop` implements the accepted contract and returns bounded evidence:
    accepted outcome, implemented scope, gates, durable-output status, stable
    references, obligations, dependencies, completion event, and independent
    authority facts. It does not close or disposition the work.
11. `close-work` reacquires evidence, inventories the plan's Design/LLD and
    implementation findings, and requires human whole-surface freshness review.
    Unowned non-inferable truth, a stale surface, or a live obligation blocks.
12. A pause preserves Ready or Implementing state through a reference-only
    restorable overlay in an existing writable surface. Closeout does not start.
13. A completed, abandoned, or superseded item moves through Closeout-pending
    only under `close-work`. For `cool-30-days`, it enrols cooling state in `docs/lifecycle/`, computes
    the review date, and answers dueness from an injected instant. Disposition is intent,
    never deletion permission; every persisted effect needs a separately resolved authority
    fact and fresh human confirmation bound to the exact current
    resource and evidence.
14. Initiative coordination can settle independently from artifact retention.
    An RFC or decision family may remain anchored after its terse workspace entry
    leaves. A completion receipt keeps only delivery ID, outcome, completion
    event, and evidence reference while a live dependency needs it.

Classification routes an explicit start to exactly one durability class:

```text
explicit start
    |
validate and classify
    |
    +-- direct light --> work-loop from current request
    |
    +-- durable single slice --> spec + plan --> workspace --> work-loop
    |
    +-- multi-slice outcome --> brief --> confirmed specs + plans
```

The end-to-end pipeline those classes execute in:

```text
source adapter ── normalized-intake.v1 ──> work-intake
                                                |
              +---------------------------------+------------------+
              |                                 |                  |
        direct-light                    artifact + index       status/refresh
        (session only)                         |                  |
                                               v                  v
                                        processor/work-loop   workspace-status
```

The optional producer seam composes above that unchanged pipeline:

```text
confirmed shaping gate
        |
        +-- compatible Core --> bounded handoff --> work-intake admission
        |
        +-- absent/older Core --> portable rendered handoff

work-intake admission
        |
        +-- delivery contract --> new-spec
        +-- delivery brief ----> author-delivery-brief continue
        +-- ambiguity/refusal --> stable zero-effect stop
```

## 6. Failure and recovery behavior

Missing, malformed, duplicate, unsafe, or inconsistent state becomes a stable
non-dispatchable reconciliation finding with one safe next action. An
unavailable or version-mismatched refresh processor performs no mutation.
Unresolved authority or lifecycle conflicts stop before an artifact write.

Migration serializes through `.workspace-repair.lock`, rechecks the workspace,
ledger, selection, and artifact fingerprints inside the lock, and consumes
fresh authorization before effects. A durable `pending` or `rollback_pending`
operation is recovered from the ledger. A concurrent change or malformed
ledger fails closed; canonical artifacts and unknown/private TOML extensions
are never deleted or silently rewritten.

A locator-only workspace entry is contract-valid and visible, but it stops at
`configuration_mismatch` before local artifact access or dispatch. An unsafe
local candidate, symlink escape, symlink loop, or mandatory-policy conflict
returns a stable refusal without raw exception text.

Handoff admission also stops on incomplete bounded content, confidentiality or
mandatory-policy conflict, source or revision mismatch, forged/non-resolved
resolver data, and unacquired external content. No handoff result changes
lifecycle state. Dependencies carried in the handoff remain context until the
existing workspace contract separately admits and satisfies them.

Closeout fails closed when a durable destination is ambiguous or stale, a lasting
fact exists only in the delivery container, a compatible pause/receipt surface is
absent, or source, write, and deletion authority do not independently support the
requested action. Disposition never supplies authority. Every immediate deletion
re-resolves, confines, enumerates, fingerprints, and checks source-state evidence
before effect; drift expires confirmation. Committed removal is an ordinary
reviewed change and never a history rewrite.

Wave 5 has shipped the lifecycle record, review-date, due-state, and retirement engine.
It requires the platform time-zone database for `zoneinfo`; if a named zone is
unavailable, it returns `unknown-timezone` with no UTC fallback.
Wave 6 and 7 own ordinary-context exclusion and historical migration and pruning behavior.

## 7. Observability, evidence, and the compatibility window

`workspace.toml`, canonical artifacts, and `workspace-status` provide the
observable routing and lifecycle record. Provenance records the source locator
and revision without copying credentials or a tracker payload.

Closeout evidence is layered. Stable source, test/eval, gate, review, and release
references prove capability and chronology; current semantic owners preserve the
human meaning that those references cannot reconstruct. Pause overlays and
completion receipts contain references only, never copied contracts, transcripts,
credentials, personal identity, or embedded instructions.

Each resolved semantic-surface result reports its role, logical and physical
locator, bounded evidence, availability, writability, confinement, revision or
fingerprint when known, confirmations, and source/write/deletion authority as
independent facts. Non-resolved results omit selected locators and make those
facts explicitly unknown.

All current writers and the workspace seed emit only target entries. The
accepted legacy reader and `capture-work` forwarding alias remain installed in
the initial delivery. Their later removal is a separate, non-dispatchable
follow-up gated by RFC-0083's release count, elapsed time, advance notice,
fixture/writer/guide/rollback evidence, and check-before-effect Approver
authorization.

Rollback returns writers to the preceding dual-reader release and uses the
ledger to restore legacy workspace representation. It preserves target
artifacts and migration evidence.

## 8. Mechanical invariants and evaluation

- JSON Schemas own normalized intake, target entries, authority/refresh,
  migration selection/confirmation/ledger/result, and semantic-surface
  resolution shapes.
- Reconciliation owns stable finding codes and never makes legacy entries
  dispatchable by inference.
- The integrated routing matrix runs acquisition, normalization, routing,
  authority/refresh, and read-only migration planning across Jira, Jira Align,
  GitHub, and Linear in two clean roots; canonical results and next actions must
  be byte-identical.
- Pack/plugin versions move together for non-cosmetic pack changes. Self-hosted
  projections and marketplace metadata are generated from pack sources.
- Marketing builds before docs, followed by emitted-link validation.
- The semantic-surface completion matrix enumerates every resolution outcome
  and is compared deterministically against the resolver's own results.
- The shaping-handoff completion matrix runs twice, covers compatible,
  standalone, and legacy pack pairings plus every routing/refusal class, and
  fingerprints its filesystem before and after to prove zero effects.
- The architecture-decision portability matrix calls the real resolver for
  custom repository and external destinations, mandatory-policy rejection,
  ambiguity, absence, and the boundary-change dual output. It pins the resolver
  and published schema bytes so consumers cannot widen Wave 1 by accident.
- The close-work matrix pins the same resolver and canonical file-safety helper,
  crosses all lifecycle/disposition/refusal paths, proves exact single-use
  authority and drift behavior, and checks pause, receipt, initiative, and
  read-only status projection without adding a Wave 5–7 schema. Current detail
  lives in [`close_work.py`](../../packs/core/.apm/skills/close-work/scripts/close_work.py),
  its [behavior tests](../../packs/core/tests/skills/close-work/), and the
  [maintainer how-to](../../guides/core/how-to/close-and-disposition-work.md).

These skill scripts run in the finish-time checklist and can run as fail-closed
CI gates where a PR event and Python exist. They do not fail closed inside an
arbitrary adopter repository.

- `lint-spec-status.py` checks `docs/specs/*/spec.md` metadata against the
  status contract in `CONVENTIONS.md` §4.
- `lint-traceability.py` flags structural orphans across the product chain.
- `lint-brief-coverage.py` rolls each brief's Spec map from `Brief:` back-links
  and requires a non-empty map of shipped specs for delivery.

Maintainer procedures live in
[Maintaining work intake, refresh, and legacy migration](../guides/reference/work-intake-maintenance.md).

## 9. Relevant decisions

- [RFC-0083 — Work intake and artifact routing](../rfc/0083-work-intake-and-artifact-routing.md)
- [RFC-0096 — Portable delivery-artifact lifecycle](../rfc/0096-portable-delivery-artifact-lifecycle.md)
- [ADR-0009 — Product brief layer and plan-owned LLD](../adr/0009-product-brief-layer-and-plan-owned-lld.md)
- [ADR-0019 — Product intent ontology and brief projection](../adr/0019-product-intent-ontology-and-brief-projection.md)
- [ADR-0033 — Intent-level open recognized set decoupled from scale](../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md)
- [ADR-0077 — Feature projection and tracker authority](../adr/0077-feature-projection-and-tracker-authority.md)
- [ADR-0078 — Standalone intake and deterministic workspace index](../adr/0078-standalone-intake-and-deterministic-workspace-index.md)
- [ADR-0092 — Direct-light execution is session-local](../adr/0092-direct-light-execution-session-local-boundary.md)
  — the decision this page's §5 invariant records; it refines ADR-0078's
  start-route materialization rule for captured and indexed items while leaving
  its workspace-entry dispatchability rule unchanged.

## 10. Last verified surface

Core `2.15.0`, against neutral intake precedence, repository-intent admission,
delivery-brief create/continue, the normalized-intake handoff, semantic
resolver, `work-loop` evidence handoff, `close-work` source, cooling source and
tests, lifecycle record documentation, workspace projection, pack metadata,
evaluation, and documentation surfaces.
