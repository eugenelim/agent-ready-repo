---
title: "How to write a guide"
summary: "Document a shipped feature in the right Diátaxis kind — tutorial, how-to, reference, or explanation — from the first page."
pack: product-documentation
kind: how-to
status: stable
---

**Use this when:** a feature already ships and you need to document it in
the right Diátaxis kind — tutorial, how-to, reference, or explanation — from
the first page.
**Prerequisites:** `product-documentation` pack installed, a real reader in
mind, and behavior that already ships.
**Result:** a guide at `guides/<pack>/<kind>/<slug>.md`, kind-checked against
the reader's posture, with task-first structure and sibling cross-links verified.

This guide is for someone documenting a feature that already ships and who
wants the page to land in the right Diátaxis kind the first time. It assumes
you've installed the `product-documentation` pack and your agent can run the
`author-product-docs` skill.

New to the four kinds? Read
[About the Diátaxis framework](../explanation/the-diataxis-framework.md) first.

## Before you start

You need:

- The `product-documentation` pack installed. Your agent then has access to
  the `author-product-docs` skill.
- A real reader in mind. "Someone might want to know X" isn't a reader.
  "An adopter who installed the credential-brokers pack and needs to rotate a
  token" is.
- Behavior that already ships. Guides document current product behavior.
  Documenting something you're proposing? You want an RFC or a spec, not a guide.

## Steps

1. **Invoke the skill.** Tell your agent what you're documenting: "Write a
   how-to guide for rotating a credentialed-skill token." The skill triggers
   on phrases like "write a guide for X", "create a tutorial for X", "new
   how-to", "new reference page", "new explanation".

2. **The skill proposes a documentation contract.** It names the mode (create),
   the audience, the artifact type, and the page kind — and asks you to confirm
   or redirect. This is the cheapest place to catch a mismatched kind.

3. **Pick the kind by reader posture, not by topic.** The skill maps posture to
   kind: on rails wanting a guaranteed result → tutorial; named problem wanting
   the recipe → how-to; scanning for an authoritative answer → reference; wanting
   to understand *why* → explanation.

4. **The skill inspects canonical behavior.** It reads `pack.toml`, skill
   sources, and any existing guides before drafting. It does not invent
   capabilities that are not in the source.

5. **Draft inside the kind's rules, applying link-out.** When you reach for
   material from an adjacent kind, write a link instead of the material.
   Tempted to explain *why* mid-tutorial? Link to an explanation.

6. **Cross-link real siblings only.** The skill adds a `See also` section. It
   links a sibling only when the file exists, and surfaces missing ones as
   follow-up TODOs rather than writing a broken link.

## Variations

- **The contract splits into two readers or two postures.** That's two guides,
  not one. Pick the first; the second goes to follow-up.
- **You're editing an existing guide.** Use revise mode: "Revise this guide to
  lead with what the reader can accomplish."
- **You need to connect several related pages.** Use retrofit mode: "Retrofit
  the onboarding guides so they connect into a first-value journey."

## Common pitfalls

- **Picking the kind by topic** — "authentication" is a topic, not a kind.
  *Learning* it, *configuring* it, and *understanding* it are three different pages.
- **Writing narrative voice in reference** — reference says *what*; recommendations
  live in explanation.
- **Creating four empty quadrant directories** — the kind is a page contract, not
  a required folder structure.

## See also

- [About the Diátaxis framework](../explanation/the-diataxis-framework.md) — the
  four kinds and the link-out discipline.
- [Author product docs](author-product-docs.md) — the full five-mode skill guide.
