# RFC-0018: Event/AsyncAPI authoring engine for the `contracts` pack

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-05-31
- **Date closed:** 2026-05-31
- **Related:** RFC-0017 D4 (deferred this exact event follow-on); ADR-0008 (contract-authoring seam); `spec-contract-seam` spec (the `x-spec` traceability + `asyncapi` row); `packs/contracts/` (`api-contract` is the method+data template); `new-spec` seam (`contract-types.md`)

## The ask

- **Recommendation (BLUF):** Ship `event-contract` — a second authoring skill in the `contracts` pack, built as a **standard-driven engine** in the same shape as `api-contract`: the skill carries the **event-design method**, the ruleset is swappable **data** with Zalando's event rules (ch. 19–21) as the bundled starter. It emits **AsyncAPI 3.1.0** documents into `contracts/asyncapi/`, with **CloudEvents 1.0.2** as the bundled message **envelope** (not a peer contract type). Wire it into the spec loop by filling the one stub row already waiting in `core`'s `new-spec` seam — no other `core` change.

- **Why now (SCQA):** *Situation* — RFC-0017/ADR-0008 shipped the contract seam and the `contracts/<type>/` tree; `api-contract` authors OpenAPI, and the seam routes *any* type by location convention. *Complication* — the `asyncapi` row in `core`'s seam table is a stub (`— (none bundled; direct-edit + note)`), so every event-driven spec degrades to hand-editing with a "no authoring skill" note, even though RFC-0017 D4 explicitly named a standalone event engine as the follow-on. *Question* — how do we add event authoring that matches `api-contract`'s pluggable-standard model, targets the current AsyncAPI + CloudEvents specs, and slots into the existing seam without re-touching `core`'s critical path?

