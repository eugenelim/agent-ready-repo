---
title: "How to author product docs"
summary: "Audit your project's documentation against the reader journey, then fix the worst gaps — or create, revise, or verify a single page."
pack: product-documentation
kind: how-to
status: stable
---

**Use this when:** you want to improve a project's docs and are not sure which pages are missing, stale, or wrong.
**Prerequisites:** `product-documentation` pack installed, and a repository with a library, CLI, API, app, service, framework, plugin, or agent-context pack in it.
**Result:** a journey gap report for your doc set, and the smallest set of page changes that closes the worst gaps.

Ask your agent:

> Audit this project's docs and tell me which stages of the reader journey are missing.

The `author-product-docs` skill reads your repository and replies with a report. It edits nothing during an audit unless you also ask for fixes.

## Steps

1. **Run the audit.** Send the request above. The skill infers audit mode from the words "audit" and "missing". It first finds what your product is — the code, manifests, and `--help` output reveal a library, CLI, API, app, service, framework, plugin, or agent-context pack — then reads the README, the docs index, and every page they link to.
2. **Read the journey gap report.** You get one row per reader stage, in order: discover and evaluate, install, first success, daily tasks, look up, understand, troubleshoot, upgrade, contribute. Each row is `covered`, `partial`, `missing`, or `not applicable`, with a file reference or the reason. The next actions are ranked by where readers are lost first, so a missing first success outranks a missing explanation.
3. **Read the page-level findings.** After the report, each finding names a file, a line, what was found, and the page contract it breaks.
4. **Retrofit the worst rows.** Ask "Retrofit the docs so the missing and partial rows are covered." The skill changes the smallest set of pages that moves the worst rows to `covered`, and links each page to the stage before and after it.
5. **Check the result.** Ask for a second audit, or run the checks in [Verify before you ship](#verify-before-you-ship).

## Other entry points

You do not need to name a mode. These requests start the other three modes: create, revise, and verify.

> Write a how-to guide explaining how to [your most common user task].

> Revise the README so a newcomer can run something in the first minute.

> Write release notes for v2.1.

> Verify this reference page still matches what the code does.

Create mode writes one page by default and reports the page kind and destination. Revise mode reads the existing page first and improves it in place.

## Prompts by journey stage

After the audit, ask for the page that fits the top-ranked row:

```
Write a quickstart for this project
```

```
Write release notes for the next version
```

```
Write a troubleshooting page for the most common install errors
```

Use the first for First success, the second for Upgrade, and the third for Troubleshoot.

## What the skill inspects

Before it states anything about your product, the skill reads the canonical sources for the surface it found:

- A library: the public API in source, its doc comments, and the examples.
- A CLI: the parser definitions and the help text they produce.
- An HTTP or RPC API: the contract file, then the route handlers.
- An app: the screens and flows in source, and the end-to-end tests.
- A service: the configuration schema, the environment variables the code reads, and the deploy files.
- A plugin: the manifest's commands, settings, and permissions.
- A framework or extension point: the interfaces users implement and the code that registers or loads them.
- An agent-context pack: the manifest and each skill's source.

A claim it cannot check against those sources is labeled unverified or cut.

## Where pages are written

The skill writes where your repository already keeps docs of that kind. It looks, in order, for a destination you name, the repository's own documentation map, and the existing layout of similar pages. If none of those settles it, it asks once. It keeps user-facing docs and maintainer docs apart: it does not put user docs in a maintainer-only tree, or publish maintainer runbooks as user guides.

## Verify before you ship

Verification follows the surface:

- A library: run its examples or doc tests.
- A CLI: compare the docs with `--help` and run each documented command.
- An HTTP or RPC API: compare with the contract file.
- A service: compare with the configuration schema and the code that reads it.
- An app: walk each documented task in the running app, or in its end-to-end tests.
- A plugin: compare with the contribution block in its manifest.
- A framework or extension point: compare each entry with its interface and the loader or registration code.
- An agent-context pack: read each skill's source, and send the first starter prompt.

Then check links. Run a route check after navigation changes. Review the rendered page after layout changes. The skill's report lists only the checks that ran.

## What remains your decision

- Whether the proposed page kind fits the reader you have in mind.
- Whether the artifact set is the smallest useful one.
- Whether the draft describes the product as users will meet it.

## Common mistakes

- **Expecting four pages.** Ask for one page and you get one. The audit decides which pages matter most.
- **Writing a standalone FAQ.** The skill folds each answer into the task or troubleshooting page where a reader would look.
- **Editing rendered output.** Edit the source files the docs build reads from. Generated pages are overwritten on the next build.

## See also

- [Getting started](../getting-started.md) — a first walk-through on your own repository.
- [How to write a guide](write-a-guide.md) — document one shipped feature.
- [About the Diátaxis framework](../explanation/the-diataxis-framework.md) — the four page kinds and how they sit inside the journey.
- [Product Documentation guides](../README.md) — install and starter prompts.
