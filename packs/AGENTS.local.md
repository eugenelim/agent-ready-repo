# AGENTS.local.md — `packs/`

Applies to `packs/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Self-hosting projection — insider notes

`packs/credential-brokers/.apm/user-libs/credbroker/` is byte-synced from
`packages/credbroker/credbroker/`; edit the `packages/` source, never the vendored copy.

| Target (do not edit) | Source |
| --- | --- |
| `docs/CONVENTIONS.md` | `core/seeds/docs/CONVENTIONS.md` |
| Adapter skill projections | `<pack>/.apm/skills/<name>/**` |
| Adapter agent, command, and hook projections | `<pack>/.apm/{agents,commands,hooks}/...` |
| Scaffold `packs/AGENTS.md` | `packs/AGENTS.md` |

The scaffold flow runs the other way and `make build-check` does not cover it.
After scaffold-source edits, run `python3 tools/catalogue/sync_authoring_scaffold.py --write`
and its check; the agentbundle suite owns the drift gate.
That sync writes `packages/agentbundle/agentbundle/_data/catalogue-scaffold/`, so
a scaffold-source edit needs an `Engine-Change-RFC:` trailer; CI enforces it with `tools/lint-catalogue-curation-guard.py`.
It is also an agentbundle engine change: bump matching `pyproject.toml` and
`agentbundle/version.py` versions. This release-correctness rule is not machine-enforced.
For a non-engine change, the trailer accepts `n/a — <reason>`; never invent an RFC number.

## Marketplace and release pipeline

1. Bump matching pack and plugin versions; see [Version bump rule](AGENTS.md#version-bump-rule).
2. Run `FORCE=1 make build-self` to regenerate `marketplace.json`.
3. Add the pack release entry to `docs/product/changelog.md`, free-standing at
   `##` — never nested under `[Unreleased]`, where it could never publish.
4. Decide the entry's `Highlights` disposition in the same step; do not leave it
   to a human to remember. Read the release diff and its verification evidence
   and answer one question: **does this change what a consumer of the pack can
   do?** If yes, draft the outcome-led bullets under a `### Highlights`
   subsection — those are what publish at `/now/`. If no, record that verdict
   and its reason in the PR's *What did you not change that you considered?*
   answer, so a reviewer sees a decision rather than an omission. Nothing
   downstream will make this call for you: the `/now/` projection is a pure
   parser over the file's bytes, and by contract no model runs in CI, release
   automation, or site generation. An unwritten `Highlights` block is a release
   the public page never mentions.

Design against projected adopter state, not this checkout's internal corpus. Forks
own their own publishing mechanism.

## Shipped pack content carries no internal-governance citations

Keep shipped material portable; see [the portable rule](AGENTS.md#shipped-pack-content-carries-no-internal-governance-citations).
Before committing, run:

```bash
grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bAC-?[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' packs/ --exclude='AGENTS*.md'
```

Rewrite internal citations rather than deleting their meaning. IETF RFC numbers never
start with `0`, unlike this catalogue's zero-padded identifiers.
Illustrative examples that teach a skill are permitted and must not be stripped: they
describe adopter artifacts. The same ordinal can be internal in one file and
illustrative in another; judge what it points at, never the number.

## Self-hosting projection

For source and projection ownership, follow [Self-hosting projection](AGENTS.md#self-hosting-projection).