- **Decisions requested:**
  1. **Build the event engine now** (vs. defer further / leave events direct-edit forever). Recommended: build now — it's RFC-0017 D4's named follow-on and the seam already waits for it. Decide-by: this RFC's acceptance. Default if no objection: build.
  2. **Name the skill `event-contract`** (vs. `asyncapi-contract`). Recommended: `event-contract` — parallels `api-contract`'s domain framing; the seam matches on the table's roster-name column, so the name is free to read well. Default: `event-contract`.
  3. **Target AsyncAPI 3.1.0** (latest), backward-compatible with 3.0. Recommended: 3.1.0 — empirically validated against CloudEvents (Evidence § spike). Default: 3.1.0.
  4. **CloudEvents 1.0.2 is the *bundled default* message envelope (not a peer type), and the envelope is *swappable standard data* — not hardcoded.** Recommended: bundle CloudEvents (CNCF-Graduated, the vendor-neutral envelope every hyperscaler adopts) as the default reusable component, but treat the envelope as a swap point so an org can plug in AWS EventBridge-native, bare JSON Schema, or Avro via the same base+delta delta. Support both structured and binary content modes. Default: CloudEvents bundled, envelope swappable.
  5. **Mirror `api-contract`'s method+data split, with two swappable standard axes for events.** The standard splits into (a) the **event-design ruleset** (naming/ordering/governance — Zalando default) and (b) the **envelope/schema format** (CloudEvents default, D4). Both are swappable data; the method (skill) is agnostic to both. Recommended: full parity, two axes — the across-organisations rationale that motivated pluggable REST standards applies to *both* event axes. Default: full parity, two axes.
  6. **Leave `api-contract`'s `events.md` untouched**; `event-contract` ships its own AsyncAPI-expressed event standard. Recommended: leave it — RFC-0017's non-goal already pins those rules inside the OpenAPI bundle; moving them would re-touch `api-contract` and couple two skills to one file. Default: leave. (Duplication tension → Open Q1.)
  7. **Fill the one seam row in `core`** (`asyncapi → contracts/asyncapi/ → event-contract`); the skill emits the `x-spec` extension the seam already mandates. Recommended: one-row edit, no other `core` change. Default: fill the row.
  8. **Author an event contract only when the feature *owns/produces* the event type — not when it merely *consumes* one.** Recommended: the `asyncapi` detection distinguishes producer/owner (→ author or modify the AsyncAPI contract) from consumer/subscriber (→ reference the producer's existing contract if one exists, else proceed with no contract). A spec that only stands up a Kafka subscriber/consumer over an existing stream does **not** trigger AsyncAPI authoring. Default: producer-only authoring.

## Problem & goals

**Diagnosis.** RFC-0017 built the contract seam to be contract-type-agnostic and shipped exactly one authoring skill (`api-contract`, OpenAPI/REST). It deferred a standalone event type (D4) with a precise rationale: *"CloudEvents is an envelope, not a peer type; AsyncAPI is the real event peer; neither is needed to prove the engine."* The deferral left a visible seam: `core`'s `contract-types.md` carries an `asyncapi` row whose authoring-skill column is empty, so the seam *places* a detected event contract at `contracts/asyncapi/` but cannot *author* it under rule-enforcement — it degrades to direct file-edit plus a runtime note. Event contracts are first-class API contracts (Zalando [#194]); leaving them perpetually hand-authored is the gap this RFC closes.

**Goals.**

- A team can author an AsyncAPI 3.1.0 event contract from requirements, under an enforced event-design standard, into `contracts/asyncapi/` — the same authoring rigour `api-contract` gives REST.
- The bundled default event standard is **swappable data** (base + delta), so an organisation can plug in its own event guidelines without forking the skill — identical to `api-contract`'s model.
- CloudEvents 1.0.2 is available as the bundled message envelope (structured and binary content modes), composed into AsyncAPI messages.
- `new-spec`'s event path stops degrading: the seam delegates to `event-contract` when it's on the roster, with the same graceful fallback when it isn't.
- `core` gains no new dependency and no critical-path change — only the one stub row is filled.

**Non-goals.**

- **A CloudEvents *contract type*** (a `contracts/cloudevents/` peer row) — CloudEvents is an envelope composed into AsyncAPI messages, not a peer to OpenAPI/AsyncAPI (RFC-0017 D4; reaffirmed here).
- **Re-homing Zalando's event rules out of `api-contract`** — those rules stay in the OpenAPI bundle for events that surface inside a REST contract (RFC-0017 non-goal). `event-contract` ships its own AsyncAPI-expressed standard.
- **Pre-authoring a bundle for every vendor standard** — the engine *handles* alternative standards on both axes through the same base+delta swap (an org plugs in its house event-design ruleset, or an AWS EventBridge-native / Avro envelope, via a delta). This RFC ships the *mechanism* plus the dominant bundled defaults (Zalando + CloudEvents); it does not pre-write the AWS / SBB / house-ruleset bundles — that's the org's delta, exactly as for REST. (This is a *non-goal*, not a *can't* — not handling the envelope as a swappable standard would defeat the engine's purpose.)
- **Bundling a validator** — AsyncAPI CLI / Spectral validate the emitted document in CI; the skill's quality gates guide authoring, they don't replace tooling.
- **A contract for consumer-only features** — a spec that only subscribes to / consumes an existing event stream owns no contract (D8). The seam references the producer's existing contract if one exists and otherwise authors nothing; it never fabricates a `contracts/asyncapi/` file for a stream the feature doesn't produce.
- **Codegen / mock / SDK generation** from the AsyncAPI document — downstream tooling, out of scope (as in RFC-0017).
- **Protocol bindings beyond what the envelope needs** — Kafka/AMQP/MQTT binding catalogues are not in v1; the method notes where they plug in.

## Proposal

### D1 — A second skill in `contracts`, not a merge or a new pack

`event-contract` lands in `packs/contracts/.apm/skills/event-contract/`, alongside `api-contract`. The pack description already says "OpenAPI 3.1 (api-contract) and more to come"; this is the "more." It inherits the pack's install posture unchanged (user-scope default, repo-scope allowed, `allowed-adapters = [claude-code, kiro, codex]`). `core` imports nothing from it — the integration is the seam (D7), exactly as ADR-0008 prescribes.

### D2 — Method+data architecture, mirroring `api-contract`

The skill splits the same way `api-contract` does:

- **Method (in `SKILL.md`):** the event-design phase procedure — model the event domain → name event types → choose categories → design the message envelope → design payload schemas → ordering/partitioning → compatibility/versioning → quality gates → emit AsyncAPI 3.1.0. Standard-agnostic.
- **Standard (swappable data), two axes:**
  - **Axis A — the event-design ruleset:** a **manifest** (`standards-manifest-zalando-events.yaml`) — `name`, `version`, attribution/license, an optional `extends` base, plus `rules` (to disable inherited rules) / `adds` — naming **phase-grouped rule files** (event naming, categories, schema design, ordering, metadata, compatibility), the Zalando ch. 19–21 rules expressed for AsyncAPI output, and a **machine-checkable quality-gate checklist**.
  - **Axis B — the envelope/schema format:** a **reusable envelope component** the manifest names, defaulting to the bundled CloudEvents 1.0.2 schema (D4). An org swaps it for AWS EventBridge-native, bare JSON Schema, or Avro by overriding this one manifest key in its delta — the method composes whatever envelope the manifest points at into the AsyncAPI messages.

Zalando + CloudEvents ship as the bundled defaults; an org authors a delta on either axis exactly as for REST standards. Delivery reuses `adapt-to-project`'s Class 2 `.upstream` companion-merge — no new mechanism (RFC-0017 D3).

### D3 — Output: AsyncAPI 3.1.0 into `contracts/asyncapi/`

The skill emits a single valid AsyncAPI **3.1.0** document. 3.1.0 is the latest release and is backward-compatible with 3.0 (it adds a binding, no breaking changes). The document uses AsyncAPI 3's `channels` / `operations` / `components.messages` / `components.schemas` structure. Backward spec→contract traceability is the `x-spec` vendor extension the `spec-contract-seam` spec already mandates for AsyncAPI.

### D4 — CloudEvents 1.0.2 as the bundled default envelope (swappable, not hardcoded)

The envelope is **Axis B of the standard bundle (D2)** — swappable data, not baked into the method. **CloudEvents 1.0.2 is the bundled default**, chosen on adoption merit: it is **CNCF-Graduated** (since 2024-01-25, the foundation's top maturity tier) and is the vendor-neutral envelope adopted across the field — Azure Event Grid, Google Cloud Eventarc, AWS EventBridge, Adobe I/O, Alibaba, IBM, the European Commission. An org whose events use a different envelope overrides the manifest's envelope key in its delta:

- **AWS EventBridge-native** (`source` / `detail-type` / `detail` / `time` / `region`) — for AWS-centric estates that haven't adopted CloudEvents (EventBridge can also carry CloudEvents in `detail` or transform between the two).
- **Bare JSON Schema or Avro** — for orgs with no envelope convention beyond the payload schema.

The skill composes whatever envelope the manifest names into the AsyncAPI messages. With the default, composition follows AsyncAPI's own published guidance (the cited blog's examples are AsyncAPI 2.x-era; the spike re-confirmed the same composition holds under the 3.1.0 `components.messages` structure):

- **Structured mode** — the CloudEvents attributes (`specversion`, `id`, `source`, `type`, `time`, `data`, …) are modelled as the message **payload** schema; the business payload nests under `data`.
- **Binary mode** — CloudEvents attributes ride as message **headers** (via an AsyncAPI message trait); the business payload is the message payload.

The default content type is `application/cloudevents+json`. The two modes are a CloudEvents-bindings concept (HTTP/Kafka); the skill picks per the target broker and keeps technical envelope fields out of the business payload.

### D5 — Two swappable axes; bundled defaults chosen on adoption

The event "standard" is not one thing — it spans two orthogonal axes, each swappable data (D2):

- **Axis A — event-design ruleset** (naming, categories, ordering, governance, versioning). Bundled default: **Zalando** (ch. 19–21, ~24 numbered rules), chosen after checking alternatives (Evidence § external prior art): **Google's AIP has no dedicated event-design proposal** — AIP governs REST resource design (naming, pagination, errors), not events; **AWS publishes no event-design *ruleset*** (its EventBridge schema registry is schema *tooling* — OpenAPI3 / JSONSchema — not design rules); **SBB**'s event principles are selective and carry no clear license. Zalando is the only published, comprehensive, numbered, CC-BY-4.0 event-design ruleset, and it keeps `event-contract` in the same standard family as `api-contract`.
- **Axis B — envelope/schema format** (D4). Bundled default: **CloudEvents 1.0.2**, the CNCF-Graduated vendor-neutral envelope adopted across the field.

Both defaults travel with their attribution/license in the manifest, as for the REST bundle, and both are overridden by an org's delta — we ship the *mechanism* plus the *dominant defaults*, not a pre-authored bundle for every vendor.

**Composing the axes — the common case (org rules *on top of* CloudEvents).** The axes are independent keys in one delta manifest, resolved by the same base+delta reading `api-contract` already documents (`references/standards-authoring.md`). To keep CloudEvents and layer house rules on top, the org `extends` the Zalando event base, leaves the envelope key untouched (CloudEvents is inherited), and lists its rules under `adds:`:

```yaml
# standards-manifest-acme-events.yaml  (the org's delta — Axis A only)
name: acme-events
version: "0.1.0"
extends: zalando-events     # inherit the Zalando event ruleset (Axis A base)
# no components.envelope override → CloudEvents 1.0.2 inherited unchanged (Axis B)
rules:
  "#210": false             # optionally relax one inherited rule
adds:
  - { id: "ACME-E1", phase: naming,   text: "Event types must be prefixed 'acme.'." }
  - { id: "ACME-E2", phase: metadata, text: "Every event carries 'tenant_id' as the partition key." }
```

Resolved effective standard = all Zalando event rules (minus `#210`) **+** `ACME-E1/E2` **+** the bundled CloudEvents envelope, unchanged. Swapping the *envelope* instead is the same file with a `components.envelope:` override (e.g. an AWS-native or Avro schema) and no `adds:` — the two axes move independently, and an org can do both at once. Delivery is `adapt-to-project`'s Class 2 companion-merge at the `contracts` pack's scope; no skill fork, no new runtime resolver.

### D6 — `api-contract`'s `events.md` stays put

`api-contract`'s `events.md` covers events that surface *within* a REST/OpenAPI contract (events-as-OpenAPI-Schema-Objects, webhooks/callbacks) — a different output surface from a standalone AsyncAPI document. RFC-0017's non-goal already keeps those rules in the OpenAPI bundle. `event-contract` ships its own rule files; the shared *design principles* (no-PII, naming, ordering, compatibility) are restated in AsyncAPI terms. The minor restatement is accepted in exchange for not coupling two skills to one file (Open Q1 records the tension).

### D7 — Seam wiring: one row in `core`

`core`'s `new-spec/references/contract-types.md` gets its `asyncapi` row's skill column filled:

```
| asyncapi (events) | contracts/asyncapi/ | event-contract |
```

That is the entire `core` change. The seam already routes by location convention and looks up the authoring skill by roster name; filling the row upgrades the event path from "direct-edit + note" to "delegate to `event-contract`" when the `contracts` pack is installed, and leaves the graceful-degradation fallback intact when it isn't (ADR-0008's two-layer discovery).

