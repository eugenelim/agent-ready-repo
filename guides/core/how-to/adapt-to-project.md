---
title: "How to adapt a freshly installed pack to your project"
summary: "Diagnose repository guidance or tailor installed seed content without losing project-specific conventions."
pack: core
kind: how-to
---

# How to adapt a freshly installed pack to your project

**Use this when:** You want a read-only diagnosis of the repository context agents can reach, or you have just installed `core` and need to tailor its seed content to the repository.
**Prerequisites:** The `core` pack installed. Post-install adaptation also uses an `.adapt-install-marker.toml` when one is present; repository diagnosis does not require it, and a local-scope install intentionally has none.
**Result:** A repository-context diagnosis first, followed only with your approval by a minimal root/scoped guidance proposal or post-install seed and companion changes.

The `adapt-to-project` skill first finds and respects the repository's existing
sources of authority wherever they live. It can then tailor newly installed seed
content with per-item approval. It links to repository-owned guidance instead of
moving or duplicating it merely to match the pack.

Ask your agent:

```text
Run adapt-to-project for a read-only readiness check. Do not change files until I approve adaptation.
```

At repository scope, a newly installed pack may ship *seed* content such as a
generic `AGENTS.md`, `docs/CHARTER.md`, or governance shape. Local scope ships
projected primitives without those seeds.

## Prerequisites

- The `core` pack installed in your target repo (or under user scope for user-scope packs). Fresh user-scope `core` installation is not supported.
- For post-install work, an `.adapt-install-marker.toml` may be present at the
  install scope root. It is not required for a read-only repository diagnosis.
- For a direct repository-scope install, that marker normally records unresolved
  adaptation work, and the installer chains the deterministic CLI adaptation
  step.
- A local-scope install deliberately writes no seeds, marker, layout section,
  or chained CLI adaptation result. Run the skill directly. Start a new agent
  session first if the newly installed skill is not yet available.
- For APM and plugin routes, a marker depends on the target runtime actually
  projecting and executing the package hook. Do not wait for a hook nudge when
  you can invoke the skill directly.

## Run the skill

In any agent harness that loads skills, use the prompt from the top of this page
— including its approval clause, which is what keeps the first pass read-only.

```
/adapt-to-project
```

For repository diagnosis, ask it to inspect the repository without changing
files. For post-install work, the skill is the judgment layer on top of the
deterministic `agentbundle adapt` CLI: the CLI handles substitution and companion
bookkeeping, while the skill presents readiness, inferred project conventions,
companion merges, and the non-mechanical decisions you approve. They are
separate surfaces; `agentbundle adapt` does not accept a `--scope` option.

Re-invoke any time. The skill dedupes against prior declines, surfaces only what's unresolved, and exits clean when nothing remains.

## Start with repository anchoring

The doctor reads effective root and scoped `AGENTS.md`, follows existing
architecture and contributor links, verifies real commands, and labels evidence
as explicit, framework-owned, convergent, tentative, contradictory, or absent.
Only documented rules and repository-owned primitives bind without confirmation.

Its minimum recommendation covers project overview, development workflow,
verified build/test commands, and coding conventions across the effective
guidance chain. It offers documentation, security, repository structure, or
scoped guidance only when the repository has evidence that makes the section
useful. A scoped `AGENTS.md` is appropriate for a stable subtree delta; root
guidance remains the home for repository-wide concerns.

The diagnosis is read-only. If you approve changes, the doctor merges links into
the existing root or scoped file without overwriting unrelated guidance. When no
equivalent source exists, it may offer the core pack's conventional location as
an optional starting point.

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
3. **Discovery + restructuring.** The skill surfaces genuine consolidation or
   restructuring opportunities while preserving adopter-owned guidance such as
   root `DESIGN.md`. It does not relocate files to match pack conventions.
   When it offers an implemented-system reference architecture, it requests the
   `current-architecture` semantic destination through Core and preserves a
   custom repository or external location. `docs/architecture/reference.md` is
   only the catalogue fallback; no destination is created silently.
4. **Within-layout consolidation.** Overlapping shapes — your `docs/howto/` vs. the diátaxis pack's `guides/how-to/` — get folded together per your call.

### Companion availability by install route

The skill's class-2 *Companion merges* walk depends on `*.upstream.<ext>` files being on disk. The three install routes differ in when those appear:

| Route | When companions appear |
| --- | --- |
| `agentbundle install` (CLI) | At install time — the CLI drops them on every Tier-2 collision. |
| `apm install` | Not at install. Run `agentbundle init-state` to record a baseline; the next `agentbundle upgrade` produces companions on Tier-2 collisions. |
| `/plugin install` (Claude Code) | Same as APM — `agentbundle init-state` first, then companions surface on `agentbundle upgrade`. Not a route for `core` itself, which is repo-scoped; this row covers user-scope packs you installed as plugins. |

The class-2 walk is a no-op if no companions are on disk. Repository anchoring
still runs without companions or install markers; post-install classes run only
when their state is present.

## Pitfalls

:::caution
**Skipped markers don't disappear.** The skill records skips against `.adapt-discovery.toml` so re-invocations don't pester you about the same one, but they're not declined — re-invoke explicitly with the skip cleared to revisit.
:::

:::caution
**The skill does not write outside the install scope.** Repo-scope invocations confine writes to the repo root; user-scope invocations confine to the scope's user root. A misconfigured marker pointing outside scope is rejected, not silently followed.
:::

## Related

- [How to upgrade an installed pack](../../_shared/how-to/upgrade-packs.md) — companion merges from upgrades flow through this skill too.
