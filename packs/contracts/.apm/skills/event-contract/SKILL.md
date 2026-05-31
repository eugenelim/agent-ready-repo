---
name: event-contract
description: Use when authoring an AsyncAPI event contract from requirements, user stories, or domain models. Applies a pluggable event-design standard (Zalando by default) as hard constraints and composes a swappable message envelope (CloudEvents by default) to produce a complete, validated AsyncAPI document for an event stream you produce or own. Activate for event-driven API design, event/message contract authoring, or AsyncAPI spec creation. Author only when the feature produces or owns the event type, not when it merely consumes one.
---

# Event Contract Generation

> **Standard-driven.** This skill carries the event-design *method*; the rules it
> enforces are *data* supplied by the **active standard**, across two swappable
> axes. The bundled defaults are the Zalando event ruleset
> (`references/standards-manifest-zalando-events.yaml`) and the CloudEvents
> message envelope. An organisation can plug in its own ruleset or envelope as a
> base+delta bundle without forking this skill — see
> [references/standards-authoring.md](references/standards-authoring.md).

## Your Role

You are an event contract author inside an SDLC pipeline, treating event types as first-class API contracts following the active standard's design rules.

**Inputs you receive:** user stories, domain models, plain-English requirements, an existing partial contract, the producing service's emitted events.

**Output you produce:** a single, complete, valid AsyncAPI YAML document — `channels`, `operations`, `components.messages`, `components.schemas` — with the active envelope composed into the messages, that downstream tooling (validators, code generators) can consume without modification.

## When NOT to author — produce vs. consume

Author an event contract **only when the feature produces or owns the event
type.** A feature that merely *consumes* an existing stream implements behaviour
against a contract the producer owns; it does not author one. Resolve to one of
three outcomes before you start:

| The feature… | Action |
| --- | --- |
| **Produces / owns** an event type (publishes a new event, or changes one it owns) | Author or modify the AsyncAPI contract in `contracts/asyncapi/` — the full method below. |
| **Consumes** an event whose contract already lives in `contracts/asyncapi/` | **No authoring.** Set the spec's `- **Contract:**` header to the existing producer contract (read-only reference) and point the plan's tests at it; add **no** back-pointer to it. |
| **Consumes** an event with no in-repo contract (external/upstream producer) | **No authoring, no fabricated contract.** Proceed spec→plan unchanged; optionally note the upstream event type the consumer depends on. |

Fabricating a contract for a stream the feature doesn't produce falsely claims
ownership and drifts from the producer's real one. If in doubt, you are a
consumer — ask who publishes the event.

## The active standard

Before authoring, resolve the **active standard** — the data this method applies.
The standard spans two axes (see `standards-authoring.md`): **Axis A**, the
event-design ruleset, and **Axis B**, the message envelope.

1. **Read the standard manifest.** The default is
   `references/standards-manifest-zalando-events.yaml`. If your organisation
   installed a custom standard (a bundle that `extends` the base, delivered via
   `adapt-to-project`'s `.upstream` companion-merge), read that instead.
2. **Load rule files per phase.** The manifest names the standard's phase rule
   files, its quality-gate checklist, the reserved `components.envelope`
   (Axis B), and the output target. Load each phase rule file as you reach it.
3. **Resolve base + delta by reading.** If the manifest `extends` a base, apply
   the base's rules first, then the delta: a rule the delta sets to `false` is
   disabled; rules under `adds` are additional house rules; an envelope override
   under `components.envelope` swaps Axis B. Nothing parses the manifest for you
   — you resolve it by reading.

Every MUST / MUST-NOT in the active standard is a non-negotiable rail. SHOULD
rules are followed unless you document the deviation inline with a rationale. The
rule numbers, the envelope, and the output version all come from the active
standard; this method does not hardcode them.

## Design Method

Follow these phases in order. Do not skip ahead. For each phase, load the active
standard's rule file for that category (named in the manifest) and apply its
rules.

### Phase 1 — Model the event domain

Extract the domain facts worth publishing: which state changes and business
milestones other services need to react to. Define event types around
**meaningful business resources**, not technical artifacts. Identify, per type,
who owns it and whether the feature produces it (if not, stop — see *produce vs.
consume*).

### Phase 2 — Name event types

Name each type per the active standard's naming rule (load the naming rule file).
The name is the contract's stable identity; it also flows into the envelope's
type attribute. Map each type to an AsyncAPI `channel` (the stream address) and a
named `components.messages` member.

### Phase 3 — Choose categories

Classify each type using the active standard's categories (load the categories
rule file). The category fixes the type's semantics, ordering expectations, and
payload shape — record it on the message.

### Phase 4 — Design the message envelope

Compose the envelope the manifest's `components.envelope` key names (Axis B —
CloudEvents by default) into each message. Pick the content mode per the target
broker:

- **Structured mode** — the envelope's context attributes are the message
  payload schema; the business payload nests under the envelope's data member.
  Compose by `allOf`-ing the envelope schema with a `data` property that
  `$ref`s the business payload schema.
- **Binary mode** — the envelope's context attributes ride as message headers
  (via the envelope's message trait); the business payload is the message
  payload directly.

Keep technical envelope fields out of the business payload. If an org swapped
Axis B, compose whatever envelope the manifest now names — the method is the
same; only the composed component differs.

### Phase 5 — Design payload schemas

Define each business payload under `components.schemas` per the active standard's
schema-design rule file: snake_case properties, ISO date/time and code formats,
reference identifiers instead of sensitive data, and closed schemas where the
standard requires. Where a data change event mirrors a REST resource, reuse that
resource's schema.

### Phase 6 — Ordering & partitioning

Apply the active standard's ordering and partitioning rules (load that rule
file): ordering fields per category, the partition key, and the producer-side
design for idempotent, out-of-order-tolerant consumers.

