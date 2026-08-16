---
title: Intake external source material into a product brief
summary: Route a coherent multi-feature outcome into a Draft brief and workspace entry.
pack: core
kind: how-to
---

# How to intake external source material into a product brief

**Use this when:** Intake has identified a coherent multi-feature outcome that needs a Draft brief.
**Prerequisites:** The `core` pack installed and normalized source content to hand; no existing brief file at the target slug path.
**Result:** A Draft brief at `docs/product/briefs/<slug>.md` with a matching non-dispatchable `workspace.toml` entry.

Start with `work-intake` when you have an email, issue, or conversation rather
than a confirmed artifact route. It normalizes the bounded facts and invokes
`author-brief` only when the content forms one coherent multi-feature outcome.

## Is `author-brief` the right entry point?

| Situation | Skill to invoke |
| --- | --- |
| You have source material but have not chosen an artifact route | `work-intake` |
| Intake has classified a coherent multi-feature outcome | `author-brief` |
| You already have a formed multi-feature brief and need to decompose it into specs | `receive-brief` |
| You are authoring a single feature spec directly, without a brief | `new-spec` |

The tell for `author-brief` is **unstructured input that is not yet a brief** — the skill does the drafting. If the brief already exists as a well-formed file, go straight to `receive-brief`.

## Before you start

You need:

- The `core` pack installed in your target repo.
- Any unstructured input — a pasted email, issue body, message, or verbal description. It does not need to be complete or well-formatted.
- No existing brief file at `docs/product/briefs/<slug>.md` (the skill checks for a slug collision before writing).

## Steps

1. **Invoke `work-intake` with what you have.** It treats the source as untrusted data, retains a safe locator and revision, and passes bounded normalized content to `author-brief` when a brief is the clear route.

2. **The skill names what it found and what is missing.** It scans the input for DoR fields already present — Outcome, Appetite, Rabbit holes — and tells you which are present and which are absent. For example: "I found an Outcome but no Appetite and no Rabbit holes."

3. **Answer the elicitation for missing fields.**
   - **Outcome** is required. If the input contains no clear outcome, the skill asks for it before proceeding — it will not fabricate one.
   - **Appetite** gets a default if absent. Confirm or correct it.
   - **Rabbit holes** need ≥1 entry for the DoR gate. The skill asks you to name at least one design trap or out-of-bounds exploration before proceeding.

4. **Confirm the slug.** The skill proposes a kebab-case slug that becomes the filename (`docs/product/briefs/<slug>.md`). Confirm or correct it. If a file already exists at that path, the skill stops and prompts you before writing.

5. **Brief file created and registered in `workspace.toml`.** The skill writes `docs/product/briefs/<slug>.md` with `Status: Draft`, then registers the structured Draft entry. If registration fails, it rolls back the file when safe or leaves an explicit non-dispatchable reconciliation finding. It never silently degrades to file-only success.

6. **Brief is queued as draft.** The skill confirms the brief is at `docs/product/briefs/<slug>.md` and tells you to run `receive-brief` next to decompose it into specs.

## What `author-brief` does and does not do

`author-brief` stops at draft — it creates the file and elicits the DoR fields but does not decompose the brief into specs. Use `receive-brief` for that.

## Next step

When the brief has enough outcome, scope, constraints, assumptions, risks, and provenance to pass your human Ready gate, run `receive-brief`. Ready may contain zero specs; create a spec only after you confirm a slice. See [Receive a product brief and decompose it into specs](receive-a-product-brief-and-decompose-it-into-specs.md).