### D8 — Detection fires on *producing/owning* an event type, not *consuming* one

The seam's step 4b already authors a contract only when a feature **exposes** an interface surface. For events this distinction is acute and must be made explicit, because many event-driven specs are pure **consumers**: a spec that stands up a Kafka subscriber/consumer (or any reader of an existing stream) implements behaviour against an event contract it does **not** own — the producer owns it. Consuming is not exposing.

So the `asyncapi` detection resolves to one of three outcomes:

| The feature… | Seam action |
| --- | --- |
| **Produces / owns** an event type (publishes a new event, or changes one it owns) | Author or modify the AsyncAPI contract in `contracts/asyncapi/` via `event-contract` (the full D1–D7 path). |
| **Consumes** an event whose contract already lives in `contracts/asyncapi/` | **No authoring.** Set the spec's `- **Contract:**` header to the existing producer contract (read-only reference) and point the plan's tests at it; do not add an `x-spec` back-pointer (this spec doesn't define it). |
| **Consumes** an event with no in-repo contract (external/upstream producer) | **No authoring, no fabricated contract.** Proceed spec→plan unchanged; optionally note the upstream event type the consumer depends on. |

This keeps the engine from manufacturing a contract a consumer-only feature has no authority over — a fabricated `contracts/asyncapi/` file would falsely claim ownership and would drift from the producer's real one. The rule is a detection refinement the implementation spec encodes; it needs no new `core` mechanism (it sharpens the existing "exposes a surface" test, it doesn't replace it).

