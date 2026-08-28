---
title: Intake external source material into a product brief
summary: Route a coherent multi-feature outcome into a Draft brief and workspace entry.
pack: core
kind: how-to
---

# Intake external source material into a product brief

**Use this when:** Intake has identified a coherent multi-feature outcome that needs a Draft brief.
**Prerequisites:** The `core` pack installed and normalized source content to hand; no existing brief file at the target slug path.
**Result:** A Draft brief at `docs/product/briefs/<slug>.md` with a matching non-dispatchable `workspace.toml` entry.

Start with `work-intake` when you have an email, issue, or conversation rather
than a confirmed artifact route. It normalizes the bounded facts and invokes
`author-delivery-brief create` only when the content forms one coherent multi-feature outcome.

For a confirmed upstream delivery brief, use:

```text
Intake this confirmed delivery brief and preserve its handoff provenance.
```

Core admits the bounded fields through `work-intake`. An existing brief
continues through `author-delivery-brief continue`; otherwise create mode authors the Draft.
An external locator is recorded as opaque provenance. Core does not fetch,
search, probe, or read it.

## Is `author-delivery-brief create` the right entry point?

| Situation | Skill to invoke |
| --- | --- |
| You have source material but have not chosen an artifact route | `work-intake` |
| Intake has classified a coherent multi-feature outcome | `author-delivery-brief create` |
| You already have a repository brief and need to review or slice it | `author-delivery-brief continue` |
| You are authoring a single feature spec directly, without a brief | `new-spec` |

The tell for create mode is **bounded input that is not yet a repository brief**. If the brief already exists in the repository, use continue mode.

## Before you start

You need:

- The `core` pack installed in your target repo.
- Any unstructured input — a pasted email, issue body, message, or verbal description. It does not need to be complete or well-formatted.
- No existing brief file at `docs/product/briefs/<slug>.md` (the skill checks for a slug collision before writing).

## Steps

1. **Invoke `work-intake` with raw or ambiguous input.** It treats the source as untrusted data, retains minimized provenance, and passes bounded normalized content to `author-delivery-brief create` when a brief is the clear route. If you already know the artifact route, invoke create mode directly.

2. **The skill names what it found and what is missing.** It scans the input for
   the outcome, constraints or appetite, assumptions or risks, and safe source
   provenance, then reports what is present and what a later Ready review must
   resolve.

3. **Answer the elicitation for missing fields.**
   - An identifiable multi-slice outcome lets the Draft proceed. If it is
     missing, the skill records that blocking gap rather than inventing one.
   - Constraints, appetite, assumptions, and risks improve readiness but do not
     block Draft creation.
   - Safe source provenance is required; raw source payloads are not copied.

4. **Confirm the slug.** The skill proposes a kebab-case slug that becomes the filename (`docs/product/briefs/<slug>.md`). Confirm or correct it. If a file already exists at that path, the skill stops and prompts you before writing.

5. **Brief file created and registered in `workspace.toml`.** The skill writes `docs/product/briefs/<slug>.md` with `Status: Draft`, then registers the structured Draft entry. If registration fails, it rolls back the file when safe or leaves an explicit non-dispatchable reconciliation finding. It never silently degrades to file-only success.

6. **Brief is queued as draft.** The skill confirms the brief is at `docs/product/briefs/<slug>.md` and tells you to run `author-delivery-brief continue` next for readiness and optional slice selection.

## What create mode does and does not do

`author-delivery-brief create` stops at Draft — it creates the file and names Ready gaps but does not decompose the brief into specs. Use continue mode for that.

## Next step

When the brief has enough outcome, scope, constraints, assumptions, risks, and provenance to pass your human Ready gate, run `author-delivery-brief continue`. Ready may contain zero specs; create a spec only after a separate slice confirmation. See [Continue a delivery brief and confirm delivery slices](receive-a-product-brief-and-decompose-it-into-specs.md).
