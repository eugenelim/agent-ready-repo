# Repository ownership

Defines which documentation owns which content, and how to find out in any repository. The most common documentation bug is writing user-facing docs into the maintainer tree, or the reverse.

This skill is portable. It reads the split from the repository and does not impose one.

## The audience split

| Kind of docs | Audience | Ships to users? | Owns |
|---|---|---|---|
| User-facing | People who install and use the product | Yes | README, installation guide, tutorials, how-tos, reference, explanations, troubleshooting, changelog, migration guides |
| Maintainer-facing | People who work on the product's source, CI, and releases | No | Contributor workflows, architecture and design records, release procedures, internal runbooks |

The contributing guide is the one bridge: it is linked from the user-facing README and is written for maintainers and new contributors.

## Discover the trees

Look in this order and stop when the answer is clear:

1. The agent-guidance documentation map, such as `AGENTS.md` or `CLAUDE.md`, if it says where each kind of doc lives.
2. `CONTRIBUTING`, the README's docs section, or other written conventions.
3. The docs-site configuration: what content directory the docs build reads.
4. The existing layout: where pages of the same kind and audience already sit.

If none of these settles it and the location would change the artifact, ask once.

## Decision rule

Would someone following the public install guide ever need this? If yes, it is user-facing. If it needs repository access and context, such as CI, release steps, or internal design, it is maintainer-facing.

## Machine facts and human description

A manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, a plugin or pack manifest) owns machine facts: name, version, scope, dependencies, supported runtimes. The README owns the human description: what the product does and how to start. When they diverge, the manifest wins for machine facts. Do not repeat a version or dependency in prose where it can go stale.

## Generated and rendered output

Generated or rendered output is never edited. That includes built sites, generated API reference, and projections copied from a source. An edit there does not change the source and the next build overwrites it. Find the source the docs build reads, edit that, and let the build regenerate the output.

## Destination order

Resolve where an artifact goes in the same order as Step 10 of the skill: the destination the user named, then the repository's documentation map, then the existing layout, then one question. Write to the structure the repository already uses. A repository that keeps all docs in `docs/` and API docs in `src/docs/` has a valid layout.
