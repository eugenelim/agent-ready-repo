# <Thing> reference

> Authoritative description of <thing>. For tasks, see the
> [how-to index](../how-to/). For why the design is shaped this way,
> see [<explanation title>](../explanation/<slug>.md).

<!--
If this page is auto-generated from <source>, replace this comment with:

> **Generated.** This file is generated from `<source>`. Do not edit by
> hand — edit the source and re-run `<generator command>`.
-->

## <Section 1 — pick the shape that fits the item kind>

Reference items come in many kinds. Pick *one* shape per kind and apply
it uniformly across every entry of that kind — predictability is
everything; readers scan. Three common shapes appear below as examples.
If your reference items are a different kind (data schemas, env vars,
event payloads, webhook bodies, etc.), design a shape that fits and
apply it uniformly — don't force-fit one of the three.

**Config option / parameter / flag — fixed metadata table:**

### `<option name>`

| | |
| --- | --- |
| Type | `<type>` |
| Default | `<default>` |
| Required | <yes / no> |
| Since | `<version>` |

<One-sentence neutral description. No recommendation. Just *what*.>

```<lang>
<minimal usage example>
```

**API endpoint / RPC — request / response shape:**

### `<METHOD> <path>`

<One-sentence neutral description.>

| Parameter | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `<name>` | path / query / body | `<type>` | <yes / no> | <description> |

**Response:** `<status>` — `<shape>`.

**CLI command / subcommand — usage + flags table:**

### `<command>`

```
<command> [flags] <args>
```

| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--<name>` | `<type>` | `<default>` | <description> |

## Errors

<!-- Delete this section if your reference items don't have associated
     error codes. -->

| Code | Meaning | When you see it |
| --- | --- | --- |
| `<CODE>` | <neutral description> | <trigger condition> |
| `<CODE>` | <neutral description> | <trigger condition> |

## See also

- [<how-to title>](../how-to/<slug>.md) — for tasks that use these.
- [<explanation title>](../explanation/<slug>.md) — for the design
  rationale.

<!--
Reminders from the skill — delete before committing:

- Neutral, austere, factual. No editorializing, no "we recommend".
- Every entry of the same kind has the same shape — readers scan.
- Complete. Omitted options are the most common reference failure.
- If auto-generated, mark it clearly at the top.
-->
