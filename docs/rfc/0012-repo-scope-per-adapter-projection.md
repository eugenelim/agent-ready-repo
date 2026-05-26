# RFC-0012: Repo-scope per-adapter projection

- **Status:** Draft
- **Author:** eugenelim
- **Date opened:** 2026-05-26
- **Date closed:**
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) (base bundle / install routes); [RFC-0004](0004-install-scope-per-pack.md) (scope dimension); [RFC-0008](0008-claude-plugins-install-route-parity.md) (claude-plugins route); [RFC-0010](0010-apm-install-route-parity.md) (apm route); [RFC-0011](0011-pack-allowed-adapters.md) (user-scope adapter resolution — this RFC closes its repo-scope erratum); [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md) (per-pack scope default + allowance)

## Summary

`agentbundle install --pack <name> --scope repo --adapter <name> .` lands the pack at the adopter repo's per-IDE directory directly — `<repo>/.claude/skills/`, `<repo>/.kiro/skills/`, `<repo>/.agents/skills/`, or `<repo>/.github/instructions/` — instead of the current dist-tree shape (`<repo>/claude-plugins/<pack>/...` and `<repo>/apm/<pack>/...`). The `--adapter` flag, which RFC-0011 bound to `--scope user`, lifts to work at both scopes; `[pack.install] allowed-adapters` gains repo-scope semantics; the dist-tree shape becomes opt-in via `--emit-install-routes` for catalogue-publishing workflows. Closes the gap RFC-0011's *Repo-scope projection* erratum left open: today there is no supported path through `agentbundle install` for a Kiro or Codex adopter to land a pack into their project-local `.kiro/skills/` or `.agents/skills/`. Contract bumps v0.6 → v0.7: every shipped adapter declares `[adapter.<name>.scope]` (Copilot gains one for the first time); `allowed-prefixes.repo` joins `allowed-prefixes.user` per adapter; the module-level constant `DEFAULT_USER_SCOPE_ADAPTER` is renamed `DEFAULT_ADAPTER` since it now governs greenfield resolution at both scopes.

## Motivation

**The shipped gap.** Today `agentbundle install --pack atlassian --scope repo .` produces `<repo>/claude-plugins/atlassian/.claude/skills/...` and `<repo>/apm/atlassian/.apm/skills/...` — dist-tree install-route artifacts, not anything an IDE reads at the project root. A Kiro adopter who wants `<repo>/.kiro/skills/atlassian-jira/SKILL.md` has no path through this CLI today. APM's `HookIntegrator` projects to Claude Code, Cursor, Gemini, and Copilot per RFC-0010, but [Kiro isn't on that list](../guides/explanation/install-routes.md). Kiro's own extension model is Open VSX (VS Code extensions, not per-project skill content); its Kiro Powers bundle format has no documented programmatic install verb. The only published paths today are: (a) `agentbundle install --scope user` → `~/.kiro/skills/` (works since RFC-0011), or (b) manual copy from `dist/`. Option (a) doesn't help adopters who want project-pinned skill versions; option (b) bypasses the file-safety contract.

**The erratum that revealed the shape.** RFC-0011's Draft proposed exactly this RFC's idea (`allowed-adapters` filters per-IDE directories at repo scope) and was [walked back in the post-merge erratum](0011-pack-allowed-adapters.md) because the premise was wrong about *current* behaviour: `--scope repo` doesn't emit per-IDE directories at all. The erratum closed the wrong door: it noted *"`allowed-adapters` is strictly user-scope-only"* (line 88) but left open whether repo-scope projection itself should change. This RFC takes the open question and answers it.

**The dist-tree-as-default mismatch.** `make build` already produces canonical install-route artifacts at `dist/claude-plugins/`, `dist/apm/`, `dist/marketplace.json` for catalogue maintainers to publish. `agentbundle install --scope repo` redundantly produces the same shape into an adopter repo where the artifacts have no downstream consumer — adopters use `/plugin install <pack>@agent-ready-repo` (which reads the catalogue's `dist/claude-plugins/`, not their own) or `apm install` (which reads the catalogue's `dist/apm/`). The dist-tree-at-the-adopter is the install verb solving a problem nobody has.

