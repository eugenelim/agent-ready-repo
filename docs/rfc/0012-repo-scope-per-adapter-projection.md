# RFC-0012: Repo-scope per-adapter projection

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-26
- **Date closed:** 2026-05-26
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) (base bundle / install routes); [RFC-0004](0004-install-scope-per-pack.md) (scope dimension); [RFC-0008](0008-claude-plugins-install-route-parity.md) (claude-plugins route); [RFC-0010](0010-apm-install-route-parity.md) (apm route); [RFC-0011](0011-pack-allowed-adapters.md) at commit `af1b6c8` plus PR #132 erratum at commit `45049f1` (user-scope adapter resolution — this RFC closes its repo-scope erratum); [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md) (per-pack scope default + allowance)

## Summary

**CLI surface.** `agentbundle install --pack <name> --scope repo --adapter <name> .` lands the pack at the adopter repo's per-IDE directory directly — `<repo>/.claude/skills/`, `<repo>/.kiro/skills/`, `<repo>/.agents/skills/`, or `<repo>/.github/instructions/` — instead of the current dist-tree shape (`<repo>/claude-plugins/<pack>/...` and `<repo>/apm/<pack>/...`). The `--adapter` flag, which RFC-0011 bound to `--scope user`, lifts to work at both scopes; the existing argparse `choices=` already enumerates every shipped adapter (RFC-0011's implementation widened from the user-scope-capable subset its text named; no `cli.py` edit needed for the lift). The dist-tree shape becomes opt-in via `--emit-install-routes` for catalogue-publishing workflows.

**Contract surface.** v0.6 → v0.7: every shipped adapter declares `[adapter.<name>.scope]` (Copilot gains one for the first time); `allowed-prefixes.repo` joins `allowed-prefixes.user` per adapter. `[pack.install] allowed-adapters` gains repo-scope semantics: the field is now validated at both scopes, with the user-scope-capability subcheck scope-conditional.

**Constant rename.** The module-level constant `DEFAULT_USER_SCOPE_ADAPTER` is renamed `DEFAULT_ADAPTER` since it now governs default-adapter resolution at both scopes. Enterprise rebrands flip one constant to cover both `--scope user` and `--scope repo`.

**Why now.** Closes the gap RFC-0011's *Repo-scope projection* erratum left open: today there is no supported path through `agentbundle install` for a Kiro or Codex adopter to land a pack into their project-local `.kiro/skills/` or `.agents/skills/`.

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
- **`--adapter` and `--emit-install-routes` are mutually exclusive at `--scope repo`** — they target different artefact shapes; combining them is incoherent. **Refusal is handler-level** (not `argparse.add_mutually_exclusive_group`), because the exclusion is scope-conditional — `--emit-install-routes` is meaningless at user scope and refused independently there with its own message. The pinned wording is enumerated under *Pinned refusal messages* below.

### Pinned refusal messages

| Trigger | Message (stderr) | Code site |
| --- | --- | --- |
| Pack declares `[pack.install] allowed-scopes` not including the requested scope (e.g. user-only pack invoked at `--scope repo`) | `<pack>: scope '<requested>' not in allowed-scopes <declared-set>` *(unchanged; exception raised in `scope.py:scope.resolve()`, formatted to stderr in `install.py` handler that catches `ScopeRefused`)* | install.py handler (catches `ScopeRefused` from `scope.resolve()`) |
| `--emit-install-routes` at `--scope user` | `install: --emit-install-routes is bound to --scope repo` | install.py handler |
| `--adapter X --emit-install-routes` at `--scope repo` | `install: --adapter and --emit-install-routes are mutually exclusive at --scope repo` | install.py handler |
| `--adapter X` against pack with declared `allowed-adapters` not including `X`, at either scope | `install: --adapter X not in pack's allowed-adapters set` *(unchanged from RFC-0011)* | resolver step 1 |
| `--adapter copilot` at `--scope user` against pack with no `allowed-adapters` | `install: --adapter copilot not admitted as a user-scope-capable adapter under contract v0.7` *(version string updated from v0.6; only fires at user scope, per AC15 scope-conditional subcheck)* | resolver step 1 |
| `<verb>: pack '<name>' declares allowed-adapter '<X>' which is not admitted by adapter contract v0.7 shipped with agentbundle <cli-version>` | publisher-drift refusal at either scope (`<verb>` ∈ `{install, upgrade}`) | resolver step 0 |

