# `figma` — guides

The Figma REST primitive. Point it at a file URL and read what's there: the document tree, specific nodes, file metadata, version history, and comments. Render any frame to PNG, SVG, JPG, or PDF. Turn a FigJam connector graph into a Mermaid flowchart. It reads design — it never modifies it, because the REST API can't.

The token never reaches the model. `figma` is a credentialed skill: it invokes a CLI that resolves your Personal Access Token in-process and makes the call itself.

New here? Read the [`figma` skill reference](reference/figma-skill.md) for the full surface, then [inspect a Figma file](how-to/inspect-a-figma-file.md) when you have a URL in hand.

## How-to

Task-oriented recipes for a problem you already have.

- [Inspect a Figma file](how-to/inspect-a-figma-file.md) — fetch a file, scope to nodes, read metadata and comments, render frames, and turn FigJam into Mermaid.

## Reference

Information-oriented, dry and complete.

- [The `figma` skill](reference/figma-skill.md) — every subcommand, its inputs and outputs, the exit-code bands, and the credential it needs.

---

The two-layer credential model — why the skill never holds your token — lives with the [`credential-brokers`](../credential-brokers/) pack: [Credentialed skills](../credential-brokers/explanation/credentialed-skills.md). Installing and upgrading the catalogue live in [`../_shared/`](../_shared/).