**The enterprise-single-IDE shape.** Some adopting organisations standardise on one approved agentic IDE (Kiro, Claude Code, or Codex). Today the resolver's `DEFAULT_USER_SCOPE_ADAPTER = "claude-code"` lets them rebrand the default at user scope; at repo scope there's no equivalent because the dist-tree-shape ignores adapter choice. Lifting `--adapter` to repo scope plus renaming the constant to `DEFAULT_ADAPTER` gives a single rebrand point that covers both scopes uniformly.

**The file-safety contract works at repo scope today** ([explanation](../guides/explanation/file-safety-contract.md)). `<repo>/.agentbundle-state.toml` carries the per-pack file SHAs, Tier-1/2/3 classification, install_route, and (post RFC-0011 AC10a) the resolved adapter. The mechanism that protects adopter edits is already there; we just need the projection to land at per-IDE prefixes so the SHAs map to files the IDE actually reads.

## Proposal

### CLI surface

`agentbundle install` gains repo-scope behaviour for `--adapter`:

```
agentbundle install --pack <name> --scope repo --adapter <name> <catalogue>
agentbundle install --pack <name> --scope repo <catalogue>           # uses DEFAULT_ADAPTER
agentbundle install --pack <name> --scope repo --emit-install-routes <catalogue>  # dist-tree (legacy publishing)
```

- **`--adapter` is no longer bound to `--scope user`.** Pinned message `install: --adapter is bound to --scope user` at install.py:107-115 and 204-213 is removed; `--adapter` accepted at either scope.
- **No `--adapter` at `--scope repo`** falls back to `DEFAULT_ADAPTER` (currently `"claude-code"`). Enterprise rebrands flip the constant once; both scopes pick up the new value.
- **`--emit-install-routes`** is the opt-in for the legacy dist-tree shape. Catalogue maintainers who script publishing keep their existing workflow by adding the flag. Adopters never need it.
- **`--adapter` and `--emit-install-routes` are mutually exclusive at `--scope repo`** — they target different artefact shapes; combining them is incoherent. argparse refuses the combination.

### Resolver

`_resolve_target_adapter` (renamed from `_resolve_user_scope_target_adapter` since it now covers both scopes) keeps the six-step lookup from RFC-0011, with each step's scope-conditional logic spelled out:

0. **Publisher-vs-installer drift refusal (AC15-equivalent)** — `allowed-adapters` entries must be in `shipped_adapters_from_contract()`. At repo scope, the user-scope-capability subcheck is skipped (Copilot is admissible at repo scope but not at user scope).
1. **`--adapter` override** — validated against `allowed-adapters` (when declared) or the shipped set at repo scope / the user-scope-capable set at user scope.
2. **State-hint short-circuit** — `state_adapter` returns directly when admissible; AC10b's logic extends to repo scope identically.
3. **Contract-version gate** — `< 0.7` packs fall through to step 5 at repo scope unconditionally (legacy heuristic preserved). v0.7+ packs with `allowed-adapters` declared consult the field at step 4.
4. **Per-adapter probe (user scope) / default (repo scope)** — at user scope, walk `allowed-adapters` against populated `~/.<ide>/` homes (the probe table from RFC-0011 step 3). At repo scope, **skip the probe** and return `DEFAULT_ADAPTER` if it's in `allowed-adapters`, else `allowed-adapters[0]`. Probing for `<repo>/.claude/` etc. would silently pick whatever IDE last touched the repo, which is exactly the silent-misdetection failure mode this RFC is meant to avoid.
5. **Legacy heuristic** — `.apm/agents/*.md` present ⇒ `kiro`; else `claude-code`. Unchanged.

### Contract bump v0.6 → v0.7

- **Every shipped adapter declares `[adapter.<name>.scope]`.** Copilot gains a scope table for the first time; existing tables grow an `allowed-prefixes.repo` key. Shape:

  ```toml
  [adapter."claude-code".scope]
  repo = "."
  user = "~"
  allowed-prefixes.repo = [".claude/"]
  allowed-prefixes.user = [".claude/", ".agentbundle/"]
  
  [adapter.kiro.scope]
  repo = "."
  user = "~"
  allowed-prefixes.repo = [".kiro/"]
  allowed-prefixes.user = [".kiro/", ".agentbundle/"]
  
  [adapter.codex.scope]
  repo = "."
  user = "~"
  allowed-prefixes.repo = [".agents/skills/"]
  allowed-prefixes.user = [".agents/skills/", ".agentbundle/"]
  
  [adapter.copilot.scope]
  repo = "."
  allowed-prefixes.repo = [".github/instructions/"]
  # No user key — Copilot has no user-scope projection.
  ```

