# Compatibility & versioning

> Derived from the [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE), chapter 21. Restated for **AsyncAPI 3.1.0** output. Each rule keeps its shared `[#NNN]` token.

Events are persisted and replayed, so their schemas are **harder to evolve** than
REST responses. These rules keep evolution safe.

---

### [#209] MUST maintain backward compatibility for events

Event payload schemas follow the same compatibility discipline as REST APIs:

**Breaking changes (forbidden on a published event type):**
- Removing or renaming a required field.
- Changing a field's type or format.
- Tightening validation constraints (e.g. adding `required`, narrowing an enum
  consumers rely on).

**Compatible changes (allowed):**
- Adding new optional fields.
- Relaxing validation constraints.
- Adding new event types (a new `components.messages` member).

A breaking change is a new **major** schema version ([#246]) on a parallel type,
not an in-place mutation.

---

### [#245] MUST carefully define the compatibility mode

Every event type MUST declare its **compatibility mode** — the rules governing
how its schema may evolve. Record it on the message (e.g. an `x-compatibility`
extension or the `description`):

| Mode | Allowed changes |
|---|---|
| **Forward** | New fields can be added; consumers must tolerate unknown fields |
| **Backward** | Old consumers can read new events; no required-field removal |
| **Full** | Both forward- and backward-compatible |
| **None** | No guarantee (use sparingly) |

The declared mode tells consumers how defensively they must read, and tells
reviewers which schema changes to reject.

---

### [#246] MUST use semantic versioning of event type schemas

Event schemas MUST be versioned with **semantic versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** — breaking schema changes (avoid; [#209]). A new major is a parallel
  event type, not an in-place change.
- **MINOR** — new optional fields or compatible extensions.
- **PATCH** — documentation or description corrections.

Carry the schema version in the event metadata ([#247] — e.g. CloudEvents
`dataschema` or an `x-schema-version` attribute), distinct from the AsyncAPI
document's own `info.version`.
