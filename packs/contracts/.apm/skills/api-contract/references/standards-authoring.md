# Authoring your organisation's API standard

The `api-contract` skill applies an **active standard** — a bundle of *data*
the method reads. The bundled default is Zalando
(`standards-manifest-zalando.yaml`). Your organisation can supply its own
standard **without forking this skill** by writing a small **base + delta**
bundle that `extends` the default. This is the same model Spectral popularised
(`extends: spectral:oas` + `rules: { …: false }`).

> Everything here is **agent-read**. No program parses these files — the skill
> resolves base + delta by reading them, the way it reads any reference file.

## What a standard bundle is

A bundle is three things, all living under this skill's `references/`:

1. **A manifest** — `standards-manifest-<name>.yaml`. Identity, attribution,
   the base it `extends`, the rule files it provides, its quality-gate
   checklist, and any reusable schema components.
2. **Rule files** — phase-grouped markdown (naming, methods/status,
   representations, errors, security, compatibility, events). A delta usually
   adds none and just overrides a handful of inherited rules.
3. **A quality-gate checklist** — `standards-quality-gates-<name>.md`, the
   MUST / MUST-NOT items the method verifies before finalizing.

See `standards-manifest-zalando.yaml` for the canonical base.

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
| `components` | Reusable schema fragments (e.g. `money`, `problem`). |
| `rules` | Rule-id → definition (in a base) **or** rule-id → `false` to disable an inherited rule (in a delta). Keys are canonical tokens, e.g. `"#129"`. |
| `adds` | List of house rules the standard adds: `{ id, phase, text }`. |

## Base + delta resolution

The method resolves the **effective ruleset** by reading, in this order:

1. Start from the base named by `extends` (its rules, rule files, quality
   gates, components).
2. **Disable** any inherited rule whose id maps to `false` under the delta's
   `rules:`.
3. **Add** every rule under the delta's `adds:`.
4. **Override** a base rule file only where the delta provides a `rule_files:`
   entry for the same phase; otherwise the base's file applies.

The result is the effective ruleset the method applies for every phase.

## Worked example — a fictional organisation "acme"

Acme adopts Zalando but (a) serves path segments in `camelCase` rather than
Zalando's kebab-case (`#129`), and (b) requires mutual TLS on every endpoint as
a house rule.

`standards-manifest-acme.yaml`:

```yaml
name: acme
version: "0.1.0"
title: Acme API Standard
extends: zalando            # inherit the bundled Zalando base
attribution:
  source: Acme API Guidelines
  publisher: Acme Corp
  license: proprietary
rules:
  "#129": false             # disable Zalando's kebab-case path rule
adds:
  - id: "ACME-1"
    phase: security
    text: "Every endpoint must require mutual TLS (mTLS) in addition to OAuth2."
```

**Resolved effective ruleset** (what the method actually applies):

- **All** of Zalando's 138 applied rules, **except `#129`** (kebab-case paths) —
  Acme paths follow `camelCase` instead.
- **Plus `ACME-1`** — mTLS required on every endpoint, enforced in the Security
  phase alongside the inherited OAuth2 rules.
- All other inherited rules (naming except `#129`, methods/status,
  representations, errors, the rest of security, compatibility, events),
  inherited quality gates, and inherited components (Money, Problem) are
  unchanged.

A reviewer can check this resolution by hand: it is exactly the base set, minus
the one disabled token, plus the one added rule.

## File-namespacing convention

Multiple standards coexist in this one `references/` directory by name:

```
references/
  standards-manifest-zalando.yaml          # bundled base
  standards-quality-gates-zalando.md
  standards-manifest-acme.yaml             # your delta
  standards-quality-gates-acme.md          # only if the delta changes the gates
```

A delta that only overrides a rule or two needs **just the manifest** — it
inherits the base's rule files and quality gates.

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

No adopter action is needed unless you want a custom standard — Zalando is the
default base, and existing invocations keep working unchanged.
