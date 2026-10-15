---
title: "Write the docs"
summary: "Document a shipped feature as a page that matches your code, or find the gaps in a whole doc set."
pack: product-documentation
kind: how-to
status: stable
uses: [product-documentation]
---

# Write the docs

Name a feature that already ships and the reader it is for, and your agent drafts the page from your code.

## Write one page

Name the feature and the reader:

```text
Write a how-to guide for rotating an API token, for a developer who already installed our CLI.
```

The agent runs the `author-product-docs` skill, reads the code, and drafts the page. A real reader matters: "someone might want this" gives it nothing to aim at.

## Check the kind

The agent picks a tutorial, how-to, reference, or explanation from what the reader is doing, not from the topic. It reports the kind and where the page landed, so read that line and ask for a different kind if it is wrong. A reader who wants a guaranteed result on rails needs a tutorial. A reader with a named problem needs a how-to.

## Read the draft

The page opens with what the reader can do and a first command, request, or code sample they can run. Ask for what it left out:

```text
Which claims in this page could you not check against the code?
```

The agent lists any claim it marked unverified. Run the examples yourself before you publish.

## Revise or audit

For a page that already exists, ask for a revision:

```text
Revise this guide to lead with what the reader can accomplish.
```

The agent reads the page, then improves it in place. To see what is missing across the whole project, ask for an audit instead:

```text
Audit this project's docs and tell me which stages of the reader journey are missing.
```

The agent changes nothing and reports each stage as covered, partial, or missing. [Author product docs](author-product-docs.md) walks through the audit and the fixes that follow. For why the four kinds differ, read [About the Diátaxis framework](../explanation/the-diataxis-framework.md).

Next, [release the change](../../release-engineering/how-to/run-a-release.md).
