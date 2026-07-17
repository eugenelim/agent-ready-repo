# Authoring your organisation's event standard

The `event-contract` skill applies an **active standard** — a bundle of *data*
the method reads. The bundled default is Zalando-events
(`standards-manifest-zalando-events.yaml`). Your organisation can supply its own
standard **without forking this skill** by writing a small **base + delta**
bundle that `extends` the default. This is the same model Spectral popularised
(`extends: spectral:oas` + `rules: { …: false }`), and the same model the
sibling `api-contract` skill uses for REST.

> Everything here is **agent-read**. No program parses these files — the skill
> resolves base + delta by reading them, the way it reads any reference file.
> There is no runtime resolver.

## Two swappable axes

An event standard is not one thing. It spans two orthogonal axes, each swappable
data, and a delta can move them **independently**:

- **Axis A — the event-design ruleset.** Naming, categories, schema design,
  ordering/partitioning, metadata, compatibility/versioning. Bundled default:
  Zalando ch. 19-21, expressed for AsyncAPI output, anchored on `[#NNN]` tokens.
- **Axis B — the message envelope / schema format.** The reusable component the
  manifest's reserved `components.envelope` key names. Bundled default:
  CloudEvents 1.0.2. An org swaps it for AWS EventBridge-native, bare JSON
  Schema, or Avro by overriding that one key.

Axis A is moved with the `rules:` / `adds:` keys (disable or add design rules);
Axis B is moved with a single `components.envelope:` override. You can do either,
both, or neither.

## What a standard bundle is

A bundle lives under this skill's `references/`:

1. **A manifest** — `standards-manifest-<name>.yaml`. Identity, attribution,
   the base it `extends`, the rule files it provides, its quality-gate
   checklist, the reserved `components.envelope` key (Axis B), and the
   output/envelope defaults.
2. **Rule files** — phase-grouped markdown (naming, categories, schema_design,
   ordering_and_partitioning, metadata, compatibility). A delta usually adds
   none and just overrides a handful of inherited rules.
3. **A quality-gate checklist** — `standards-quality-gates-<name>.md`, the
   MUST / MUST-NOT items the method verifies before finalizing.
4. **An envelope component** — the YAML the `components.envelope` key resolves
   to (Axis B). Inherited from the base unless the delta overrides the key.

See `standards-manifest-zalando-events.yaml` for the canonical base.

## Manifest fields

| Field | Meaning |
| --- | --- |
| `name` | Short standard id (kebab/lower). |
| `version` | Version of *this bundle*. |
| `title` | Human title. |
| `extends` | The base standard's `name` (or `null` for a base). |
| `attribution` | `source`, `url`, `publisher`, `license`, `license-url`, `note`. **Required** when the standard derives from a licensed source. |
| `rule_files` | Map of phase → rule-file path. A delta lists only the files it *adds or replaces*; inherited files come from the base. |
| `quality_gates` | Path to the quality-gate checklist. |
| `example` | A complete validated example authored against the standard. |
| `components.envelope` | **Axis B** — the message envelope the method composes into `components.messages`. The one key an org overrides to swap CloudEvents for another envelope. |
| `output` | `format` (`asyncapi`) and `version` (e.g. `3.1.0`) — the emit target as data, so a spec bump is a one-line edit. |
| `envelope_defaults` | Envelope defaults the method reads, e.g. `content_type`. |
| `rules` | Rule-id → definition (in a base) **or** rule-id → `false` to disable an inherited rule (in a delta). Keys are canonical tokens, e.g. `"#210"`. |
| `adds` | List of house rules the standard adds: `{ id, phase, text }`. `phase` is one of the `rule_files` keys — `naming`, `categories`, `schema_design`, `ordering_and_partitioning`, `metadata`, `compatibility`. |

## Base + delta resolution

The method resolves the **effective standard** by reading, in this order:

1. Start from the base named by `extends` (its rules, rule files, quality
   gates, envelope, output target).
2. **Disable** any inherited rule whose id maps to `false` under the delta's
   `rules:` (Axis A).
3. **Add** every rule under the delta's `adds:` (Axis A).
4. **Override** a base rule file only where the delta provides a `rule_files:`
   entry for the same phase; otherwise the base's file applies (Axis A).