### Migration path

No existing state to convert — there is no `contracts/asyncapi/` content in the repo today. The change is purely additive: a new skill directory in `contracts`, the manifest/rule-file/component bundle, and the one seam row. Self-hosting projection (`make build-self`) projects the new skill into `.claude/skills/` like any other `contracts` skill.

## Options considered

**Axis A — should the engine exist at all (do-nothing baseline).** MECE along *act-now / act-later / never*.

| Option | Trade-off | |
| --- | --- | --- |
| **Build now** | Closes the stub row RFC-0017 D4 named; one more skill to maintain. | ★ recommended |
| Defer to a later milestone | No new maintenance now; every event spec keeps degrading to direct-edit. | |
| Never (events stay direct-edit) | Zero skill cost; abandons rule-enforcement for a first-class contract type ([#194]). | |

**Axis B — how CloudEvents relates to AsyncAPI.** MECE along *peer-type / envelope / absent*, grounded in AsyncAPI's published guidance and RFC-0017 D4.

| Option | Trade-off | |
| --- | --- | --- |
| CloudEvents as a `contracts/cloudevents/` peer type | A row per spec flavour; but CloudEvents has no channels/operations — it isn't a peer to AsyncAPI/OpenAPI. Rejected by RFC-0017 D4. | |
| **CloudEvents as the message envelope inside AsyncAPI** | Matches AsyncAPI's own integration guidance and CloudEvents' self-description ("envelope for the message"). | ★ recommended |
| No CloudEvents support | Simpler; but the user requirement and the dominant cloud-native envelope go unmet. | |

**Axis C — how much of `api-contract`'s architecture to mirror.** MECE along *full parity / partial / minimal*.

| Option | Trade-off | |
| --- | --- | --- |
| **Full parity (method + swappable standard bundle)** | Consistent with `api-contract`; pluggable per org; more files to author up front. | ★ recommended |
| Partial (method skill, CloudEvents baked-in, no pluggable standard) | Fewer files; but an org can't swap its event guidelines — the very gap RFC-0017 fixed for REST. | |
| Minimal (templates only, no standard model) | Cheapest; no enforcement, inconsistent with the pack's existing skill. | |

**Axis D — bundled default for the event-design ruleset (Axis A of D5).** MECE along *reuse-an-in-repo-standard / adopt-a-new-external-standard / write-our-own*.

| Option | Trade-off | |
| --- | --- | --- |
| **Zalando event rules (ch. 19–21)** | Published, numbered, CC-BY-4.0, already in-repo, same family as the REST bundle. | ★ recommended |
| Google AIP / AWS / SBB / Confluent | Google AIP has no event-design proposal; AWS publishes schema *tooling*, not a ruleset; SBB isn't numbered and lacks a license; Confluent is a course. Researched and rejected as the *default* (any can still be plugged in as a delta). | |
| Author an original event standard | Full control; reinvents a published standard and loses citable provenance. | |

**Axis E — how the envelope/schema format is bound (Axis B of D5).** MECE along *hardcoded / default-but-swappable / no-default*. This is the axis the first cut got wrong.

| Option | Trade-off | |
| --- | --- | --- |
| Hardcode CloudEvents into the method | Simplest; but an AWS-native or Avro shop can't use the engine — defeats the standard-driven purpose. | |
| **CloudEvents default, envelope swappable via the manifest** | One manifest key selects the envelope; CloudEvents (CNCF-Graduated, tri-cloud) ships as default; AWS-native / JSON Schema / Avro plug in by delta. | ★ recommended |
| No bundled envelope (always BYO) | Maximally neutral; but every adopter must author an envelope before first use, even the CloudEvents majority. | |

## Risks & what would make this wrong

- **Pre-mortem — duplication drift.** If the Zalando event principles restated in `event-contract` drift from `api-contract`'s `events.md`, the two skills give conflicting guidance. *Mitigation:* the rule *numbers* ([#NNN]) are the shared anchor; both cite the same Zalando source, so a reviewer can diff by number. Recorded as Open Q1.
- **Pre-mortem — CloudEvents/AsyncAPI compose worse than expected** for some broker binding (e.g. binary-mode header mapping on a protocol the skill doesn't model). *Mitigation:* v1 scopes structured + binary JSON; protocol-binding catalogues are an explicit non-goal with a documented plug-in point.
- **Pre-mortem — spec churn.** AsyncAPI 3.x or CloudEvents 1.x revs and the bundled templates lag. *Mitigation:* the version is named in the manifest (data), not hardcoded in the method, so a bump is a data edit — the same property that makes the standard swappable.
- **Key assumptions (falsifiable):**
  - *AsyncAPI 3.1.0 can express a CloudEvents 1.0.2 envelope in a single valid document.* — **Validated** (Evidence § spike); if false, the whole output format is wrong.
  - *Zalando is the best available bundled default for event rules.* — falsifiable by a better-licensed, comprehensive, numbered event ruleset surfacing.
  - *The seam needs no structural change.* — falsifiable if event detection requires logic the type-agnostic table can't express; the `spec-contract-seam` spec already routes `asyncapi`, so this is low-risk.
- **Drawbacks:** one more skill and standard bundle to maintain; "contracts" now spans REST + events, raising the pack's surface; minor rule-text restatement across two skills (Open Q1).

## Evidence & prior art

- **Spike / de-risk result.** Riskiest assumption: AsyncAPI 3.1.0 + CloudEvents 1.0.2 compose into one valid document. I authored a minimal AsyncAPI **3.1.0** document with a CloudEvents 1.0.2 **structured-mode** envelope (business payload under `data`) and validated it with the official AsyncAPI CLI (`npx @asyncapi/cli@6.0.0 validate`): result — *"File … is valid! … don't have governance issues."* This both confirms the output format and settles D3 (3.1.0, no CloudEvents conflict). Spike artifact: `.context/spike/order-events.yaml` (gitignored workspace dir; carries the validator command + version as a header comment).
- **Repo precedent.**
  - RFC-0017 D4 — deferred a standalone event/AsyncAPI type "to a named follow-on"; this RFC is that follow-on. Its non-goal pins Zalando's event rules inside the OpenAPI bundle (→ D6).
  - ADR-0008 — "other contract types (AsyncAPI, proto, …) plug in as new `contracts/<type>/` rows + roster entries without re-touching `core`"; the two-layer discovery that gives the seam its graceful fallback.
  - `spec-contract-seam` spec — specifies `x-spec` backward traceability for OpenAPI **and AsyncAPI**, and routes the `asyncapi` type today.
  - `packs/contracts/.apm/skills/api-contract/` — the method+data template (`standards-manifest-zalando.yaml` + phase rule files + quality gates + `golden-example.yaml` + reusable components) this RFC mirrors.
- **External prior art** (every link fetched or returned by search; the spike result is the load-bearing evidence):
  - [AsyncAPI 3.0.0 release notes](https://www.asyncapi.com/blog/release-notes-3.0.0) and [3.1.0 release notes](https://www.asyncapi.com/blog/release-notes-3.1.0) — 3.0 is the major (reusable channels, traits, request/reply); 3.1.0 is latest and non-breaking.
  - [CloudEvents v1.0.2](https://github.com/cloudevents/spec) — latest stable envelope (Feb 2022); structured vs. binary content modes are defined in its protocol bindings.
  - [CNCF: CloudEvents graduation (fetched)](https://www.cncf.io/announcements/2024/01/25/cloud-native-computing-foundation-announces-the-graduation-of-cloudevents/) — confirms **Graduated 2024-01-25**, "over 340 contributors … from 122 different organizations," and names Azure Event Grid, Google Cloud Eventarc, Adobe I/O, Alibaba, IBM, the European Commission as adopters — the basis for CloudEvents being the bundled default envelope (D4/Axis E).
  - [AWS: sending/receiving CloudEvents with EventBridge (fetched)](https://aws.amazon.com/blogs/compute/sending-and-receiving-cloudevents-with-amazon-eventbridge/) — "EventBridge uses its own event envelope … requires that you define top-level fields, such as `detail-type` and `source`," *and* supports publishing/consuming CloudEvents and transforming between them. Establishes AWS EventBridge-native as the main swappable alternative envelope (D4).
  - [Eventarc: CloudEvents format (Google Cloud docs)](https://cloud.google.com/eventarc/docs/cloudevents) — Eventarc "delivers events … in a CloudEvents format in binary content mode," i.e. Google's envelope *is* CloudEvents. [Google AIP index](https://google.aip.dev/general) shows AIP covers REST resource design with no dedicated event-design proposal — the basis for rejecting Google AIP as an Axis-A default (D5).
  - [AsyncAPI ⨯ CloudEvents (official blog, fetched)](https://www.asyncapi.com/blog/asyncapi-cloud-events) — documents two composition approaches (full JSON-Schema field mapping; `schemaFormat: application/cloudevents+json`) and the framing "AsyncAPI focuses on the application and how it is connected; CloudEvents focuses on the message."
  - [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) — ch. 19–21 event rules; the bundled default standard (CC-BY-4.0).
  - [SBB API Principles — event-driven (fetched)](https://schweizerischebundesbahnen.github.io/api-principles/eventdriven/principles/) — checked as an alternative; selective principles, not a numbered ruleset, no clear license → rejected as the bundled default.

## Open questions

1. **Keeping the two intentionally-separate rule copies from drifting.** D6 decides *not* to re-home the rules (the two skills keep separate, format-specific copies); the residual question is the *maintenance* mechanism that catches the two copies diverging over time. Recommended default: **anchor both copies on the shared [#NNN] rule numbers and add a diff-by-number check to the `event-contract-engine` spec's quality gates** (no cross-skill file dependency); escalate to a shared file only if drift is observed in practice. Owner: eugenelim. Decide-by: the `event-contract-engine` spec's review gate.

## Follow-on artifacts

<!-- Filled in when the RFC is accepted. -->

- ADR-NNNN: record the event-engine architecture decision (CloudEvents-as-envelope; standard family) if it warrants a standalone record beyond ADR-0008.
- Spec: `docs/specs/event-contract-engine/` — the implementation contract for the skill, the Zalando-events standard bundle, the CloudEvents component, the one-row seam edit, and the producer-vs-consumer detection rule (D8).
- No `docs/CONVENTIONS.md` change (the `contracts/<type>/` convention and the seam already exist).

## Errata

> Approver-signed corrections recorded during implementation
> (`docs/specs/event-contract-engine/`). The body above is frozen at acceptance;
> these clauses supersede it where they conflict. — Approved: eugenelim, 2026-05-31.

1. **Migration-path correction — `event-contract` is *not* self-host-projected.**
   The *Migration path* section above states "Self-hosting projection
   (`make build-self`) projects the new skill into `.claude/skills/` like any
   other `contracts` skill." This is **wrong**: `contracts` is a user-scope-default
   pack and is **excluded from `SELF_HOST_PACKS`**, so `make build-self` does
   **not** project `event-contract` (or `api-contract`) into this repo's
   `.claude/skills/`. The only part of this change that projects is the **`core`
   seam edit** (`contract-types.md`). Adopters who install the `contracts` pack
   still receive `event-contract` through their own install route; the
   non-projection is specific to this repo's self-hosting.

2. **D7 "that is the entire `core` change" reads as *two parts*.** D7 says
   filling the `asyncapi` row is "the entire `core` change." Per the confirmed
   decision, the `core` edit is **two parts in one file**: (a) fill the
   `asyncapi` row's skill column with `event-contract`, **and** (b) add the D8
   producer-vs-consumer detection note to the same `contract-types.md`. Part (b)
   is detection prose only — it adds **no new `core` mechanism** — so D7's
   "no other `core` change" still holds in substance; the row-fill is simply not
   the *only* line that changes in that file.