The refusal-ordering invariant: `scope.resolve()` fires first (declared-scope refusals), then handler-level flag refusals (mutex / repo-vs-user binding), then resolver-internal refusals (publisher-drift at step 0, `--adapter` at step 1). The implementation spec pins this order via integration tests.

The implementation spec asserts each string exactly in dedicated tests (mirrors RFC-0011's AC15 pattern).

### Install-time message rail (repo scope)

RFC-0011 AC14 added `installed: <pack> @ user via <adapter>` and the "other declared adapters" suffix at user scope. RFC-0012 extends symmetrically:

| Install shape | Stdout line |
| --- | --- |
| `--scope repo --adapter kiro <repo>` (no flag, default adapter, or explicit) | `installed: <pack> @ repo via kiro` |
| `--scope repo --emit-install-routes <repo>` | `emitted install routes for <pack> at <route-list>` where `<route-list>` enumerates every emitted route under the bundled contract joined with " and " (today: `<repo>/claude-plugins/<pack>/ and <repo>/apm/<pack>/`; a future codex-plugins addition would extend the list automatically). Tests pin substring presence per emitted route, not the full string. |
| `--scope user --adapter kiro` | `installed: <pack> @ user via kiro` *(unchanged)* |

The "other declared adapters" suffix from RFC-0011 AC14 stays user-scope-only — at repo scope there is no probe, so there are no "other adapters that matched a probe" to suggest. The default-adapter case at repo scope omits any suffix.

### Reliability — projection-vs-state write ordering

The shipped ordering at user scope today (verified at `packages/agentbundle/agentbundle/commands/install.py:583-672`) is **projection-then-state**: the per-file write loop at 583-611 lands every projection file and populates `new_pack_state.files[relpath]` per-file in memory; `new_pack_state.adapter = user_target_adapter` at line 627 happens after the loop; `state.toml` reaches disk at `safety.write_jailed(...)` lines 664-672 only after that. Repo scope inherits the same ordering. The crash window is **"projection files on disk, no state row on disk"** (not the inverse).

This crash window is **not benign as a naive retry**. On retry-install, `_classify_for_install` reads the on-disk file but finds no matching state row (because state.toml never reached disk), classifies the file as **Tier-2 (squatter)**, and writes a `.upstream.<ext>` companion next to every orphan file from the prior crashed run. The adopter ends up with a coherent install plus a tree of stale companion files — structurally safe, visually confusing.

The implementation spec ships **two coordinated artifacts** to close the gap:

1. **New helper `safety.scan_for_pack_artifacts(root, allowed_prefixes) -> list[Path]`** (net-new infrastructure; named here so the spec's task list has a slot for it; lives alongside the existing `safety.write_jailed` and adopts the same path-jail rules). Walks every `<root>/<prefix>/` declared in the adapter's `allowed-prefixes.<scope>` and returns any file present on disk. The scan is read-only; no state mutation.

2. **Defensive AC at install start.** Before classifying any file, if `state.toml` has no row for the pack being installed AND `scan_for_pack_artifacts(root, allowed_prefixes)` returns a non-empty list, stderr emits `install: orphan projection files for pack <name> at <prefix> — prior install interrupted; rerun with --force to clean and reinstall, or delete the listed paths and rerun`. The install **refuses** rather than proceeding into the Tier-2 companion proliferation. `--force` adds an "I know what I'm doing" override that deletes the orphans first.

**Regression test (in spec, not RFC).** Monkeypatch `safety.write_jailed` to raise on the Nth call inside the projection loop; assert no state row written; rerun install without `--force` and assert the orphan refusal fires with the pinned wording; rerun with `--force` and assert the install completes and `state.files` matches every on-disk path. This is the falsifier for the "retry guarantee" — without it a future refactor that reorders the write sequence silently regresses the recovery path. The construction-tests list at the bottom of Follow-on artifacts pins this test.

### Resolver

`_resolve_target_adapter` (renamed from `_resolve_user_scope_target_adapter` since it now covers both scopes) extends the lookup RFC-0011 shipped — and *explicitly renumbers* it.

**Step-count reconciliation.** RFC-0011's body labelled its resolver "six-step" but the implementation that shipped at `install.py:1383-1531` has **five steps (0–4)** because RFC-0011 combined "contract-version gate" and "per-adapter probe" into one. RFC-0012 splits the combined step in two so the repo-scope branch has a clean attachment point — taking the lookup from 5 to 6 steps (0–5). Three surfaces carry the "six-step" claim today; the implementation spec amends each: (a) the function docstring at `install.py:1393`; (b) the test-module docstring at `packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py:1`; (c) an **erratum block appended to RFC-0011** noting the step-count discrepancy, mirroring how RFC-0011 itself recorded its repo-scope erratum (RFC-0011 is Accepted/frozen per `docs/CONVENTIONS.md`, so the fix is an erratum block, not an in-body edit). The new function is **scope-branched at three steps** (step 0's user-scope-capability subcheck, step 4's probe-vs-default-adapter, step 5's heuristic semantics for `< v0.7` packs at repo scope) — the branching is intentional; the docstring names it; the implementation spec adds a unit test that pins repo scope does **not** probe `<repo>/.<ide>/` even when those directories exist.

0. **Publisher-vs-installer drift refusal (AC15-equivalent)** — `allowed-adapters` entries must be in `shipped_adapters_from_contract()`. At repo scope, the user-scope-capability subcheck is skipped (Copilot is admissible at repo scope but not at user scope).
1. **`--adapter` override** — validated against `allowed-adapters` (when declared) or the shipped set at repo scope / the user-scope-capable set at user scope.
2. **State-hint short-circuit** — `state_adapter` returns directly when admissible; AC10b's logic extends to repo scope identically.
3. **Contract-version gate** — gated on **two conjoined predicates**: `allowed_adapters is not None` AND `contract_supports_hook_wiring(version)` (the latter true for any `version not in {"0.1", "0.2"}` per `scope.py:239`). RFC-0011 already ANDs these in code (`install.py:1508-1511`); RFC-0012 preserves it (no tightening to `< 0.7`). A v0.3-0.6 pack that declares `allowed-adapters` consults the field at step 4 — same as today at user scope. A v0.6+ pack omitting `allowed-adapters` drops straight to step 5 (legacy heuristic) regardless of contract version. **At user scope, the step 3 / step 4 split is descriptive only — the same code paths run in the same order as today, only the docstring step labels change. Repo scope is where step 4 newly diverges (default-adapter instead of probe).**
4. **Per-adapter probe (user scope) / default-adapter (repo scope)** — at user scope, walk `allowed-adapters` against populated `~/.<ide>/` homes (the probe table RFC-0011 shipped). At repo scope, **skip the probe** and return `DEFAULT_ADAPTER` if it's in `allowed-adapters`, else `allowed-adapters[0]`. The asymmetry is intentional and load-bearing — see Drawback #4. *"Greenfield" was the user-scope label for "no probe matched"; at repo scope every install hits the no-probe branch by construction, so the section calls it the "default-adapter branch" instead.*
5. **Legacy heuristic** — `.apm/agents/*.md` present ⇒ `kiro`; else `claude-code`. Unchanged at user scope. **At repo scope** the same heuristic fires for `< v0.7` packs that omit `allowed-adapters` — but it can only return `"kiro"` or `"claude-code"`, never `"codex"` or `"copilot"`, so an enterprise rebrand to `DEFAULT_ADAPTER = "codex"` cannot route a pre-v0.7 pack at repo scope to codex via this path. The implementation spec lands the migration story: any pack that wants the enterprise-rebrand default at repo scope bumps to v0.7 (one-line `pack.toml` edit).

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

`agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER` → `agentbundle.scope.DEFAULT_ADAPTER`. The constant's value (`"claude-code"`) is unchanged; the rename reflects the widened semantics. Backwards compatibility kept via a deprecation alias for one minor release — `DEFAULT_USER_SCOPE_ADAPTER = DEFAULT_ADAPTER` with a `DeprecationWarning` on import. **Removal version: `agentbundle 0.2.0`** (current `0.1.0` per `packages/agentbundle/agentbundle/version.py:17`). Single-sourced here; Follow-on artifacts reference this section rather than re-stating the version.

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

The behavioural change for adopters running `agentbundle install --scope repo .` against a user-scope-capable pack is real and intentional: the default output changes from dist-tree to `.claude/skills/`. Catalogue maintainers who scripted `--scope repo` to mirror artifacts add `--emit-install-routes` to their script — single-line fix.

## Alternatives considered

1. **Do nothing.** Keep the dist-tree shape; tell adopters who want `.kiro/skills/` to wait for APM Kiro support (out of our roadmap) or copy manually. *Rejected:* leaves a real and named gap that adopters hit today; the manual-copy workaround was exactly the Tier-3 squatter problem [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) and [RFC-0004](0004-install-scope-per-pack.md) set out to prevent.

2. **Build a `kiro-plugins` sibling install route (and `codex-plugins` later).** Mirror [RFC-0008](0008-claude-plugins-install-route-parity.md)'s claude-plugins shape per IDE. *Rejected:* Kiro has no programmatic plugin-install API to integrate with — its extension model is Open VSX (VS Code extensions, not skill content) and Kiro Powers has no documented install verb ([researched](https://kiro.dev/docs/editor/extension-registry/)). Building a route for which no consumer exists upstream is premature; adds maintenance burden for no adoption.

3. **Wait for APM to add Kiro `HookIntegrator` support.** APM is upstream of this catalogue; adding Kiro support is their roadmap call. *Rejected:* indefinite wait on a third-party project; the gap exists today and is closeable within agentbundle's own surface area.

4. **Auto-probe `<repo>/.claude/` / `<repo>/.kiro/` / `<repo>/.agents/skills/` at repo scope (symmetric to user-scope step 3).** *Rejected per recommendation* — at user scope the probe leverages the natural fact that IDEs populate `~/.<ide>/` on install. At repo scope, those directories rarely pre-exist except via an earlier `agentbundle install` (which would then make the probe self-perpetuating to the first IDE installed). The greenfield case is most repos; auto-detect would silently misdirect. `DEFAULT_ADAPTER` + explicit `--adapter` covers the cases cleanly.

5. **Keep the dist-tree as default; gate per-adapter behind a flag (`--per-adapter` or similar).** *Rejected:* makes the rarely-used legacy shape the default and the common-case workflow the opt-in. The current shape only serves catalogue publishing; that's the opt-in, not the default.

6. **Drop `--emit-install-routes` entirely; let `make build` be the only dist-tree producer.** *Rejected for now, but documented as the likely successor.* The implementation spec keeps `--emit-install-routes` for one transitional release to preserve the back-compat surface for any downstream caller scripting `agentbundle install --scope repo` for publishing. **Search predicate:** `grep -rn "agentbundle install.*--scope repo" Makefile .github/workflows/ docs/guides/how-to/` finds zero invocations (only `--scope repo` references in RFC/spec narrative text). The public-facing publishing path is `make build` (which `release-preflight` and the wheel-release workflow at RFC-0011-followup PR #131 both use exclusively). The implementation spec lands the flag with a `DeprecationWarning` on use and an explicit *Unresolved #1 → remove in next minor* commitment. If telemetry shows zero adoption after one release, RFC-0012b drops it.

7. **Fan out at repo scope (write to `.claude/skills/` AND `.kiro/skills/` from one install).** *Rejected:* breaks the one-install-one-adapter invariant the rest of the system carries. Multi-IDE adopters run install twice with different `--adapter` values; state file rows distinguish them by `adapter` and `scope` cleanly. Fan-out would mean each pack has multiple rows per scope, a state-schema bump, and a new uninstall flow.

8. **Skip the contract bump; treat `allowed-prefixes.repo` as derivable from existing projection `target-path` values.** *Rejected:* the path-jail needs a single declared list to consult, not a transitive derivation from the per-primitive projection rules. The explicit `allowed-prefixes.repo` is one line per adapter and makes the path-jail's input self-contained.

## Drawbacks

1. **Behavioural change at the default.** Adopters scripting `agentbundle install --scope repo .` against the four user-scope-capable packs see a different on-disk shape post-merge. Catalogue maintainers see the same. The mitigation (add `--emit-install-routes` to publishing scripts) is one flag, but it's a flag; existing CI pipelines will need a one-line fix.

2. **Contract bump cost.** v0.6 → v0.7 ripples through `pack.toml` for any pack opting into the resolver's repo-scope path. The four user-scope packs will bump again (they just bumped to v0.6 in RFC-0011); the four repo-only packs don't need to bump unless they want to use `allowed-adapters` at repo scope to restrict targets (none currently do).

3. **`--emit-install-routes` may be a flag without users.** If `make build` covers every catalogue-publishing case, the flag exists only to placate the alternative-3 fallback. We carry it for one release, then revisit; orphan-flag churn is real cost.

4. **Probe asymmetry between scopes.** User scope probes `~/.<ide>/`; repo scope doesn't probe. Reviewers may push for symmetry. The asymmetry is intentional and load-bearing — see the unit-test AC under Follow-on artifacts — but the choice has one observable consequence: **per-pack independence at repo scope.** State-hint at step 2 is per-pack, so pack A can resolve to kiro and pack B to claude-code in the same repo, leaving `<repo>/.kiro/skills/A/` next to `<repo>/.claude/skills/B/`. The default-adapter at step 4 makes the no-flag case consistent across packs (everything routes to `DEFAULT_ADAPTER`), but explicit `--adapter` per pack can diverge. Documented as an Unresolved question (#2) for the cross-pack consistency question; the asymmetry itself stays.

5. **Copilot at repo scope is a third user.** Today Copilot's projection writes `.github/instructions/<pack>.md` via the build pipeline; landing that in adopter repos via `agentbundle install` is new behaviour. The `.github/instructions/` namespace overlaps with adopter-authored Copilot instructions; Tier-1/2/3 still applies, but the collision surface is wider than `.claude/skills/` (where the catalogue's three top-level dirs rarely conflict with adopter content). Copilot adopters will encounter `.upstream.md` companion files more often.

6. **The state.adapter field at repo scope was already populated dataclass-default `"claude-code"` for every install post-AC10a.** Existing repo-scope state files written between RFC-0011 and this RFC's implementation will carry `adapter = "claude-code"` regardless of what an adopter actually wanted (because no `--adapter` was passable at repo scope). Upgrade-time, AC10b's state-hint will then route the upgrade to claude-code even on a kiro-targeted reinstall. **Affected population.** Adopters who passed `--scope repo` against `atlassian` / `figma` / `converters` / `contracts` in the RFC-0011 → RFC-0012 window — an explicit override against the user-scope default for those packs. The repo doesn't ship telemetry, so the exact count is unknown; the upper bound is "everyone who ran repo-scope install of a user-scope-default pack in this window," and the realistic-deliberate-override population is small. The four repo-only packs (`core` et al.) are unaffected because they never declared `allowed-adapters` and route through the legacy heuristic at step 5.

**Mitigation, two parts:**
(a) Affected adopters perform a one-time uninstall + reinstall to move from the dist-tree shape to the per-IDE shape; the uninstall surface handles both the dist-tree shape (legacy) and the per-IDE shape (post-RFC-0012) since `state.files` tracks per-relpath SHAs regardless of which top-level directory they sit under.
(b) The implementation spec adds an **in-band detection AC** at `agentbundle install --scope repo` covering three triggers (not just disagreement). Trigger precedence is **(b) → (a) → (c)** so the most-specific shape-mismatch signal fires before the more-generic disagreement and orphan signals; only the first matching trigger emits:
   - **(b) Shape-mismatch:** `state.toml` exists, was written by CLI version `< <RFC-0012-version>` (read from `state.toml` if recorded, otherwise inferred from `state.install_route == "cli"` + missing `<RFC-0012>`-introduced fields), AND projection files exist under the dist-tree shape (`<repo>/claude-plugins/<pack>/` or `<repo>/apm/<pack>/`). Catches the **same-default-agrees-but-shape-changed** case where the resolver returns claude-code matching the recorded default but the on-disk layout is dist-tree. Stderr names the dist-tree paths to remove. (Note: this trigger keys on **CLI version + on-disk shape**, not state-schema-version — `STATE_SCHEMA_VERSION` is v0.3 today and this RFC does not bump it.)
   - **(a) Adapter disagreement:** `state.toml` exists, was written by CLI version `< <RFC-0012-version>`, AND resolver's pick disagrees with `state.adapter` — explicit drift signal.
   - **(c) Orphan recovery:** `state.toml` has no row for the pack but projection files exist (the orphan-projection case from §Reliability). This is the safety-net path; refuses install unless `--force` is passed.

Each trigger pins its own stderr line. Detection runs once per pack per session and short-circuits to silence after the first run. *(The angle-bracket `<RFC-0012-version>` is the CLI version at which this RFC's implementation lands — the spec pins the literal value.)*

7. **The legacy heuristic at step 5 doubles its live-pack surface area.** Today the heuristic fires for `< 0.6` packs at user scope only (repo scope doesn't invoke the resolver). After this RFC, `< 0.7` packs at repo scope also hit the heuristic — which says *"agents present ⇒ kiro"*. Three concrete consequences worth naming:
   - **Codex / Copilot rebrand cannot route pre-v0.7 packs at repo scope.** The heuristic can only return `"kiro"` or `"claude-code"`. An enterprise that flips `DEFAULT_ADAPTER = "codex"` and runs `agentbundle install --pack X --scope repo .` (no `--adapter`) against a v0.2 pack hits step 5 and gets claude-code or kiro — not codex. **Important: bumping pack version alone does NOT escape the heuristic.** Step 3 requires `allowed_adapters is not None` *and* `contract_supports_hook_wiring(version)`; a v0.7 pack that omits `allowed-adapters` still drops to step 5. The four repo-only catalogue packs (`core` et al.) sit on v0.2 today; the implementation spec bumps them to v0.7 to align with the contract bump, but they cannot escape the heuristic until they also declare `allowed-adapters` (the sibling RFC under *Resolved during review* / Follow-on artifacts). Until that sibling RFC lands, repo-only-pack installs at `--scope repo` continue to route via the heuristic (claude-code/kiro only).
   - **Removing the heuristic is now harder.** RFC-0011's "retired someday when no live pack relies on it" plan doubled its scope: every pre-v0.7 repo-scope install now relies on it too. The retirement gets pushed out at least one minor release.
   - **Explicit `--adapter` short-circuits at step 1**, so the heuristic only fires in the no-flag fall-through case — adopters who pass `--adapter` are unaffected.

## Prior art

### In this repo

- **[RFC-0011 § Repo-scope projection erratum (lines 78-92)](0011-pack-allowed-adapters.md)** — the post-merge correction that named the gap this RFC closes. *"`allowed-adapters` constrains user-scope installs only … At repo scope, the install-route fan-out (`apm`, `claude-plugins`, and the future codex-plugins addressed by the sibling RFC) is governed by which `[[adapter.<name>.install-routes]]` recipes the contract declares, not by per-pack `allowed-adapters`."* This RFC is the named follow-on.
- **[RFC-0004](0004-install-scope-per-pack.md)** — established `[scope]` table, `default-scope`, `allowed-scopes`, and the per-pack default-plus-allowance shape. Repo-scope writes' path-jail allowances trace to this RFC's framework.
- **[RFC-0008](0008-claude-plugins-install-route-parity.md)**, **[RFC-0010](0010-apm-install-route-parity.md)** — install-route parity precedent. Both added per-route artifacts to the dist-tree (`dist/claude-plugins/`, `dist/apm/`) plus, in RFC-0010's case, install-time fan-out via APM's `HookIntegrator`; this RFC takes the inverse direction at adopter install (when install isn't going through a downstream marketplace, write the per-IDE shape directly into the adopter repo).
- **`packages/agentbundle/agentbundle/build/main.py:167-171`** — `DEFAULT_RECIPES` is the current source of the dist-tree-at-repo-scope shape (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`). This RFC's implementation reads these only when `--emit-install-routes` is passed.
- **`packages/agentbundle/agentbundle/build/recipes/self-host.toml`** — the catalogue's own self-host overlay *already* produces per-IDE direct writes at `.claude/skills/`, `.kiro/skills/`, `.agents/skills/` for the catalogue root. The mechanism this RFC generalises exists in-tree; only the adopter-side dispatcher is new.
- **[RFC-0001 § Distribution outputs](0001-bundle-distribution-by-adapter-spec.md)** — the original distribution model. The dist-tree shape comes from here.

### External

- **[VS Code workspace settings](https://code.visualstudio.com/docs/configure/settings)** and **[Contribution Points](https://code.visualstudio.com/api/references/contribution-points)** — first-class project-local config under `.vscode/settings.json`, scope declarations (`window`, `workspace`, `machine`) per contribution. Direct precedent for project-local IDE config at the repo root.
- **[pnpm: Building production-ready artifacts from a monorepo](https://github.com/orgs/pnpm/discussions/4478)** — explicit precedent for splitting "install for local use" from "build artifacts for redistribution." pnpm's `--prod` mode parallels our proposed `--emit-install-routes`.
- **[Bun workspaces](https://bun.com/docs/guides/install/workspaces)** — workspace installs land at project-local paths; redistribution is a separate verb. Same split.
- **No directly comparable per-IDE-adapter install resolver found** — the multi-IDE ecosystem doesn't have a published RFC pattern for what we're doing (the adapter-contract approach itself is novel per [RFC-0001](0001-bundle-distribution-by-adapter-spec.md)). The closest analogues are package-manager `--target` flags (Cargo's `--target` for cross-compilation, etc.), which name the runtime/platform; ours names the consuming IDE — a different axis but the same shape of dispatch.

## Unresolved questions

1. **Should `--emit-install-routes` be deprecated and removed in a future RFC, or is there a long-term role for it?** The shape exists today as `make build`'s output; an adopter-side opt-in flag duplicates the producer. *Author's lean: keep for one transitional release with `DeprecationWarning`; if telemetry shows zero adoption, RFC-0012b drops it. See Alternative #6 for the cost-side rationale.*

2. **Cross-pack adapter consistency at repo scope.** Resolver step 2 (state-hint) is per-pack; nothing in this RFC prevents pack A from resolving to kiro and pack B from resolving to claude-code in the same repo. The state file's `[packs.<name>]` rows distinguish them by `adapter`, but the resulting `<repo>/.claude/` + `<repo>/.kiro/` coexistence may surprise adopters. *Author's lean: accept the across-pack independence (matches user-scope behaviour where the same `$HOME` carries packs across IDEs); revisit if adopters report it as a footgun.*

3. **`--emit-install-routes` scope of emission.** Should the flag emit ALL install routes the contract declares per adapter, or only those the pack's `[pack.install]` admits? Today `make build` emits both `dist/claude-plugins/` and `dist/apm/` for every pack. *Author's lean: emit all (the catalogue-publishing use case wants the full artifact set; filtering is a future RFC's surface).*

4. **Migration timing for the four user-scope-capable packs.** RFC-0011 bumped them to v0.6 last week. The implementation spec for this RFC would bump them to v0.7. Two contract bumps in two RFCs is friction for downstream pack authors who pin pack versions. *Author's lean: keep v0.7 — the gap is real and worth one more bump.*

### Resolved during review

- **`core` (and the three other repo-only packs) declaring `allowed-adapters` is out of scope for this RFC.** Originally raised as an unresolved question; resolved on adversarial review to keep the contract bump's adopter-side cost bounded to the four user-scope-capable packs (Drawback #7 already touches the repo-only packs by forcing a v0.2 → v0.7 bump to escape the legacy heuristic). Per-pack `allowed-adapters` declarations for repo-only packs (e.g. `core` declaring `allowed-adapters = ["claude-code"]` to refuse silent degradation against codex/copilot) ship as a sibling RFC (RFC-0013 candidate). The follow-on artifacts list pins this.
- **Degraded-adapter warning is out of scope for this RFC.** Originally proposed: a `--scope repo --adapter codex` against `core` (which has no `allowed-adapters` and no codex-meaningful primitives) would emit a `degraded-info-log`-style warning. Resolved on quality review: the warning string would drift without a pin, and the sibling RFC for repo-only-pack `allowed-adapters` (above) makes the warning unnecessary — once `core` declares `allowed-adapters = ["claude-code"]`, `--adapter codex` against it refuses cleanly with the existing pinned message. No new warning surface.

## Follow-on artifacts

To be filled in on acceptance. Anticipated:

- **Spec** at `docs/specs/repo-scope-per-adapter-projection/` — implementation contract for the work, mirroring `pack-allowed-adapters/spec.md` in shape. Tasks T1-T11 expected: contract bump v0.6 → v0.7 + `[adapter.copilot.scope]` table + `allowed-prefixes.repo` on existing adapters; resolver rename to `_resolve_target_adapter` + step-renumber (5 → 6 steps) + repo-scope handling + reconciliation of RFC-0011's docstring; CLI flag lift + `--emit-install-routes` + handler-level mutex refusal with pinned wording; constant rename + deprecation alias (removal version per *Module-level constant rename* above); four user-scope-capable packs bump to v0.7; **also** the four repo-only packs bump v0.2 → v0.7 in the same PR to escape the legacy heuristic at step 5 per Drawback #7; install-time message rail extension with pinned strings (see *Install-time message rail (repo scope)*); documentation surface (README, two architecture pages); integration tests for the three new repo-scope adapter paths.
- **Sibling RFC (RFC-0013 candidate)** — per-pack `allowed-adapters` declarations on repo-only packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`). Constrains repo-scope targets so an adopter passing `--adapter copilot` against `core` refuses with the existing pinned message rather than silently dropping primitives. Out of scope for RFC-0012 to keep this RFC's adopter-side cost bounded; the contract surface this RFC ships is what the sibling RFC consumes.
- **ADR** at `docs/adr/0004-repo-scope-per-adapter-projection.md` — records the architectural decision to make per-IDE direct writes the repo-scope default and the dist-tree shape opt-in. Pairs with ADR-0002 (per-pack default-plus-allowance).
- **`docs/CONVENTIONS.md`** — possibly: a one-line note that `agentbundle install --scope repo` defaults to per-IDE direct writes (catalogue-distribution use cases pass `--emit-install-routes`). Depends on whether reviewers want this surfaced at the conventions layer or kept inside the implementation spec.
- **README's `Where primitives land` table** — gains repo-scope columns for each adapter (mirroring the user-scope columns added in RFC-0011's docs).

### Implementation-spec-level ACs surfaced on review

The spec must include these so the implementation contract is testable from day one:

- **AC: in-band detection of pre-RFC-0012 repo-scope state.** When `agentbundle install --scope repo` runs and `state.toml` exists, was written by an `agentbundle` version `< <RFC-0012-version>`, and the resolver's pick disagrees with `state.adapter`, stderr emits a one-line warning with pinned wording naming the uninstall+reinstall step. Test pins the exact string.
- **AC: `allowed-prefixes.repo` path-jail enforcement at safety layer.** A kiro-resolved repo-scope install must fail-closed via `safety.PathJailError` (the existing path-jail exception at `safety.py:69`, propagated to stderr as `install: <message>`) if any recipe attempts a write to `.claude/skills/`, even if that write would land inside the repo root. New unit test module under `packages/agentbundle/tests/unit/test_safety_repo_scope_prefixes.py`.
- **AC: probe-asymmetry pinned by unit test.** Repo-scope resolver does NOT probe `<repo>/.claude/` even when the directory exists — with `--adapter kiro` and `<repo>/.claude/` populated, result must be `kiro`, not `claude-code`. Pins the asymmetry as load-bearing behaviour; refuses the symmetric refactor.
- **AC: existing `install: --adapter is bound to --scope user` tests inverted.** Every test asserting that string is deleted or flipped to assert admission at repo scope. Spec's task list enumerates the test file paths so the deletion is part of the contract.
- **AC: resolver test fixture widens to materialise `pack.toml` (or stub contract).** Repo-scope behaviour depends on `[adapter.<name>.scope].repo` and `allowed-prefixes.repo`; the current `_make_pack` helper at `test_resolve_user_scope_target_adapter.py` doesn't exercise the scope-table read. Spec's *Always do* names the fixture widening.
- **AC: `DEFAULT_ADAPTER` deprecation alias.** `DEFAULT_USER_SCOPE_ADAPTER = DEFAULT_ADAPTER` with `DeprecationWarning` on import. Removal version: see *Module-level constant rename* above (single-sourced). Separate test asserts the warning fires; the existing test at `test_resolve_user_scope_target_adapter.py:139` is renamed and flipped to import `DEFAULT_ADAPTER` directly.

### High-leverage construction tests (from quality review)

The implementation spec pins these in per-task `Tests:` subsections. They cover the spec-vs-implementation join — unit tests would miss them, integration tests catch them:

- **`test_repo_scope_kiro_greenfield_writes_projection_and_state`** — install at `--scope repo --adapter kiro` lands `<repo>/.kiro/skills/<skill>/SKILL.md`, records `state.adapter = "kiro"`, prints `installed: <pack> @ repo via kiro`. Failure of any of the three is a regression.
- **`test_repo_scope_upgrade_consults_state_adapter_not_disk`** — AC10b at repo scope. Install under `--adapter kiro`; later create `<repo>/.claude/`; upgrade — state stays `kiro`, no cross-adapter refusal.
- **`test_emit_install_routes_flag_gates_dist_tree_shape`** — two installs of the same pack: one without `--emit-install-routes` lands `.kiro/skills/`; one with the flag lands `claude-plugins/` + `apm/`. Proves the opt-in is exclusive at the right axis.
- **`test_repo_scope_refuses_adapter_with_emit_install_routes`** — handler-level mutex refusal with pinned message.
- **`test_resolver_step_0_publisher_drift_at_both_scopes`** — same refusal text at both scopes (scope-uniform drift refusal). *Implementation note: extend the existing step-0 drift test in `test_resolve_user_scope_target_adapter.py` with a `scope=repo` parametrise; don't add a separate test module. **Task ordering matters:** the parametrise depends on (a) resolver function renamed and gaining `scope: str` parameter, (b) `fake_home` fixture widened or sibling `fake_repo` fixture added, and (c) `_make_pack` materialising `pack.toml` for the scope-table read. The spec's task list orders fixture-widen (a→b→c) before the parametrise.*
- **`test_repo_scope_retry_after_partial_projection_reconciles`** — monkeypatch `safety.write_jailed` to raise on the Nth call inside the projection loop; assert no state row written; rerun install without `--force` and assert the orphan-refusal stderr fires; rerun with `--force` and assert install completes with `state.files` matching every on-disk path. Falsifier for the §Reliability retry-guarantee claim.
- **`test_repo_scope_does_not_probe_dot_claude`** — load-bearing probe-asymmetry test.