- **Why `.agentbundle/` is in user-scope but not repo-scope prefixes.** At user scope, `~/.agentbundle/` namespaces CLI infrastructure under a single dot-directory: `state.toml` (per-pack file SHAs, install_route, resolved adapter, hook_wiring_owned — the source of truth for the file-safety contract), `credentials.env` (Tier-3 dotfile credentials per skill-secrets spec), `.adapt-install-marker.toml`, `.adapt-discovery.toml`, `.adapt-pending.md`. At repo scope, the repo *is* the namespace — `<repo>/.agentbundle-state.toml` and `<repo>/.adapt-install-marker.toml` live as top-level dotfiles, not under any directory. The path-jail already admits top-level dotfiles at repo scope; no `.agentbundle/` directory is needed there.

- **`allowed-adapters` becomes scope-uniform.** Validated at both scopes; the user-scope-capability subcheck (AC22) only fires when the pack's resolved scope is user. A pack declaring `allowed-adapters = ["claude-code", "kiro"]` and resolved at repo scope refuses `--adapter codex` with the same pinned message it would at user scope.

- **`[adapter.<name>.scope].repo` becomes mandatory** for every adapter that participates in repo-scope projection (i.e., every shipped adapter). The schema enforces this at validate time. `user` stays optional (Copilot omits it).

### Module-level constant rename

`agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER` → `agentbundle.scope.DEFAULT_ADAPTER`. The constant's value (`"claude-code"`) is unchanged; the rename reflects the widened semantics. Backwards compatibility kept via a deprecation alias for one minor release — `DEFAULT_USER_SCOPE_ADAPTER = DEFAULT_ADAPTER` with a `DeprecationWarning` on import — then removed.

### State file

