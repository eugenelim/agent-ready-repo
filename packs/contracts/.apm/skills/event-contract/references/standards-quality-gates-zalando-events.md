# Zalando-events standard — quality-gate checklist

> The machine-checkable MUST / MUST-NOT items the `event-contract` method
> verifies before finalizing output when the active standard is
> **zalando-events**. Referenced from
> `standards-manifest-zalando-events.yaml` (`quality_gates`). Each item names the
> shared `[#NNN]` rule it enforces.

Before finalizing the output, verify every item. A single failure means the
contract is not ready.

### Structural validity

- [ ] Valid AsyncAPI YAML (parseable; passes `npx @asyncapi/cli validate`; no `$ref` errors)
- [ ] `asyncapi` version matches the manifest's output target
- [ ] `info.title`, `info.description`, `info.version` present
- [ ] `info.contact` (or per-message `x-owner`) names the owning team [#207]
- [ ] Every event type is a named `components.messages` member surfaced on a `channel` [#197]

### Naming & governance

- [ ] Event type names follow `org.domain.resource.verb`, lowercase, past-tense verb [#213]
- [ ] Event payload properties follow the API guidelines (snake_case, ISO formats) [#208]
- [ ] Every type is treated as a first-class contract — documented and reviewable [#194][#195]

### Categories

- [ ] Every event type declares a category — general, data-change, or business [#198]
- [ ] General events signal process steps/milestones [#201]
- [ ] Data change events signal mutations and carry `operation` + resource state [#202]
- [ ] Events represent useful business resources, not technical artifacts [#199]

### Schema design

- [ ] Payload schemas are valid AsyncAPI Schema Objects [#196]
- [ ] No PII / secrets / sensitive data inlined; reference ids used instead [#200]
- [ ] Data change event payloads mirror the corresponding REST resource [#205]
- [ ] Payload objects set `additionalProperties: false` (closed schemas) [#210]

### Ordering & partitioning

- [ ] General events provide an ordering mechanism (timestamp/sequence) [#203]
- [ ] Data change events carry an explicit monotonic `sequence_number` [#242]
- [ ] Data change events declare a hash partition key strategy [#204]
- [ ] Producer design supports idempotent, out-of-order consumption [#212]

### Metadata & resilience

- [ ] Every event carries a unique event id (envelope `id`) [#211]
- [ ] Mandatory metadata present via the active envelope's attributes [#247]
  (with the bundled CloudEvents envelope this is a **mapping**, not a field-by-field
  copy: `eid`→`id`, `event_type`→`type`, `occurred_at`→`time`, `version`→`dataschema`,
  `partition_key`→`partitionkey`; `received_at` is broker-supplied — see `metadata.md`.
  A by-number match on `#247` is not a field-set match)
- [ ] Event id is stable so consumers can deduplicate on it [#214]

### Compatibility & versioning

- [ ] No breaking changes to published event types (breaking = new major) [#209]
- [ ] Every type declares its compatibility mode [#245]
- [ ] Schemas are semantically versioned (MAJOR.MINOR.PATCH) [#246]

### Standard integrity (drift-by-number)

- [ ] **Every rule enforced above traces to its shared Zalando `[#NNN]` anchor**,
  so this checklist and the phase rule files are diffable by number against
  `api-contract`'s `references/events.md` (which expresses the same Zalando
  ch. 19-21 rules for events surfaced inside an OpenAPI contract). Any rule that
  has no `[#NNN]` token, or a `[#NNN]` present here but absent from `events.md`'s
  ch. 19-21 set (or vice versa), is **drift** — reconcile before shipping.
