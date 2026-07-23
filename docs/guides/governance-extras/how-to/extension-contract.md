# How to define an extension contract

**Use this when:** A component you ship exposes an intentional hook — a plugin point, config extension, or lifecycle callback — that adopters are expected to plug into.
**Prerequisites:** A design doc, RFC, or ADR that describes why the extension hook exists.
**Result:** A documented extension contract naming the hook's shape, stable guarantees, out-of-contract boundaries, and verification method.

An extension contract is a documented agreement between a component and its
adopters: here is the hook you may use, here is the shape it must satisfy, and
here is what we promise to keep stable. It is a convention, not a skill — you
write it once in a design doc or ADR, reference it in code comments, and verify
it via the `architect-review` rubric.

## When you need one

An extension contract is warranted when a component ships an intentional
hook that third parties or adopters are expected to plug into:
- A plugin point (a registered handler, a middleware slot, a provider interface)
- A configuration extension (a YAML/TOML key that adds domain-specific entries)
- A standards extension (an adopter-supplied standard that overrides a pack
  default, as in the `iac-terraform` pack's governance-index `standards:` field)
- A lifecycle hook (a callback, a webhook, an event bus subscription)

It is *not* needed for internal implementation detail that callers do not
directly depend on.

## What an extension contract documents

| Field | What to write |
| --- | --- |
| **Extension point** | Name and location of the hook (file path, interface name, config key) |
| **Shape** | The schema or type signature the adopter's extension must satisfy |
| **Stable contract** | What the maintainer promises to keep backward-compatible |
| **Outside the contract** | What the adopter must *not* depend on (internal data, internal types) |
| **Validation** | How the maintainer verifies the contract (type check, lint, review rubric) |
| **Versioning** | When the contract version increments and what that means for adopters |

## Where to write it

- **In a design doc or RFC** — use the Proposal section's extension-contract
  check (see the `architect-review` Proposal rubric). This is the primary home.
- **In an ADR** — when the extension mechanism is itself an architectural
  decision.
- **In a README** or a dedicated `EXTENSION-CONTRACT.md` — for ongoing
  reference after the design doc is frozen.

## Example (governance-index standards extension)

The `iac-terraform` pack's governance-index accepts a `standards:` list per
domain:

```yaml
domains:
  tagging:
    standards: [docs/standards/tagging.md]  # ← adopter-supplied extension
```

The extension contract for this point:
- **Extension point:** `standards:` field in `docs/governance-index.yaml`
- **Shape:** a list of repo-relative paths to Markdown files
- **Stable:** the field name `standards:` and the YAML schema version
- **Outside the contract:** pack-internal reference paths; pack version
- **Validation:** the `generate-iac` Stage-0 gate reads the file and warns if
  the path does not exist

## The `architect-review` rubric check

When reviewing a design doc that introduces an extension contract, the
`architect-review` Proposal rubric includes:

> If the proposal introduces an extension contract, it names the contract
> explicitly, describes the extension point's shape, and states what is stable
> vs what the adopter must not depend on.

A design doc that adds a plugin point without documenting these three things
fails this check.

## Relationship to ADRs

An extension contract is often recorded in an ADR when the decision to expose
the hook is itself an architectural choice. The ADR records *why* the hook
exists and what alternatives were considered; the contract document (linked
from the ADR) records *what* the adopter must satisfy.
