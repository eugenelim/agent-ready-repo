# How to intake an external brief into a product brief

**Use this when:** You have unstructured external input (email, stakeholder message, Linear issue, or verbal sketch) describing multi-feature work and need to draft a DoR-compliant product brief.
**Prerequisites:** The `core` pack installed and any raw input to hand; no existing brief file at the target slug path.
**Result:** A draft brief file at `docs/product/briefs/<slug>.md` queued in `workspace.toml`, ready to decompose with `receive-brief`.

You have an email thread, a stakeholder message, a Linear issue, or a verbal sketch — unstructured input that describes multi-feature work. The `author-brief` skill turns that input into a DoR-compliant product brief file, elicits any missing gate fields in a short conversation, and queues the brief so `workspace-status` surfaces it immediately.

## Is `author-brief` the right entry point?

| Situation | Skill to invoke |
| --- | --- |
| You have unstructured external input (email, stakeholder message, Linear issue, verbal sketch) and need to draft a brief first | `author-brief` |
| You already have a formed multi-feature brief and need to decompose it into specs | `receive-brief` |
| You are authoring a single feature spec directly, without a brief | `new-spec` |

The tell for `author-brief` is **unstructured input that is not yet a brief** — the skill does the drafting. If the brief already exists as a well-formed file, go straight to `receive-brief`.

## Before you start

You need:

- The `core` pack installed in your target repo.
- Any unstructured input — a pasted email, issue body, message, or verbal description. It does not need to be complete or well-formatted.
- No existing brief file at `docs/product/briefs/<slug>.md` (the skill checks for a slug collision before writing).

## Steps

1. **Invoke the skill with whatever you have.** Paste the email, message, or issue text, or describe the work verbally. The skill accepts partial or messy input — it extracts what signal is there and asks for what is missing.

2. **The skill names what it found and what is missing.** It scans the input for DoR fields already present — Outcome, Appetite, Rabbit holes — and tells you which are present and which are absent. For example: "I found an Outcome but no Appetite and no Rabbit holes."

3. **Answer the elicitation for missing fields.**
   - **Outcome** is required. If the input contains no clear outcome, the skill asks for it before proceeding — it will not fabricate one.
   - **Appetite** gets a default if absent. Confirm or correct it.
   - **Rabbit holes** need ≥1 entry for the DoR gate. The skill asks you to name at least one design trap or out-of-bounds exploration before proceeding.

4. **Confirm the slug.** The skill proposes a kebab-case slug that becomes the filename (`docs/product/briefs/<slug>.md`). Confirm or correct it. If a file already exists at that path, the skill stops and prompts you before writing.

5. **Brief file created and queued in `workspace.toml`.** The skill writes `docs/product/briefs/<slug>.md` with `Status: Draft` and stages it. Then it handles the `workspace.toml` queue:
   - **Happy path:** the brief's path is appended to the active initiative's `brief_queue.draft` list.
   - **`workspace.toml` absent, unparseable, or has no active initiative with a `brief_queue`:** the file is created only. The skill emits a named diagnostic with the manual step to add the path yourself.
   - **Multiple active initiatives:** the skill asks which initiative's queue the brief joins. It does not guess.

6. **Brief is queued as draft.** The skill confirms the brief is at `docs/product/briefs/<slug>.md` and tells you to run `receive-brief` next to decompose it into specs.

## What `author-brief` does and does not do

`author-brief` stops at draft — it creates the file and elicits the DoR fields but does not decompose the brief into specs. Use `receive-brief` for that.

## Next step

When you are ready to decompose the brief into specs and mark it Ready, run `receive-brief` — see [Receive a product brief and decompose it into specs](receive-a-product-brief-and-decompose-it-into-specs.md).
