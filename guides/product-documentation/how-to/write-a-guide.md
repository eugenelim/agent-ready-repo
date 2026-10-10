---
title: "How to write a guide"
summary: "Document one shipped feature as a tutorial, how-to, reference, or explanation, written for a single reader and checked against the product."
pack: product-documentation
kind: how-to
status: stable
---

**Use this when:** a feature already ships and you need one page that documents it.
**Prerequisites:** `product-documentation` pack installed.
**Result:** one page of the right kind, in the place your repository keeps docs of that kind, with a first runnable action in its first 120 words and links to the pages before and after it.

Ask your agent:

> Write a how-to guide for rotating an API token, for a developer who already installed our CLI.

Swap in your own feature and reader. The `author-product-docs` skill reads the code first, then drafts.

## Before you start

You need:

- **A real reader.** "Someone might want to know X" is not a reader. "A developer who installed the CLI and needs to rotate a token" is.
- **Behavior that already ships.** Guides document the current product. A proposal belongs in a spec or an RFC.

## Steps

1. **Send the request.** Name the feature and, if you know it, the kind: "write a how-to", "write a quickstart", "document the `export` command". The skill infers create mode.
2. **Let it find the surface.** From the repository it works out whether the feature belongs to a library, CLI, API, app, service, framework, plugin, or agent-context pack, and which source is canonical for it — the parser definitions for a CLI command, the contract file for an endpoint.
3. **Check the kind.** The skill picks the kind from the reader's posture, not the topic. On rails and wanting a guaranteed result is a tutorial. A named problem is a how-to. Scanning for a fact is reference. Wanting to know why is explanation. Check the page kind and destination it reports, and redirect it if either is wrong.
4. **Read the draft against the contract.** The page opens with the reader's goal and a first runnable action: a request, a command, or a code sample. It says what the product reads and what it may change, shows the expected result, names what remains the reader's decision, and ends with the likely next step.
5. **Check where it landed.** The skill writes where your repository already keeps docs of that kind and audience. If it could not tell, it asked once. The report lists the files it changed and the sources it read.
6. **Check the links.** Each link points to a file that exists. A missing sibling shows as a TODO comment instead of a broken link.

## Variations

- **Two readers or two postures.** That is two pages. Pick the first and note the second as a follow-up.
- **The page already exists.** Say "revise this guide to lead with what the reader can accomplish". The skill reads the page first and treats the request as a revision.
- **Several pages need to connect.** Ask for a retrofit, or start with an audit. See [How to author product docs](author-product-docs.md).

## Common pitfalls

- **Picking the kind by topic.** "Authentication" is a topic. Learning it, configuring it, and understanding it are different pages.
- **Writing opinion into reference.** Reference says what. Recommendations belong in an explanation.
- **Creating empty category directories.** A page kind is a contract, not a folder.
- **Pasting commands that were never run.** The skill labels a claim it could not check as unverified. Run the example yourself before you publish it.

## See also

- [About the Diátaxis framework](../explanation/the-diataxis-framework.md) — the four kinds and the link-out discipline.
- [How to author product docs](author-product-docs.md) — audit a doc set and fix the biggest gaps.
- [Getting started](../getting-started.md) — a first walk-through on your own repository.
