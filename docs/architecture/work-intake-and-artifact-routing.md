# Work intake and artifact routing

## 1. Purpose and boundary

`work-intake` is the neutral local front door for raw, ambiguous, acquisition,
refresh, and intake-safety requests. Status and explicitly named artifact or
work-type requests route directly to their owner. For durable classified input,
it writes the canonical artifact and dispatches only after that write is
durable. No route adds a `workspace.toml` entry; a work item's lifecycle is the
`Status:` and `Depends on:` headers of its own file. An eligible explicit direct-light request remains
session-local.

Tracker adapters acquire and normalize; they do not classify artifacts or write
repository state. `dispatch.py` reads each artifact's headers to say what is
ready, active, or blocked. `workspace-status` only repairs entries a
`workspace.toml` still holds (`repair-plan`, `repair-apply`); nothing registers
work.
Configured refresh processors compare tracker-origin artifacts and may apply
authorized local changes or separately confirmed coordination actions.

`work-loop` owns implementation and returns bounded completion evidence.
`close-work` owns the later inventory, whole-surface freshness audit, lifecycle
projection, disposition intent, initiative settlement, lifecycle records in
`docs/lifecycle/`, and any separately confirmed immediate effect. It is the only
writer of cooling state.

The same boundary owns a shared read-only semantic-surface resolver. Callers
supply bounded candidates; the resolver applies repository policy and
established adopter conventions without assuming catalogue paths, requiring a
configuration file, or fetching external locators.

Architecture and governance workflows consume that boundary by semantic role,
not by catalogue filename. Proposed or future design requests
`architecture-design`; the implemented system and accepted boundary changes
request `current-architecture`; ADRs or equivalent records are the
`decision-record` role. `new-adr` resolves `decision-record` inside the skill,
in the same precedence order and with its own bundled confinement check, and
does not call the shared resolver. Other roles and callers (`init-project`,
`generate-iac`, Architect) still consume the shared resolver. All roles remain independent of product truth, user
documentation, and product or release history. Architect and governance own the
artifact methods after resolution; work intake owns only the shared repository
destination result.

An upstream shaping workflow may offer one optional closed handoff inside
`normalized-intake.v1`. The object adds boundaries, non-goals, dependencies,
design context, and delivery questions. Existing content and source fields keep
the outcome, assumptions, evidence, locator, revision, and proposed authority.
Absence of the object is standalone Core and follows the existing routes.

### Where work enters, and at what altitude

A brand-new repository has its own entry, distinct from the routes above.
`init-project` runs a trigger gate that sends a script, a spike or a throwaway
straight past the flow — a single feature is excluded before the skill is
invoked at all, and goes to `new-spec` — then a value gate over fed-in
discovery, then records a foundation — an ADR plus a resolved `current-architecture`
destination, for which `docs/architecture/reference.md` is the fallback rather
than a fixed filename — and authors a **walking-skeleton** spec that hands the
build to `work-loop`. Greenfield does not get a different build loop; it gets
a different way in.

Above a spec, an intent carries a **`Level`** drawn from an open recognized
set — `product-vision` › `product-strategy` › `capability` › `feature`.
`Scale` is a separate axis, inferred at intake and running app ↔ business-unit.
[ADR-0033](../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md)
decoupled the two: `Scale` *suggests* a starting altitude and no longer stamps
one, so a product-level bet is authorable directly instead of being flattened
to a feature. `Scale` still shapes where decomposition bottoms out, but it
does not by itself pick the leaf artifact: one independently shippable feature
emits a delivery contract for `new-spec`, and only multi-spec or
cross-repository work emits a delivery brief. Business-unit scale is where a
value-stream meta-repo holds the cross-component artifacts a polyrepo has
nowhere else to put and rolls up delivery across the per-component slices.

## 2. Entrypoints

- `work-intake` selects direct-light, intent, brief, spec, defect,
  Draft-with-gaps, remember, status, or refresh behavior.
- `intake-intent` creates or admits the minimum repository intent.
- `author-delivery-brief create` turns raw multi-spec or cross-repository input
  into a Draft coordination brief; `continue` makes an existing brief Ready and
  confirms spec slices.
- `work-loop`'s `dispatch.py` lists the ready, active, and blocked specs from
  their `Status:` and `Depends on:` headers, and `--captured` lists the
  captured items. `navigate-intents` `outstanding` lists the work placed under
  an intent.
- `workspace-status` runs only `repair-plan` and `repair-apply`, which move the
  entries a `workspace.toml` still holds onto their own artifacts.
