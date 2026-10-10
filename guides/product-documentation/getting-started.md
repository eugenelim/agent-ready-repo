---
title: "Getting Started with Product Documentation"
summary: "Document your own repository with the author-product-docs skill: audit it, read the journey gap report, write the first missing page, and check it."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/getting-started
status: stable
---

In about 20 minutes you will find out which pages your project's docs are missing, write the most important one, and check it against your code.

With [`agentbundle`](../_shared/explanation/install-routes.md) installed, add the pack:

```bash
agentbundle install --pack product-documentation
```

Open your agent in the repository you want to document and send this request:

```
Audit this project's docs and tell me which stages of the reader journey are missing
```

You should see the agent start reading your repository. The audit changes no files.

## Prerequisites

- A repository with something users run or call: a library, CLI, HTTP API, app, service, framework, plugin, or agent-context pack.
- An agent that supports installed packs, such as Claude Code.
- `agentbundle`, the installer. See [install routes](../_shared/explanation/install-routes.md).

## Step 1: Let the skill find out what you ship

The `author-product-docs` skill starts by working out what your product is. It looks for evidence: a package manifest and public API for a library, command parsers for a CLI, an OpenAPI or protobuf file for an API, a configuration schema for a service. A repository can ship more than one surface, and the skill documents each one a reader touches.

It then looks for where your repository keeps user-facing docs and maintainer docs, using the agent-guidance file, the contributing guide, and the existing layout. It reads your README, your docs index, and every page they link to.

You should see the report name the surface it found. If the evidence fits none of the known surfaces, the skill says what it found and asks once.

## Step 2: Read the journey gap report

The reply starts with a table of nine rows, one per stage a reader passes through:

| Stage | Reader's question |
|---|---|
| Discover and evaluate | Is this for me? |
| Install | Can I get it running? |
| First success | Can I make it do one real thing quickly? |
| Daily tasks | How do I do this specific thing? |
| Look up | What exactly does this accept or return? |
| Understand | Why does it work this way? |
| Troubleshoot | It broke. What do I check? |
| Upgrade | What changed, and what must I change? |
| Contribute | How do I report or change something? |

Each row is `covered`, `partial`, `missing`, or `not applicable`, with the file that shows it or the reason. A library with no outside contributors may mark Contribute not applicable. Nothing marks First success not applicable.

The next actions are ranked by where readers are lost first. A missing or failing first success comes before a missing explanation. The top-ranked row marked `missing` or `partial` is the page to write first.

## Step 3: Write the first missing page

Ask the skill to write the page for the top-ranked row. For example, when First success ranks first:

```
Write a quickstart for this project
```

For example prompts for other stages, see [How to author product docs](how-to/author-product-docs.md#prompts-by-journey-stage).

The skill reads the canonical sources for your surface before it writes. It then drafts one page by default. You should see the page open with the goal and a first runnable action in its first 120 words, and the draft should say what the product reads and what it may change, show the expected result, and end with a link to the next stage. The skill writes the page where your repository already keeps docs of that kind, and asks once if it cannot tell where that is.

You decide whether the page matches what you want readers to do first.

## Step 4: Check the page against your code

Ask the skill to verify what it wrote:

```
Verify this page against what the code does
```

You should get three lists: verified claims, unverified claims, and claims that contradict current behavior. Then run the check that fits your surface. Run the examples for a library. For a CLI, compare the page with `--help` and run each command. For an API, compare it with the contract file. For a service, compare it with the configuration schema. For an app, walk each documented task in the running app or its end-to-end tests. For a plugin, compare the page with the contribution block in its manifest. For a framework, compare each extension-point entry with its interface and the code that loads it. For an agent-context pack, read each skill's source and send the first starter prompt.

Fix any contradiction before you publish. A claim nothing checked stays labeled unverified.

## Step 5: Audit again

Send the audit request from the top of this page again. The row you fixed should now read `covered`, with the new page as evidence. Work down the list one page at a time.

## What you have now

- A journey gap report for your project's docs.
- One new page, checked against the code, that links to the stage after it.
- A repeatable loop: audit, write the top gap, verify.

## Next steps

- [How to author product docs](how-to/author-product-docs.md) — retrofit several pages at once and use the other modes.
- [How to write a guide](how-to/write-a-guide.md) — document one shipped feature.
- [About the Diátaxis framework](explanation/the-diataxis-framework.md) — why each page has one job.