`PackState.adapter` records the resolved adapter at both scopes (RFC-0011 AC10a's lift extends to repo scope). State-hint short-circuit (AC10b) consults `state.adapter` at both scopes on upgrade; the cross-adapter refusal at `upgrade.py:318-326` still fires for genuine drift. No state-schema version bump — the field already exists and is already populated; this RFC just stops it from being silently `"claude-code"` for non-claude-code repo-scope installs.

### What changes for the four user-scope-capable packs

`atlassian`, `figma`, `converters`, `contracts` already declare `allowed-adapters = ["claude-code", "kiro", "codex"]` (RFC-0011). At repo scope, the four packs become installable into `.claude/skills/`, `.kiro/skills/`, or `.agents/skills/` respectively — same `allowed-adapters` set, new resolver path. The `[pack.adapter-contract] version` bump to `"0.7"` happens on the implementation spec's clock; until then the v0.6 packs continue to work (the legacy heuristic at step 5 catches `< 0.7` packs at repo scope and falls back to the old dist-tree shape).

### What changes for the four repo-only packs

`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras` are unchanged. They have no `allowed-adapters` (the field is optional); they admit any shipped adapter at repo scope per the implicit-default semantics. An adopter running `agentbundle install --pack core --scope repo --adapter kiro .` lands `core`'s contents at `<repo>/.kiro/skills/`, `<repo>/.kiro/agents/`, etc. — the kiro adapter's projection rules apply.

### Migration path

| Adopter / use case | Today | Post-RFC-0012 |
| --- | --- | --- |
| Kiro adopter, repo scope | No supported path; manual copy from `dist/` | `agentbundle install --pack X --scope repo --adapter kiro .` |
| Claude Code adopter, repo scope, default IDE | `agentbundle install --pack X --scope repo .` → dist-tree | `agentbundle install --pack X --scope repo .` → `.claude/skills/` (default kicks in) |
| Catalogue maintainer publishing artifacts | `agentbundle install --scope repo .` | `agentbundle install --scope repo --emit-install-routes .` (one flag added) |
| User-scope installs | Unchanged | Unchanged |
| Enterprise rebrand to Kiro | Flip `DEFAULT_USER_SCOPE_ADAPTER = "kiro"` — covers user scope only | Flip `DEFAULT_ADAPTER = "kiro"` — covers both scopes |

The behavioural change for adopters running `agentbundle install --scope repo .` against a user-scope-capable pack is real and intentional: the default output changes from dist-tree to `.claude/skills/`. Catalogue maintainers who scripted `--scope repo` to mirror artifacts add `--emit-install-routes` to their script — single-line fix. The implementation spec ships the migration note in the per-version pack-upgrade guide.

## Alternatives considered

1. **Do nothing.** Keep the dist-tree shape; tell adopters who want `.kiro/skills/` to wait for APM Kiro support (out of our roadmap) or copy manually. *Rejected:* leaves a real and named gap that adopters hit today; the manual-copy workaround was exactly the Tier-3 squatter problem [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) and [RFC-0004](0004-install-scope-per-pack.md) set out to prevent.

2. **Build a `kiro-plugins` sibling install route (and `codex-plugins` later).** Mirror [RFC-0008](0008-claude-plugins-install-route-parity.md)'s claude-plugins shape per IDE. *Rejected:* Kiro has no programmatic plugin-install API to integrate with — its extension model is Open VSX (VS Code extensions, not skill content) and Kiro Powers has no documented install verb ([researched](https://kiro.dev/docs/editor/extension-registry/)). Building a route for which no consumer exists upstream is premature; adds maintenance burden for no adoption.

3. **Wait for APM to add Kiro `HookIntegrator` support.** APM is upstream of this catalogue; adding Kiro support is their roadmap call. *Rejected:* indefinite wait on a third-party project; the gap exists today and is closeable within agentbundle's own surface area.

4. **Auto-probe `<repo>/.claude/` / `<repo>/.kiro/` / `<repo>/.agents/skills/` at repo scope (symmetric to user-scope step 3).** *Rejected per recommendation* — at user scope the probe leverages the natural fact that IDEs populate `~/.<ide>/` on install. At repo scope, those directories rarely pre-exist except via an earlier `agentbundle install` (which would then make the probe self-perpetuating to the first IDE installed). The greenfield case is most repos; auto-detect would silently misdirect. `DEFAULT_ADAPTER` + explicit `--adapter` covers the cases cleanly.

5. **Keep the dist-tree as default; gate per-adapter behind a flag (`--per-adapter` or similar).** *Rejected:* makes the rarely-used legacy shape the default and the common-case workflow the opt-in. The current shape only serves catalogue publishing; that's the opt-in, not the default.

6. **Drop `--emit-install-routes` entirely; let `make build` be the only dist-tree producer.** *Rejected (for this RFC):* deferred. There's a real chance `--emit-install-routes` has no adoption either (every catalogue maintainer runs `make build` instead), in which case a future RFC removes the flag once telemetry shows it isn't used. Keeping it for one transitional release is the conservative call.

7. **Fan out at repo scope (write to `.claude/skills/` AND `.kiro/skills/` from one install).** *Rejected:* breaks the one-install-one-adapter invariant the rest of the system carries. Multi-IDE adopters run install twice with different `--adapter` values; state file rows distinguish them by `adapter` and `scope` cleanly. Fan-out would mean each pack has multiple rows per scope, a state-schema bump, and a new uninstall flow.

8. **Skip the contract bump; treat `allowed-prefixes.repo` as derivable from existing projection `target-path` values.** *Rejected:* the path-jail needs a single declared list to consult, not a transitive derivation from the per-primitive projection rules. The explicit `allowed-prefixes.repo` is one line per adapter and makes the path-jail's input self-contained.

## Drawbacks

1. **Behavioural change at the default.** Adopters scripting `agentbundle install --scope repo .` against the four user-scope-capable packs see a different on-disk shape post-merge. Catalogue maintainers see the same. The mitigation (add `--emit-install-routes` to publishing scripts) is one flag, but it's a flag; existing CI pipelines will need a one-line fix.

2. **Contract bump cost.** v0.6 → v0.7 ripples through `pack.toml` for any pack opting into the resolver's repo-scope path. The four user-scope packs will bump again (they just bumped to v0.6 in RFC-0011); the four repo-only packs don't need to bump unless they want to use `allowed-adapters` at repo scope to restrict targets (none currently do).

3. **`--emit-install-routes` may be a flag without users.** If `make build` covers every catalogue-publishing case, the flag exists only to placate the alternative-3 fallback. We carry it for one release, then revisit; orphan-flag churn is real cost.

4. **Probe asymmetry between scopes.** User scope probes `~/.<ide>/`; repo scope doesn't probe. Reviewers may push for symmetry. The asymmetry is intentional but deserves the dedicated mention here so it doesn't surprise readers of the resolver code; the docstring will name it explicitly.

5. **Copilot at repo scope is a third user.** Today Copilot's projection writes `.github/instructions/<pack>.md` via the build pipeline; landing that in adopter repos via `agentbundle install` is new behaviour. The `.github/instructions/` namespace overlaps with adopter-authored Copilot instructions; Tier-1/2/3 still applies, but the collision surface is wider than `.claude/skills/` (where the catalogue's three top-level dirs rarely conflict with adopter content). Copilot adopters will encounter `.upstream.md` companion files more often.