- `close-work` pauses resumable work, verifies delivery evidence and durable
  semantic owners, recommends one of RFC-0096's six dispositions, and owns
  separately authorized coordination or immediate-disposal effects.
- Jira, Jira Align, GitHub, and Linear intake adapters emit the same strict
  normalized contract and delegate the route.
- Profile refresh processors resolve by exact profile ID/version and return a
  closed comparison/effect result.
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
| Leftover entries | `workspace.toml`, which no intake route or workflow adds an entry to; `workspace-status repair-apply` drops each entry once its fact is on the artifact | `workspace-status` repair only | `workspace-status` repair, `dispatch.py` (refuses with `unmigrated_workspace` while an entry remains) |
| Tracker-origin authority | One closed `source-authority.v1` block in the canonical artifact; its optional `tracker_profile` table (`id`, `version`) is the one home of the tracker profile | Accepted intake/refresh workflow | Refresh and reconciliation |
| Refresh receipts | The artifact's authority block | Exact configured refresh processor | Later refresh |
| Direct-light decision record | Active session only | `work-loop` | Requester and current session |
| Completion evidence handoff | Active closeout invocation or stable evidence owner named by the delivery run | `work-loop` produces bounded references; no closeout authority | `close-work` and reviewers |
| Pause overlay | Existing resolved writable shaping or build coordination surface | `close-work`, after exact write authority | Resume path |
| Dependency-scoped completion receipt | Existing compatible coordination surface while a live dependency cites it | `close-work`, after exact write authority | Dependent work and closeout |
| Cooling lifecycle record | `docs/lifecycle/<delivery_id>.json` | `close-work` | Day-30 review and `dispatch.py` |
| Semantic-surface resolution result | Active invocation only | none; resolver is read-only | Requesting workflow and reviewer |
| Optional shaping handoff | Validated `normalized-intake.v1` envelope in the active invocation | Upstream producer owns offered content; Core owns validation and admission | `work-intake`, then the selected existing processor |

A repo-origin or tracker-origin intent, brief, or spec and a captured item
(defect, design, or research item) each live in their own file. Readiness comes
from each file's `Status:` header and its `Depends on:` targets, read by
`work-loop`'s `dispatch.py`. A tracker-origin artifact carries its tracker
profile in the `tracker_profile` table of its own `source-authority` record.
Refresh reads its role policy from the `[authorization.refresh]` table of
`.work-intake.toml` at the repository root.

A `workspace.toml` that still holds entries is repair input, not a requirements
store. `workspace-status` `repair-plan` and `repair-apply` move each entry onto
its artifact and drop it (the `needs-to-header`, `captured-to-file`,
`captured-entry-drop`, `refresh-policy-move`, `intent-brief-drop`,
`spec-entry-drop`, and `tracker-entry-drop` operations). The file stays in
place after the repair. Comments, summaries, order, labels, and hints cannot
select a route, satisfy a dependency, or authorize dispatch.

The captured-item file `docs/product/captured/<slug>.md` is the register for
captured work and for a spec's deferral anchors; `dispatch.py --captured` lists
those files. How a deferral marker resolves through it is the loop
contract's [§ 7](loop-contract.md#7-mechanical-invariants).

### Delivery-brief lifecycle

A brief's lifecycle is its `Status:` alone, repo-origin or tracker-origin. Child
specs constrain that state but never change automatically and are never
rewritten during brief closeout.

| State | Child-scope invariant | Transition owner |
| --- | --- | --- |
| `Draft` | No child is `Implementing` or `Shipped` | `author-delivery-brief create`, or `continue` after a material Ready-review invalidation |
| `Ready` | The Ready gate passed; no child is `Implementing` or `Shipped` | `author-delivery-brief continue` after revision-bound review and human confirmation |
| `Executing` | At least one child is `Implementing` or `Shipped` | The reviewed coordination update accompanying child execution |
| `Shipped` | The Spec map is non-empty and every materialized child is `Shipped` | `close-work`, after explicit human confirmation that the brief outcome is complete |
| `Withdrawn` | No child reached `Implementing` or `Shipped` | `close-work`, after explicit termination confirmation |
| `Cancelled` | At least one child reached `Implementing` or `Shipped` | `close-work`, after explicit termination confirmation |