### Phase 7 — Compatibility & versioning

Apply the active standard's compatibility rules (load that rule file): declare
each type's compatibility mode, version schemas semantically, and treat a
breaking change as a new major on a parallel type — never an in-place mutation.

### Phase 8 — Quality gates

Before finalizing, verify every item in the active standard's quality-gate
checklist (named in the manifest). A single failure means the contract is not
ready. See *Quality Gates* below.

### Phase 9 — Emit the AsyncAPI document

Emit a single valid AsyncAPI document at the **version the manifest's output
target names** (do not hardcode it here). It uses `channels`, `operations`,
`components.messages`, and `components.schemas`, with the active envelope composed
into the messages.

**Traceability.** When you author a contract **against a real spec**, carry the
backward spec→contract pointer the seam mandates: a top-level
`x-spec: [docs/specs/<feature>/]` extension naming the spec(s) that define or
modify this contract (the spec's forward `- **Contract:**` header names this
file). A bundled teaching example carries **no** `x-spec` — it is authored
against no spec, so a back-pointer would dangle.

## Design discipline

Standard-independent practice — true whatever the active standard says. The
*specific* rules (naming, categories, ordering, envelope, versioning) belong to
the active standard; these are about the craft of event-contract-first design.

**Rationalizations to reject:**

| Rationalization | Reality |
| --- | --- |
| "It's just an internal event, no contract needed." | Internal consumers are still consumers; an unspecified event is a coupling waiting to break. Treat events as first-class contracts. |
| "We'll document the event after we ship the producer." | The contract *is* the documentation, and consumers integrate against it. Author it first. |
| "Consumers can just ignore fields they don't know." | Events are persisted and replayed; an open schema commits you to fields you never declared. Be deliberate about evolution. |
| "We'll add ordering/idempotency handling later." | Delivery is at-least-once and out-of-order from day one. Design the ordering field and dedup key up front. |
| "I'll author the contract for the stream we consume." | Consuming is not owning. Reference the producer's contract; don't fabricate one. |

**Red flags** (consistency properties — the active standard decides the specific rule):

- A message's envelope or metadata shape varies across event types without the active standard sanctioning it.
- Sensitive data or PII inlined in a payload.
- A data change event whose payload diverges from the REST resource it mirrors.
- An in-place breaking change to a published event type.
- Authoring before reading the active standard's rules, or authoring for a stream the feature only consumes.

## Quality Gates

Before finalizing the output, verify every item in the active standard's
quality-gate checklist (named in the manifest — for the bundled default,
[references/standards-quality-gates-zalando-events.md](references/standards-quality-gates-zalando-events.md)).
A single failure means the contract is not ready.

## Output Format

Produce a single AsyncAPI YAML document. The active standard governs the
specifics; in general it has these top-level keys:

- `asyncapi` — the version the manifest's output target names
- `info` — title, description, version, and the owning team's contact
- `channels` — one per event stream, with an `address` and a `messages` map
- `operations` — `send` / `receive` operations bound to the channels
- `components/messages` — each event type, with the active envelope composed in
- `components/schemas` — business payload schemas plus the envelope schema
- `x-spec` — present only when authored against a real spec (see Phase 9)

For the bundled defaults, see `references/golden-example.yaml` for a complete
validated example.

## Reference Files

The active standard's manifest names its rule files; load the one for the phase
you're in. For the bundled Zalando-events standard:

| Your contract involves…        | Load this reference                                |
| ------------------------------ | -------------------------------------------------- |
| Naming, ownership, governance  | naming.md                                          |
| General / data-change / business categories | categories.md                          |
| Payload schemas, PII, closed schemas | schema-design.md                             |
| Ordering, sequence numbers, partitioning | ordering-and-partitioning.md             |
| The metadata envelope, dedup, event ids | metadata.md                               |
| Schema evolution, compatibility modes | compatibility.md                            |
| Choosing or swapping the message envelope (Axis B) | the manifest's `components.envelope` key + standards-authoring.md |

Full reference index:

| Reference | Covers |
| --- | --- |
| [standards-manifest-zalando-events.yaml](references/standards-manifest-zalando-events.yaml) | The active standard (default): attribution, rule-file map, quality gates, the reserved envelope key, output target |
| [standards-authoring.md](references/standards-authoring.md) | How to plug in your organisation's own ruleset or envelope (base + delta, two axes) |
| [standards-quality-gates-zalando-events.md](references/standards-quality-gates-zalando-events.md) | The Zalando-events quality-gate checklist |
| [naming.md](references/naming.md) | Event type naming, ownership, registration, governance |
| [categories.md](references/categories.md) | General, data-change, and business event categories |
| [schema-design.md](references/schema-design.md) | Payload schemas, sensitive-data avoidance, closed schemas, REST-resource mirroring |
| [ordering-and-partitioning.md](references/ordering-and-partitioning.md) | Ordering fields, sequence numbers, hash partitioning, idempotency |
| [metadata.md](references/metadata.md) | Mandatory metadata, unique event ids, duplicate robustness |
| [compatibility.md](references/compatibility.md) | Backward compatibility, compatibility modes, semantic versioning |
| [golden-example.yaml](references/golden-example.yaml) | A complete validated example authored against the bundled defaults |

The bundled message envelope (Axis B) is named by the manifest's reserved
`components.envelope` key; load whatever file that key resolves to.

---

_The bundled Zalando-events standard is a derivative work; its attribution and licence (CC-BY-4.0) live in `references/standards-manifest-zalando-events.yaml`. The bundled message envelope carries its own source and licence in the file the manifest's `components.envelope` key names._
