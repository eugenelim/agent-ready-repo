# How to adapt a freshly-installed pack to your project

**Use this when:** You have just installed a pack and need to tailor its seed content (AGENTS.md, CHARTER.md, conventions) to your project's name, stack, and existing conventions.
**Prerequisites:** `core` pack installed and an `.adapt-install-marker.toml` present at the install scope root; see Prerequisites below.
**Result:** Foundational files tailored — project name, stack commands, charter, and any companion files merged for your install route.

A just-installed pack ships *seed* content — generic `AGENTS.md`, generic `docs/CHARTER.md`, generic governance shapes — that needs to be tailored to your actual project's name, stack, and existing conventions. The `adapt-to-project` skill (shipped in `core`) walks you through the tailoring with per-item approval. This page explains what the skill does, what answers it asks of you, and how greenfield and brownfield repos differ.

## Prerequisites

- The `core` pack installed in your target repo (or under user scope for user-scope packs).
- An `.adapt-install-marker.toml` at the install's scope root — written automatically by every supported install route. The next session-start hook surfaces a nudge to run the skill.

## Run the skill

In Claude Code or any agent harness that loads skills:

```
/adapt-to-project
```

The skill is the LLM-judgment layer on top of the deterministic `agentbundle adapt` CLI; the two work together — the CLI handles substitution and companion bookkeeping, the skill handles the non-mechanical decisions (which existing file matches which pack-canonical path, what to do with overlapping shapes, etc.).

Re-invoke any time. The skill dedupes against prior declines, surfaces only what's unresolved, and exits clean when nothing remains.

## Greenfield repo

A fresh repo has nothing to merge against, so adaptation is mostly **substitution** into the seed `AGENTS.md`, `docs/CHARTER.md`, and `docs/CONVENTIONS.md`. Have these answers ready before you start:

- Project name and a one-line description of what it does and for whom
- `install`, `test`, `lint`, `build`, and `run` commands for your stack
- A sentence or two on what's in and out of scope (for `docs/CHARTER.md`)

The skill walks each `<adapt:NAME>` marker one at a time; you approve, edit, or skip. Skipped markers come back the next time you invoke the skill.

## Brownfield repo

Your repo already has conventions, so the skill walks **four classes of change** with per-item approval — not just substitution:

1. **Substitution.** Same `<adapt:NAME>` markers as greenfield, but the values usually already exist in your `README`, `package.json`, or `Makefile`; the skill proposes pulling them in.
2. **Companion merges.** For each `*.upstream.<ext>` file the install left on disk, the skill proposes a merged result against your existing file. Per-file accept, edit, skip, or decline.
3. **Discovery + restructuring.** Non-canonical primitives elsewhere in your tree — a `DESIGN.md` at root, a stray `docs/architecture.md` — get matched against pack-canonical paths (`docs/CHARTER.md`, `docs/architecture/overview.md`). Per-finding accept, edit, or decline.
4. **Within-layout consolidation.** Overlapping shapes — your `docs/howto/` vs. the diátaxis pack's `docs/guides/how-to/` — get folded together per your call.

### Companion availability by install route

The skill's class-2 *Companion merges* walk depends on `*.upstream.<ext>` files being on disk. The three install routes differ in when those appear:

| Route | When companions appear |
| --- | --- |
| `agentbundle install` (CLI) | At install time — the CLI drops them on every Tier-2 collision. |
| `apm install` | Not at install. Run `agentbundle init-state` to record a baseline; the next `agentbundle upgrade` produces companions on Tier-2 collisions. |
| `/plugin install` (Claude Code) | Same as APM — `agentbundle init-state` first, then companions surface on `agentbundle upgrade`. |

The class-2 walk is a no-op if no companions are on disk; the other three classes (substitution, discovery, consolidation) run on every invocation regardless.

## Pitfalls

> **Skipped markers don't disappear.** The skill records skips against `.adapt-discovery.toml` so re-invocations don't pester you about the same one, but they're not declined — re-invoke explicitly with the skip cleared to revisit.

> **The skill does not write outside the install scope.** Repo-scope invocations confine writes to the repo root; user-scope invocations confine to the scope's user root. A misconfigured marker pointing outside scope is rejected, not silently followed.

## Related

- [`docs/specs/adapt-to-project/spec.md`](../../../specs/adapt-to-project/spec.md) — the authoritative spec (LLM skill + CLI split, marker formats, exit conditions).
- [How to upgrade an installed pack](../../_shared/how-to/upgrade-packs.md) — companion merges from upgrades flow through this skill too.
- [RFC-0001 § Adopter file safety contract](../../../rfc/0001-bundle-distribution-by-adapter-spec.md#adopter-file-safety-contract) — the guarantee the skill relies on (Tier-2 files survive install and upgrade).