All currently materialized children being `Shipped` does not prove that the
brief is complete; a later slice may not exist yet. Such an open brief remains
`Executing`. Terminal status and artifact retention are independent: cooling
or deletion policy never substitutes for `Shipped`, `Withdrawn`, or
`Cancelled`, and those states do not start a retention clock by themselves.

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
index prose. Refresh processors receive an existing tracker-origin artifact, the exact profile identity read from its record's `tracker_profile` table, lifecycle, authority, and revision pair.

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
   durable routes materialize the artifact and register nothing.
3. `dispatch.py` reads each spec's `Status:` header, sibling `plan.md`, and
   `Depends on:` targets and lists the ready and active specs. It refuses with
   `unmigrated_workspace` while a `workspace.toml` entry remains, and the
   finding points to `workspace-status` `repair-plan`. Only a ready or active
   spec may start or resume the work-loop, and several candidates are listed
   for the caller to choose from.
4. Every workspace-dispatchable, queued, or resumable build item resolves to an
   existing durable `spec.md` and sibling `plan.md`; execution receives those
   files rather than tracker payloads or index comments. An explicit
   direct-light request is session-local, creates no entry, and is
   ineligible for argless dispatch or fresh-session resumption.
5. Refresh resolves the exact configured processor, acquires and compares one
   source revision, presents field decisions, and applies guarded local changes
   only after authorization. Remote coordination remains separately confirmed.
6. A `workspace.toml` entry in a legacy form is rewritten by hand into the
   current form; `dispatch.py` refuses with `unmigrated_workspace` until then.
   `repair-plan` and `repair-apply` then move it onto its artifact.
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
    When a brief-backed child first reaches `Implementing`, or when a shipped
    child proves execution has occurred, the brief must be `Executing` in its `Status:`; reconciliation fails closed on a mismatch.
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
    An RFC or decision family may remain anchored after its work item leaves. A completion receipt keeps only delivery ID, outcome, completion
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
        direct-light                       artifact            refresh
        (session only)                         |                  |
                                               v                  v
                                        processor/work-loop   refresh processor
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

A repair `workspace.toml` entry in a legacy form stops at `unsupported_legacy`
or `unmigrated_workspace` before local artifact access or dispatch. An unsafe
local candidate, symlink escape, symlink loop, or mandatory-policy conflict
returns a stable refusal without raw exception text. Canonical artifacts and
unknown or private TOML extensions are never deleted or silently rewritten.

### Repair

`repair-plan` is read-only with respect to `workspace.toml`. `repair-apply`
requires explicit confirmation and re-verifies each operation against the
workspace before performing it. Re-verification is **per operation, not per
plan**: an entry whose spec status or eligibility moved since planning is
recorded unapplied with its reason — `spec_status_changed`,
`canonical_repair_ineligible` — while the rest of the plan proceeds.

Only a canonically eligible Type 2 queue finding whose artifact is `Shipped` or
`Archived` can become an automatic operation. Everything else stays manual:
Type 1 and Type 3 findings, active-source entries, and duplicates are emitted as
`manual_findings`, each carrying its finding type, initiative, list and
`finding_id`, for a human to act on rather than applied.

The same repair plan also carries the entry-drop operations (`needs-to-header`,
`needs-drop-cooled`, `captured-to-file`, `captured-entry-drop`,
`refresh-policy-move`, `intent-brief-drop`, `spec-entry-drop`,
`tracker-entry-drop`). Each moves a fact into the artifact's
own file or removes an entry that no longer needs one. The
`workspace-status` `references/mutate.md` file owns their exact shapes.

A `Shipped` repair moves the structured entry into `work.shipped`; an
`Archived` repair removes it. Neither mutates `work.active` — repair never
promotes or retires work that is still running.

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
Wave 6 has shipped ordinary-context exclusion: `dispatch.py` resolves the cooled
set once per run and never loads a cooled artifact body. Wave 7a-i closes cooling
scope. Wave 7a-ii projects the
completion receipt, Wave 7b classifies history, and Wave 7c prunes
proven-eligible artifacts.
Wave 7 owns historical migration and pruning behavior.

## 7. Observability and evidence

Canonical artifacts and `dispatch.py` provide the observable routing and
lifecycle record. Provenance records the source locator
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

All current writers emit only target entries, and no seed writes a
`workspace.toml`. The accepted legacy reader and `capture-work` forwarding alias
are removed in Core 3.0.0 under RFC-0083's release count, advance notice,
fixture/writer/guide/rollback evidence, and check-before-effect Approver
authorization. A former legacy shape surfaces as an `unsupported_legacy`
finding and is rewritten by hand.