5. **Swap the envelope** only where the delta provides a `components.envelope:`
   entry; otherwise the base's envelope applies (Axis B).

The result is the effective standard the method applies for every phase.

## Worked example — a fictional organisation "acme"

Acme adopts Zalando-events but (a) relaxes the closed-schema rule `#210`
(`additionalProperties`) because its consumers tolerate unknown fields, (b)
requires every event type to be prefixed `acme.`, and (c) carries a tenant id as
the partition key. Acme keeps CloudEvents — **so it does not touch Axis B at
all.**

`standards-manifest-acme-events.yaml`:

```yaml
name: acme-events
version: "0.1.0"
title: Acme Event Standard
extends: zalando-events       # inherit the Zalando event ruleset (Axis A base)
# no components.envelope override → CloudEvents 1.0.2 inherited unchanged (Axis B)
attribution:
  source: Acme Event Guidelines
  publisher: Acme Corp
  license: proprietary
rules:
  "#210": false               # relax the avoid-additionalProperties rule
adds:
  - id: "ACME-E1"
    phase: naming
    text: "Event type names must be prefixed 'acme.' (org.domain.resource.verb)."
  - id: "ACME-E2"
    phase: metadata
    text: "Every event carries 'tenant_id' and uses it as the partition key."
```

**Resolved effective standard** (what the method actually applies):

- **All** of Zalando-events' ~24 rules, **except `#210`** (closed schemas) —
  Acme events may set `additionalProperties: true`.
- **Plus `ACME-E1`** — the `acme.` naming prefix, enforced in the naming phase.
- **Plus `ACME-E2`** — `tenant_id` partition key, enforced in the metadata phase.
- **The bundled CloudEvents 1.0.2 envelope, unchanged** — Acme touched no
  `components.envelope` key, so Axis B is inherited verbatim.
- All other inherited rule files, the inherited quality gates, and the inherited
  output target (AsyncAPI 3.1.0) are unchanged.

A reviewer can check this resolution by hand: it is exactly the base set, minus
the one disabled token, plus the two added rules, with the envelope inherited.

**Swapping the envelope instead (Axis B).** An AWS-native shop keeps the Zalando
design rules but replaces the envelope — the same file with a
`components.envelope:` override and no `rules:`/`adds:`:

```yaml
name: acme-aws-events
version: "0.1.0"
extends: zalando-events
components:
  envelope: references/eventbridge-native.yaml   # author this one file; swaps Axis B
```

When we say "the one `components.envelope` key", that means the **`envelope`
member of the `components:` map** — the nested two-level form shown above and in
the base manifest, *not* a top-level dotted `components.envelope:` key. Write it
in the shape the base uses, or the composing agent won't find your override.

The two axes move independently, and an org can do both at once.

## File-namespacing convention

Multiple standards coexist in this one `references/` directory by name:

```
references/
  standards-manifest-zalando-events.yaml         # bundled base (Axis A + B)
  standards-quality-gates-zalando-events.md
  cloudevents-1.0.2.yaml                          # bundled envelope (Axis B)
  standards-manifest-acme-events.yaml             # your delta
  standards-quality-gates-acme-events.md          # only if the delta changes the gates
  eventbridge-native.yaml                         # only if the delta swaps the envelope
```

A delta that only overrides a rule or two needs **just the manifest** — it
inherits the base's rule files, quality gates, and envelope.

## Delivering a custom standard

Standards are installed by **`adapt-to-project`'s Class 2 `.upstream`
companion-merge** — the overlay-and-reconcile mechanism the skill already
provides. There is **no new runtime resolver and no edit to `adapt-to-project`**:

- On install, when your standard differs from the bundled seed, a
  `*.upstream.<ext>` companion is dropped next to it; `adapt` proposes the merge
  and writes the result **in the same scope the companion was found**.
- **Scope follows the `contracts` pack's `allowed-scopes`:** a single
  organisation merges once at **user scope**; an organisation that pins its
  standard to one repository merges at **repo scope** and adapts per workspace.

No adopter action is needed unless you want a custom standard — Zalando-events +
CloudEvents are the defaults, and existing invocations keep working unchanged.