6. **The state.adapter field at repo scope was already populated dataclass-default `"claude-code"` for every install post-AC10a.** Existing repo-scope state files written between RFC-0011 and this RFC's implementation will carry `adapter = "claude-code"` regardless of what an adopter actually wanted (because no `--adapter` was passable at repo scope). Upgrade-time, AC10b's state-hint will then route the upgrade to claude-code even on a kiro-targeted reinstall. **Mitigation:** the migration guide documents the one-time uninstall + reinstall step (same shape as RFC-0011's pre-AC10a migration paragraph in [v05-to-v06-pack-upgrade.md](../guides/how-to/v05-to-v06-pack-upgrade.md)).

7. **The legacy heuristic at step 5 becomes scope-conditional.** Today the heuristic fires for `< 0.6` packs at user scope only (repo scope doesn't invoke the resolver). After this RFC, `< 0.7` packs at repo scope also hit the heuristic — which says *"agents present ⇒ kiro"*. A v0.2 pack with `.apm/agents/` installed at `--scope repo --adapter kiro` for the first time would route to kiro via the heuristic *and* via the explicit flag agreement — same answer, but the code path runs the heuristic instead of taking the declarative shortcut. Cosmetic; harmless.

## Prior art

### In this repo

- **[RFC-0011 § Repo-scope projection erratum (lines 78-92)](0011-pack-allowed-adapters.md)** — the post-merge correction that named the gap this RFC closes. *"`allowed-adapters` constrains user-scope installs only … At repo scope, the install-route fan-out (`apm`, `claude-plugins`, and the future codex-plugins addressed by the sibling RFC) is governed by which `[[adapter.<name>.install-routes]]` recipes the contract declares, not by per-pack `allowed-adapters`."* This RFC is the named follow-on.
- **[RFC-0004](0004-install-scope-per-pack.md)** — established `[scope]` table, `default-scope`, `allowed-scopes`, and the per-pack default-plus-allowance shape. Repo-scope writes' path-jail allowances trace to this RFC's framework.
- **[RFC-0008](0008-claude-plugins-install-route-parity.md)**, **[RFC-0010](0010-apm-install-route-parity.md)** — install-route parity precedent. Both added per-route artifacts to the dist-tree (`dist/claude-plugins/`, `dist/apm/`); this RFC takes the inverse direction (when install isn't going through a downstream route, write the per-IDE shape directly).
- **`packages/agentbundle/agentbundle/build/main.py:167-171`** — `DEFAULT_RECIPES` is the current source of the dist-tree-at-repo-scope shape (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`). This RFC's implementation reads these only when `--emit-install-routes` is passed.
- **`packages/agentbundle/agentbundle/build/recipes/self-host.toml`** — the catalogue's own self-host overlay *already* produces per-IDE direct writes at `.claude/skills/`, `.kiro/skills/`, `.agents/skills/` for the catalogue root. The mechanism this RFC generalises exists in-tree; only the adopter-side dispatcher is new.
- **[RFC-0001 § Distribution outputs](0001-bundle-distribution-by-adapter-spec.md)** — the original distribution model. The dist-tree shape comes from here.

### External

- **[VS Code workspace settings](https://code.visualstudio.com/docs/configure/settings)** and **[Contribution Points](https://code.visualstudio.com/api/references/contribution-points)** — first-class project-local config under `.vscode/settings.json`, scope declarations (`window`, `workspace`, `machine`) per contribution. Direct precedent for project-local IDE config at the repo root.
- **[pnpm: Building production-ready artifacts from a monorepo](https://github.com/orgs/pnpm/discussions/4478)** — explicit precedent for splitting "install for local use" from "build artifacts for redistribution." pnpm's `--prod` mode parallels our proposed `--emit-install-routes`.
- **[Bun workspaces](https://bun.com/docs/guides/install/workspaces)** — workspace installs land at project-local paths; redistribution is a separate verb. Same split.
- **No directly comparable per-IDE-adapter install resolver found** — the multi-IDE ecosystem doesn't have a published RFC pattern for what we're doing (the adapter-contract approach itself is novel per [RFC-0001](0001-bundle-distribution-by-adapter-spec.md)). The closest analogues are package-manager `--target` flags (Cargo's `--target` for cross-compilation, etc.), which name the runtime/platform; ours names the consuming IDE — a different axis but the same shape of dispatch.

## Unresolved questions

1. **Should `--emit-install-routes` be deprecated and removed in a future RFC, or is there a long-term role for it?** The shape exists today as `make build`'s output; an adopter-side opt-in flag duplicates the producer. *Author's lean: keep for one transitional release (~3 months), then revisit with telemetry on flag usage. If no live caller, deprecate.*

2. **Does `core` (and the other three repo-only packs) declare `allowed-adapters` to constrain repo-scope targets?** A pack like `core` ships Claude Code-specific subagents and hooks; landing it via `--adapter copilot` would silently drop the subagents and copy hook bodies the adapter can't run. *Author's lean: yes — `core` declares `allowed-adapters = ["claude-code"]` to refuse silent degradation. Tracked in the implementation spec's `Boundaries — Ask first` for the per-pack list.*

3. **Behaviour of `--scope repo --adapter <name>` against a pack with no `allowed-adapters` declared.** Today repo-only packs admit any shipped adapter implicitly. After this RFC, an adopter passing `--adapter codex` against `core` would get a coherent attempt but degraded output (most of `core`'s primitives don't project to codex). *Author's lean: warn-don't-refuse on first call (degraded-info-log style); pin a follow-on RFC to formalise per-pack adapter declarations for repo-only packs.*

4. **Should the `--emit-install-routes` flag emit ALL install routes the contract declares per adapter, or only those the pack's `[pack.install]` admits?** Today `make build` emits both `dist/claude-plugins/` and `dist/apm/` for every pack. *Author's lean: emit all (the catalogue-publishing use case wants the full artifact set; filtering is a future RFC's surface).*

5. **Migration timing for the four user-scope-capable packs.** RFC-0011 bumped them to v0.6 last week. The implementation spec for this RFC would bump them to v0.7. Two contract bumps in two RFCs is friction for downstream pack authors who pin pack versions. *Author's lean: keep v0.7 — the gap is real and worth one more bump; the migration guide consolidates the two contract versions into one upgrade walk.*

## Follow-on artifacts

To be filled in on acceptance. Anticipated:

- **Spec** at `docs/specs/repo-scope-per-adapter-projection/` — implementation contract for the work, mirroring `pack-allowed-adapters/spec.md` in shape. Tasks T1-T11 expected: contract bump v0.6 → v0.7 + `[adapter.copilot.scope]` table + `allowed-prefixes.repo` on existing adapters; resolver rename + repo-scope handling; CLI flag lift + `--emit-install-routes`; constant rename + deprecation alias; four user-scope-capable packs bump to v0.7; install-time message rail extension; documentation surface (`v06-to-v07-pack-upgrade.md`, README, two architecture pages); integration tests for the three new repo-scope adapter paths.
- **ADR** at `docs/adr/0004-repo-scope-per-adapter-projection.md` — records the architectural decision to make per-IDE direct writes the repo-scope default and the dist-tree shape opt-in. Pairs with ADR-0002 (per-pack default-plus-allowance).
- **`docs/CONVENTIONS.md`** — possibly: a one-line note that `agentbundle install --scope repo` defaults to per-IDE direct writes (catalogue-distribution use cases pass `--emit-install-routes`). Depends on whether reviewers want this surfaced at the conventions layer or kept inside the implementation spec.
- **`docs/guides/how-to/v06-to-v07-pack-upgrade.md`** — the migration guide; one section covers the `state.adapter` pre-AC10a-at-repo-scope edge case (Drawback #6).
- **README's `Where primitives land` table** — gains repo-scope columns for each adapter (mirroring the user-scope columns added in RFC-0011's docs).
