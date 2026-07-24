# How to upgrade an installed pack

**Use this when:** You want to move an installed pack to a newer version — whether a whole pack, a single primitive, or resolving companion files left by a previous upgrade.
**Prerequisites:** A pack already installed from the catalogue and the `agentbundle` CLI on your PATH; see [Prerequisites](#prerequisites).
**Result:** The pack upgraded to the newer version with any local edits preserved as `.upstream.<ext>` companion files for selective merging.

Move an installed pack to a newer version, with the conflict handling you expect when your local edits and the upstream pack have both moved on.

## Prerequisites

- A pack already installed from this catalogue via one of the three routes (Claude Code plugin marketplace, APM, or the `agentbundle` CLI).
- For the catalogue-native flow: the `agentbundle` CLI on your PATH.
- For catalogue-level safety on APM and Claude-plugin installs: a one-time `agentbundle init-state` run after the original install — see [RFC-0001 § Adopter file safety contract](../../../rfc/0001-bundle-distribution-by-adapter-spec.md#adopter-file-safety-contract).

## Pick the right granularity

Three granularities are available, in order of increasing specificity.

### Whole pack (default)

Pick the verb that matches how you originally installed.

- **APM:** `apm update <pack>`.
- **Claude Code plugins:** `/plugin update <pack>@<catalogue>`.
- **`agentbundle` CLI (single pack):**

  ```bash
  agentbundle upgrade --pack <name> <catalogue>
  ```

- **`agentbundle` CLI (all packs at a scope — bulk mode):**

  ```bash
  agentbundle upgrade --all --scope repo
  agentbundle upgrade --all --scope user
  ```

  `--all` upgrades every `(pack, adapter)` row at the specified scope. It is mutually exclusive with `--pack`.

  For machine-readable output (CI pipelines, PR annotation), add `--format json`. The JSON document is the sole content on stdout; all progress, warnings, and diagnostics go to stderr. In JSON mode you must also pass `--yes` (the interactive confirmation prompt is suppressed):

  ```bash
  agentbundle upgrade --all --scope repo --format json --yes
  ```

  See [Flow B in use-an-artifactory-catalogue.md](use-an-artifactory-catalogue.md#flow-b--repo-scope-ci-upgrade) for the full CI sequence including a GitHub Actions YAML example.

`upgrade` takes **no version** — the target is whatever the catalogue you point at declares. To move to a specific past version, point `<catalogue>` at that git ref.

The first two use the host tool's native verbs and follow that tool's conflict-resolution rules, not the catalogue's. The `agentbundle upgrade` verb is the only route that drops `*.upstream.<ext>` companions next to any Tier-2 file whose content has diverged since install — letting you walk the merges later via the `adapt-to-project` skill (see *One file at a time* below). Before it writes, it tells you how many of your edited files it will preserve as companions.

`<catalogue>` is the same URI you installed from, e.g. `git+https://git.example.test/<owner>/<catalogue>` or a local checkout path.

> **Check first.** `agentbundle list-installed` shows every installed pack with its version and whether an upgrade is available — run it before upgrading to see what's outstanding (see the [CLI reference](../reference/agentbundle.md#see-whats-installed)).

> **Multiple adapters.** If a pack is installed for more than one adapter at the scope, `upgrade` upgrades one adapter per run and asks you to `--adapter` which; the message lists each adapter with its version. Re-running against the version you already have is reported as `re-applied … (already current)`, not a version change.

> **Pitfall — `install --pack` is not the upgrade verb.** `agentbundle install --pack` refuses an in-place re-install. Use `upgrade --pack` to change an installed pack's version.

### One primitive at a time

Add a primitive filter to the same `upgrade` verb:

```bash
agentbundle upgrade --pack <name> --skill <skill-name> <catalogue>
```

`--agent`, `--hook`, `--seed <path>`, and `--command` work the same way. Only the named primitive moves; the rest of the pack stays at the previously-installed version. The CLI records the resulting mixed-version state in `.agentbundle-state.toml`; the next whole-pack upgrade flags it.

### One file at a time

Re-invoke the `adapt-to-project` skill. It walks any `*.upstream.<ext>` companions still on disk one by one, with per-file accept / edit / skip / decline. This is the merge UI for the companions a previous `agentbundle upgrade` (or first-install collision) left behind.

## Troubleshooting

**Source-conflict error.** If `agentbundle install` is refused with a source-conflict error — a message indicating that a different canonical source is already recorded for that pack name at this scope — see [Flow D in use-an-artifactory-catalogue.md](use-an-artifactory-catalogue.md#flow-d--source-conflict-remediation) for the two recovery paths (migrate the legacy row via `upgrade`, or uninstall and reinstall).

## Downgrades

Not supported in v0.1. To roll back: `agentbundle uninstall --pack <pack>` and reinstall at the prior version. Tier-2 (your edited copies) and Tier-3 (files outside the pack's projected paths) survive the uninstall by design — only the upstream-managed Tier-1 files are removed.

## Related

- [How to adapt a freshly-installed pack](../../../specs/adapt-to-project/spec.md) — the skill that walks `*.upstream.<ext>` companions.
- [RFC-0001 § Adopter file safety contract](../../../rfc/0001-bundle-distribution-by-adapter-spec.md#adopter-file-safety-contract) — the underlying guarantees.
