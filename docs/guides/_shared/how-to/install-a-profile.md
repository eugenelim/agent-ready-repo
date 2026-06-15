# How to install a curated set of packs in one command

Install a role's whole toolkit, or a repo's full governance setup, in one command instead of running `install --pack` N times. A **profile** is a first-party-curated, single-scope set of packs the catalogue ships ready to install.

## Prerequisites

- The `agentbundle` CLI on your PATH (`pip install agentbundle`, or the [clone-and-pip route](install-agentbundle-from-clone.md)).
- A catalogue URI — a local checkout path or `git+https://github.com/eugenelim/agent-ready-repo`.

## Discover what's available

```bash
agentbundle list-profiles <catalogue>
```

It prints each profile's id, scope, and description. The two shipped profiles:

| Profile | Scope | Installs |
| --- | --- | --- |
| `solution-architect` | user | `architect` + `research` + `contracts` — a solution architect's portable toolkit, carried across every repo. |
| `full-ceremony` | repo | `core` + `governance-extras` + `user-guide-diataxis` + `monorepo-extras` — a repo's full governance setup. |

## Install a profile

```bash
agentbundle install --profile <name> <catalogue>
```

For example, to set up a repo's full governance bundle:

```bash
agentbundle install --profile full-ceremony git+https://github.com/eugenelim/agent-ready-repo
```

The command installs every pack in the profile **at the profile's declared scope**, in the authored dependency-first order (so `core` lands before the packs that build on it), onto **one** adapter target. A pack already installed at that scope is left alone and reported `already present, skipped`. When it finishes, you get a per-pack summary of what was installed, skipped, or failed.

A profile install is never less safe than installing each pack by hand: it runs every pack's preconditions — scope, dependencies, adapter, path confinement — **before writing anything**. If any pack can't be installed, the command refuses before the first write and names the pack.

## Pick the adapter

By default the install resolves one adapter for the whole batch the same way a single-pack install does (your configured adapter, else the auto-detected one, else the default). To pin a specific IDE for every pack in the profile:

```bash
agentbundle install --profile solution-architect <catalogue> --adapter codex
```

The adapter is applied to every pack. If one pack in the profile doesn't support the chosen adapter, the command refuses before any write and suggests a compatible one.

## Upgrade or remove later

A profile is a one-time convenience for *installing* a set — it is not recorded as an entity. To change versions or remove packs afterward, act on the individual packs with the normal verbs: [`agentbundle upgrade --pack <name>`](upgrade-packs.md) and `agentbundle uninstall --pack <name>`. There is no `upgrade --profile` or `uninstall --profile`.

## Pitfalls

> **`--profile` and `--pack` are mutually exclusive.** Pick one. To install a single pack, use `--pack`; to install a set, use `--profile`.

> **`--scope` is rejected with `--profile`.** A profile declares its own scope in its manifest — `solution-architect` is user-scope, `full-ceremony` is repo-scope. You don't (and can't) choose the scope at install time.

> **A pack already installed at the *other* scope blocks the profile.** Profiles are single-scope and won't install the same pack across scopes. If a pack in the profile is already installed at the opposite scope, the command refuses and names it — uninstall it from that scope first, or install the remaining packs individually.

> **A partial install is not rolled back.** On a genuine I/O failure mid-batch (a full disk, say), packs already written stay; the dependency-first order guarantees the installed prefix is still consistent, and the per-pack summary tells you exactly where it stopped. Re-running the command resumes — already-installed packs are skipped.

## Related

- [The pack catalogue](../explanation/pack-catalogue.md) — what packs and profiles are, and the two-scope model.
- [Install routes](../explanation/install-routes.md) — the install→adapt chain a profile install inherits per pack.
- [How to upgrade an installed pack](upgrade-packs.md) — the per-pack upgrade verb.