## 8. Mechanical invariants and evaluation

- JSON Schemas own normalized intake, the legacy entry shape the repair reads,
  authority/refresh, and semantic-surface resolution shapes.
- Dispatch owns stable finding codes and never makes a legacy entry
  dispatchable by inference.
- The traceability lint recognizes a discovery-side producer node by a
  **bold-body** marker in the rendered document — `**Type:** screen-brief` for
  a screen, `**Action:**` and `**Service:**` for journey and blueprint entries
  extracted from a container, and `**Kind:**` and `**Level:**` for
  intent-ladder rungs, which it reads from the intent's preamble (above its
  first `## ` heading, comments hidden) the way the intent navigator does.
  YAML frontmatter is not the recognized form, so a file carrying
  `type: screen-flow` and no bold-body marker is not a producer to it. That is
  the trap worth knowing. Which directories it reads, when it uses a sidecar
  instead of walking the tree, and what an unrecognized shape costs are all
  the lint's to answer.
- The integrated routing matrix runs acquisition, normalization, routing,
  and authority/refresh across Jira, Jira Align,
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
- Feature delivery — which specs and briefs deliver a feature intent — has one
  canonical source:
  [`adapter-root-bins/intent_delivery_relations.py`](../../packs/core/.apm/adapter-root-bins/intent_delivery_relations.py).
  Byte-identical copies of that source and its private confinement helper
  `_file_safety.py` ship inside each consuming skill's own `scripts/` folder
  (`close-work`, `work-loop`, and `navigate-intents`); a parity test run at build
  and test time pins them to the source. Each consumer runs the copy beside its own script file,
  never from the analysed repository, so the copy carries the consumer's own
  trust boundary. The source's projection to `.agentbundle/bin/` is a maintainer
  diagnostic tool in this repository; the skill-local copies are what reaches
  every adopter install. The resolver reads only confined artifact preambles
  through the co-located `_file_safety.py`, so it runs without importing
  `agentbundle` and supports every install route. It returns one typed JSON
  snapshot whose top-level keys include `relations`, `classifications`,
  `provenance`, `diagnostics`, and an `artifacts` map from each identifier to its
  repository-relative file path; its module docstring and
  [construction tests](../../packs/core/tests/pack/test_intent_delivery_relations.py)
  own the relation vocabulary. A spec's `Discovery:` may name an intent by any
  of the four registered prefixes (`outcome:`, `opportunity:`, `capability:`,
  `intent:`) or by the legacy `docs/product/intents/<file>.md` path; the
  resolver matches the slug against the live intent index without checking the
  kind, and every relation and provenance record carries `intent:<slug>`. An unsafe or over-budget corpus yields an
  incomplete snapshot rather than partial data.
- `close-work` calls the resolver once per ancestor lookup and once per closure
  decision. `lint-traceability.py` calls it once per run when the repository has
  a delivery anchor. Both consumers validate every record in the snapshot before
  use and keep everything else: `close-work` owns status, freshness, and the
  closure verdict, and the lint owns the general product graph, contextual
  `Contract:` and `Discovery:` provenance, and its orphan, dangling, and cycle
  checks. A missing, failing, or incomplete resolver makes either consumer report
  `delivery-resolver-unavailable` instead of falling back to its own scan. The
  [integration suite](../../packs/core/tests/integration/test_intent_delivery_traceability.py)
  proves both consumers agree with the resolver.

These skill scripts run in the finish-time checklist and can run as fail-closed
CI gates where a PR event and Python exist. They do not fail closed inside an
arbitrary adopter repository.

- `lint-spec-status.py` checks `docs/specs/*/spec.md` metadata against the
  status contract in the `new-spec` skill's `references/spec-and-plan-contract.md`.
- `lint-traceability.py` flags structural orphans across the product chain; when
  a delivery anchor is present it invokes the canonical resolver for delivery edges.
- `lint-brief-coverage.py` rolls each brief's Spec map from `Brief:` back-links
  and requires a non-empty map of shipped specs for delivery.

Maintainer procedures live in
[Maintaining work intake and refresh](../guides/reference/work-intake-maintenance.md).

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
evaluation, and documentation surfaces. The feature-delivery resolver and its
two consumers were verified against Core `2.30.0`.

The header-derived routing state in §§ 1, 3, 5, and 7 (no intake route registers work, dispatch reads headers, and `workspace-status` only repairs)
was checked against commit `ef6fe19c5bfdea935612f7d8a6ead11db5718b0a`, Core `4.0.4`.
