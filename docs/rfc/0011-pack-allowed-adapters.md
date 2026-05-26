# RFC-0011: Per-pack `allowed-adapters` declaration for user-scope adapter resolution

- **Status:** Open
- **Author:** eugenelim
- **Date opened:** 2026-05-25
- **Date closed:**
- **Builds on:**
  - [RFC-0004](0004-install-scope-per-pack.md) — defines the `[pack.install]` table this RFC extends with a new field (existing fields unchanged).
  - [RFC-0005](0005-user-scope-hook-support.md) — precedent for an adapter-targeted contract bump.
  - [RFC-0004 § Unresolved questions](0004-install-scope-per-pack.md#unresolved-questions) — implements the open lean *"Should `[pack.install]` carry more fields than `default-scope` and `allowed-scopes`?"*.
- **Builds on (continued):** [RFC-0009](0009-codex-native-skills.md) (Accepted 2026-05-25). RFC-0009's code shipped in commit `49061e6` (PR #113) and is governance-ratified; the codex `direct-directory` skill projection at `.agents/skills/` is the live contract entry RFC-0011 extends with a `[adapter.codex.scope]` user-root table. No standalone `Depends on:` — RFC-0009 closed before RFC-0011 opens for review.

## Summary

Add a per-pack `[pack.install] allowed-adapters = [...]` declaration to `pack.toml` that constrains **user-scope installs** to the listed adapters: at user scope it picks the target adapter (`claude-code` / `kiro` / `codex`). *(Original Draft framed this as applying uniformly at both scopes; the repo-scope half was an erratum corrected post-merge — see § *Repo-scope projection*.)* Adds an adopter-side `--adapter` CLI flag on `install` for the user-scope multi-IDE adopter and a module-level constant `agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER` (default: `"claude-code"`) as the greenfield fallback. Replaces the agents-presence heuristic at `_resolve_user_scope_target_adapter` in `packages/agentbundle/agentbundle/commands/install.py:1249-1275`, whose docstring already names this RFC as the intended fix. Adds an `[adapter.codex.scope]` table to the contract pointing user-scope codex installs at `~/.agents/skills/` (per [Codex's skills documentation](https://developers.openai.com/codex/skills): *"`$HOME/.agents/skills` — any skills checked into the user's personal folder. Use to curate skills relevant to a user that apply to any repository the user may work in."*). Adapter-contract bump `0.5 → 0.6`; `allowed-adapters` is **optional** — omitting it defaults to "all shipped adapters" (current behaviour at repo scope, agents-presence heuristic at user scope). Codex plugins (`~/.codex/plugins/cache/...`, `.codex-plugin/plugin.json`) are a separate install route, addressed by a sibling RFC modeled on RFC-0008's Claude-plugins parity — not this RFC.

## Motivation

A Kiro-only adopter installing `agentbundle install --pack atlassian --scope user .` against this catalogue today lands the pack's skills in `~/.claude/skills/` — for an IDE they do not run. The four user-scope-capable packs we ship (`atlassian`, `figma`, `converters`, `contracts`) all resolve to Claude Code through the agents-presence heuristic, because none of them ships `.apm/agents/*.md` (they are skills-only). There is no override.

The cost of inaction:

- **The catalogue's user-scope dimension is silently single-adapter.** RFC-0004 landed user scope deliberately ahead of any consumer; RFC-0005 lifted Kiro out of `degraded-info-log` and gave it a working `[scope]` table; RFC-0007 brought the first user-scope pack home; RFC-0009 (Accepted) flipped Codex to filesystem-discovered skills at `.agents/skills/` whose `$HOME` variant is itself the third user-scope target. The integration test all four RFCs paid for *does not actually exercise Kiro or Codex at user scope* — every user-scope pack we ship resolves to Claude Code by construction. The Kiro work is dead code from the adopter's perspective; Codex hasn't even been admitted into the user-scope set.
- **Adopter copies files by hand.** A Kiro user wanting the `jira` skill today copies `dist/apm/atlassian/skills/jira/` into `~/.kiro/skills/jira/`; a Codex user copies into `~/.agents/skills/jira/` — both outside the CLI, outside upgrade, outside uninstall, outside the Tier model. Exactly the Tier-3 squatter problem RFC-0001 set out to prevent and RFC-0004 extended to user scope for every primitive *except* the one that mattered to them. (Notwithstanding the hand-copy workaround, the `atlassian/flow-metrics` skill's sibling-script discovery was Claude-Code-only by hardcode — see the *Atlassian portability fix* note in § *Follow-on artifacts*. Fixed on this RFC's branch.)
- **The install-time TODO is load-bearing.** `_resolve_user_scope_target_adapter`'s docstring (install.py:1255-1260) names a corner case the heuristic provably mishandles: *"a Copilot-only pack with hooks (no agents) silently resolves to `claude-code` here."* The heuristic is a proxy that worked for the v0.2/v0.3/v0.4 packs we shipped and stops working the moment a pack's content portability does not correlate with its agents-presence.
- **The validate-time twin is the same shape.** `_kiro_target_adapters` in `validate.py:351-389` infers Kiro targeting from "`.apm/agents/` + `.apm/hook-wiring/` + v0.3 contract" — another heuristic that would simplify against an explicit declaration. Both call sites converge on `allowed-adapters` cleanly.

Why now: the dimension has shipped, two adapters declare working user-scope roots ([RFC-0005 § Adapter-level scope roots](0005-user-scope-hook-support.md#proposal)), Codex's user-scope shape (`~/.agents/skills/`) is documented upstream and reachable as soon as RFC-0009's projection flip lands, and four packs are sitting on the user-scope shelf already declaring `default-scope = "user"`. The asymmetry is fully built; the resolver is the missing piece.

## Proposal

### The `allowed-adapters` field

`[pack.install]` gains an `allowed-adapters` array under the new adapter-contract version `0.6`:

```toml
[pack]
name = "atlassian"
version = "0.1.0"

[pack.adapter-contract]
version = "0.6"

[pack.install]
default-scope = "user"
allowed-scopes = ["user", "repo"]
allowed-adapters = ["claude-code", "kiro", "codex"]
```

The semantic is **user-scope only**: `allowed-adapters` declares the set of adapters this pack's user-scope install can resolve to. The `allowed-scopes` field controls *where* the install lands (repo / user / both); `allowed-adapters` controls *which adapter the user-scope install picks* from the available set. *(See § *Repo-scope projection* for why `allowed-adapters` has no repo-scope semantics.)*

- **Optional.** Omitting `allowed-adapters` means user-scope resolution falls through to the legacy agents-presence heuristic at `_resolve_user_scope_target_adapter`. Legacy `< 0.6` packs (including the four shipped repo-only packs) need no migration.
- **Declared = constrain user-scope routing.** At user scope, the resolver walks `allowed-adapters` in declared order against the adapter-root probe (CLI home directories: `~/.claude/`, `~/.kiro/`, `~/.codex/`). The `--adapter` flag overrides the probe — see § *Resolution at install time*.
- **Adapter values constrained by the live contract.** The pack-schema validator reads `adapter.toml` and refuses any value that does not name a shipped adapter. For user-scope use (when `"user" ∈ allowed-scopes`), the named adapter must also declare an `[adapter.<name>.scope]` table with a `user` root — otherwise the schema refuses with `pack.toml: [pack.install] allowed-adapters contains '<name>', which does not declare a user-scope root in the v0.6 adapter contract`. For repo-scope-only packs, any shipped adapter is admissible (Copilot is fine here even though it has no user-scope projection). Under v0.6, user-scope-capable: `{"claude-code", "kiro", "codex"}`; repo-scope-capable: those three plus `"copilot"`.
- **No separate `default-adapter` scalar.** A separate field would duplicate the array's first element in nearly every case and add a `default-adapter ∈ allowed-adapters` cross-field invariant the schema would need to enforce. The greenfield default — for adopters whose machines have *no* matching CLI home — comes from a module-level constant (see § *Resolution at install time*), not the pack's TOML.

### Resolution at install time

User-scope adapter resolution is a four-step lookup, in order:

1. **`--adapter` CLI flag.** Highest priority. `agentbundle install --pack <name> --scope user --adapter kiro .` resolves to `kiro` unconditionally, bypassing the probe and the greenfield fallback. Bound to `--scope user` only — at repo scope, the flag is rejected with `install: --adapter is bound to --scope user`. Adapter-vs-pack admissibility check:
   - If the pack declares `allowed-adapters`, the requested adapter must be in that set. Otherwise refused: `install: --adapter <name> not in pack's allowed-adapters set`.
   - If the pack omits `allowed-adapters` (either a `< 0.6` pack or a v0.6 pack that didn't declare the field), the requested adapter must name a shipped *user-scope-capable* adapter under the live contract — i.e. an adapter declaring `[adapter.<name>.scope].user`. Today: `{"claude-code", "kiro", "codex"}`. A `--adapter copilot` invocation is refused regardless because Copilot has no user-scope root. This matches the schema's `__derived_from_adapter_toml__` enum semantics: when the pack does not constrain, the live contract does. See § *CLI surface* for the argparse entry.
2. **Contract version gate.** If the pack's `[pack.adapter-contract] version >= "0.6"` and `allowed-adapters` is declared, consult it. If the pack is `< 0.6` *or* declares no `allowed-adapters`, fall through to step 4 (legacy heuristic) — no migration forced.
3. **Adapter-root probe.** Walk `allowed-adapters` in declared order; for each candidate, check whether the adopter's home shows evidence the adapter is in use. The probe signal per adapter — its **CLI home directory**, created when the adopter first runs the IDE:
   - `claude-code` ⇒ `~/.claude/` exists?
   - `kiro` ⇒ `~/.kiro/` exists?
   - `codex` ⇒ `~/.codex/` exists *or* `~/.agents/skills/` exists?
     *(Codex stores plugins and config under `~/.codex/`; skills land under the shared `~/.agents/skills/` per upstream convention. The probe checks both because the upstream docs do not pin whether the Codex CLI creates `~/.codex/` on a skills-only first run independent of plugins use — an empirical gap captured in § *Unresolved questions*. The OR-probe ensures a Codex adopter with either signal resolves correctly.)*

   The first matching adapter wins. **Greenfield fallback:** if no CLI home matches, the resolver picks the value of the module-level constant `agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER` (default: `"claude-code"`) if that value is in the pack's `allowed-adapters`, otherwise `allowed-adapters[0]`. Install prints `installed: <pack> @ <scope> via <adapter>` on success (extending the `installed: <pack> @ <scope>` rail RFC-0004 set; the `via <adapter>` clause fires only at user scope, where adapter selection is non-obvious).
4. **Legacy heuristic (`< 0.6` packs or v0.6 packs omitting `allowed-adapters`).** Unchanged: `.apm/agents/*.md` present ⇒ `kiro`; else `claude-code`. **Inherited bug:** the legacy heuristic carries a documented same-name-Kiro-agent silent-overwrite limitation at `install.py:1262-1267`. This RFC retains the legacy path *as-is* — the limitation is not re-litigated here. v0.6 packs that *declare* `allowed-adapters` bypass the heuristic entirely; a future RFC retires the heuristic and addresses the limitation when no live pack relies on it.

The function `_resolve_user_scope_target_adapter` keeps its name. Its docstring TODO block is rewritten to: *"RFC-0011 landed `[pack.install] allowed-adapters` under contract v0.6 plus the `--adapter` CLI flag and the `DEFAULT_USER_SCOPE_ADAPTER` module constant. v0.6+ packs declaring `allowed-adapters` resolve via the four-step lookup; this function's legacy branch covers `< 0.6` packs and v0.6 packs omitting the field."*

The user-scope projection dispatch at install.py:1170-1178 (currently a two-arm `if target_adapter == "kiro": kiro.project(...) else: claude_code.project(...)`) gains a third arm calling `codex.project(...)`. The codex adapter's user-scope projection is the same `direct-directory` tree-copy logic the live `[[adapter.codex.projection]]` entry at adapter.toml:217-237 already uses for repo scope, rooted at `~/.agents/skills/` instead of `<repo>/.agents/skills/`.

### Repo-scope projection — `allowed-adapters` is user-scope-only

**Amended 2026-05-25 (post-merge erratum):** the Draft of this RFC carried a "Repo-scope projection fan-out" section claiming `agentbundle install --scope repo` projects pack content into every adapter's per-IDE directory (`.claude/skills/`, `.kiro/skills/`, `.agents/skills/`, `.github/instructions/`) simultaneously and proposed a filter against `allowed-adapters` at repo scope. Pre-EXECUTE review of the implementation spec (`docs/specs/pack-allowed-adapters/`) verified against code:

- `agentbundle install --scope repo` calls `render_pack(pack_dir)` per `install.py:438` with `DEFAULT_RECIPES = ("per-pack-claude-plugin", "per-pack-apm-package", "marketplace")` per `agentbundle/build/main.py:167-171`.
- The actual top-level prefixes in the projection are `{"apm", "claude-plugins"}` (dist-shaped install-route artifacts), **not** `{".claude/skills", ".kiro/skills", ".agents/skills", ".github/instructions"}`.
- The four-per-IDE-directory fan-out only happens via `make build-self`'s self-host recipe, whose adapter list is already hardcoded to `["claude-code", "codex"]` in `recipes/self-host.toml:14`. Self-host is the catalogue's own consumer of its packs; it does not run on adopter installs.

The premise of the original section was a wrong model of what `agentbundle install --scope repo` does. The repo-scope projection filter as described is unreachable.

**Resolution.** `allowed-adapters` constrains **user-scope installs only**. At repo scope, the install-route fan-out (`apm`, `claude-plugins`, and the future codex-plugins addressed by the sibling RFC) is governed by which `[[adapter.<name>.install-routes]]` recipes the contract declares, not by per-pack `allowed-adapters`. A v0.6 pack declaring `allowed-adapters = ["claude-code", "kiro"]` still emits `dist/apm/<pack>/` and `dist/claude-plugins/<pack>/` at repo scope unchanged — the field has no repo-scope semantics.

This narrows RFC-0011's surface and removes the "behaviour change at repo scope" footgun the Draft documented. The implementation spec drops repo-scope filter ACs accordingly.

A future RFC may revisit per-pack constraints on the install-route fan-out at repo scope if a real adopter need surfaces (e.g. a pack author wanting to publish only via APM, not via Claude plugins). That is a separate decision with different motivation; it is not what this RFC's `allowed-adapters` field gates.

### CLI surface

`agentbundle install`'s argparse setup at `cli.py:199-229` gains:

```python
sp.add_argument(
    "--adapter",
    choices=_user_scope_capable_adapters_from_contract(),  # derived at CLI-load
    help=(
        "Override the auto-detected adapter at user scope. "
        "Bound to --scope user; rejected at repo scope. "
        "Refused if the named adapter is not in the pack's allowed-adapters."
    ),
)
```

The `choices` tuple is **derived from the bundled `adapter.toml`** at CLI-load time — same hydration pattern as the schema's `__derived_from_adapter_toml__` enum (§ *Schema validation*). It enumerates adapters declaring `[adapter.<name>.scope].user`. Today: `("claude-code", "kiro", "codex")`. When a future RFC adds Copilot user-scope (or any other adapter's scope table), the argparse choices widen automatically — no `cli.py` edit required. A test pins the derivation against the live contract so contract drift breaks the test rather than silently producing wrong CLI behaviour.

The module-level constant lives at `packages/agentbundle/agentbundle/scope.py`:

```python
# Greenfield-fallback default for user-scope installs when no CLI home
# matches and --adapter was not passed. Treated by the resolver as a
# preference, not a hard pick — the value must be in the pack's
# allowed-adapters set; otherwise the resolver picks allowed-adapters[0].
DEFAULT_USER_SCOPE_ADAPTER: str = "claude-code"
```

### Contract bump `0.5 → 0.6`

`packages/agentbundle/agentbundle/_data/adapter.toml`'s `[contract] version` bumps from `"0.5"` to `"0.6"` and gains two changes:

1. The pack-schema requirement above (`allowed-adapters` required for v0.6 user-scope packs).
2. A new `[adapter.codex.scope]` table mirroring `claude-code` and `kiro`:

   ```toml
   [adapter.codex.scope]
   repo = "."
   user = "~"
   allowed-prefixes.user = [".agents/skills/", ".agentbundle/"]
   ```

   The `.agents/skills/` prefix matches Codex's documented skills location (`$HOME/.agents/skills/`); `.agentbundle/` matches the cross-adapter convention RFC-0004 set for the user-scope state file at `~/.agentbundle/state.toml`. The prefix is intentionally narrowed to `.agents/skills/` rather than `.agents/` — a broader prefix would permit writes anywhere under `~/.agents/`, including the Codex marketplace catalogue at `~/.agents/plugins/marketplace.json` (a file this RFC does not write and a sibling RFC will own). Narrowing now keeps the write-jail discipline of *"each RFC's contract opens only the subtrees it actually needs."* When the codex-plugins-install-route-parity sibling RFC lands, it widens to add `.agents/plugins/` per its own decisions.

There are no other projection-table changes, no new `mode` values, no rail shifts in this bump. RFC-0009's projection-mode flip for the codex `skill` primitive (from `managed-block-inline` to `direct-directory`) already shipped in commit `49061e6`; this RFC builds on the live `[[adapter.codex.projection]]` entry at lines 217-221 of the current `adapter.toml` and does not re-author it.

The four shipped user-scope packs (`atlassian`, `figma`, `converters`, `contracts`) — which currently declare `[pack.adapter-contract] version = "0.2"` because they consume only the user-scope dimension RFC-0004 landed — bump straight to `"0.6"` and declare `allowed-adapters = ["claude-code", "kiro", "codex"]` in the implementation PR. The jump skips v0.3/v0.4/v0.5 cleanly because those bumps were forks for hook-wiring (RFC-0005), claude-plugins-install-route (RFC-0008), and apm-install-route (RFC-0010) — none of which affects skill-only user-scope packs. Repo-only packs (`core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`) do **not** bump — their content is unchanged.

The repo's other heuristic, `_kiro_target_adapters` in `validate.py:351`, is similarly augmented: for v0.6+ packs, the rail consults `allowed-adapters` (Kiro in the set ⇒ Kiro-targeted); for `< 0.6` packs, the existing on-disk inference (agents + wiring + v0.3) stays. Both heuristics are kept; both gain an early-return for v0.6+ packs.

### Schema validation

`pack.schema.json` gains under `[pack.install]`:

```json
{
  "allowed-adapters": {
    "type": "array",
    "items": {"type": "string", "enum": ["__derived_from_adapter_toml__"]},
    "minItems": 1,
    "uniqueItems": true
  }
}
```

The `enum` is hydrated at validate time from `adapter.toml`'s set of all shipped adapters — `{"claude-code", "kiro", "codex", "copilot"}` under v0.6. The validator's per-value check is scope-aware: any shipped adapter name is admissible *if* the pack's `allowed-scopes` does not include `"user"`; for user-scope-eligible packs, each value must also name an adapter that declares an `[adapter.<name>.scope]` table with a `user` root (today: `{"claude-code", "kiro", "codex"}`). A user-scope-eligible pack listing `"copilot"` in `allowed-adapters` is refused: `pack.toml: [pack.install] allowed-adapters contains 'copilot', which does not declare a user-scope root in the v0.6 adapter contract; either remove 'copilot' or drop 'user' from allowed-scopes`.

`allowed-adapters` itself is **optional** — no required-when-user-scope rule. The schema accepts omission and the resolver falls back per § *Resolution at install time*.

**Publisher-vs-installer contract drift.** Schema validation runs in two places — `agentbundle validate` at publish time (against whatever `adapter.toml` is on disk in the catalogue clone) and `agentbundle install` at install time (against the bundled contract in the installed CLI). A pack validated against an older contract checkout can declare an adapter the *current* contract no longer admits — e.g. a v0.6 pack written before a hypothetical future RFC narrows the set. Install re-runs the enum check against the bundled contract and refuses with stderr: `install: pack '<name>' declares allowed-adapter '<adapter>' which is not admitted by adapter contract v<X.Y> shipped with agentbundle <cli-version>`. The publisher-vs-installer version-skew rail is named in `agent-spec-cli/spec.md` and inherited here; the message is the new addition.

### What this RFC does NOT do

- **No new `[pack.install]` constraints beyond `allowed-adapters`.** Future per-pack fields (e.g. a `requires-confirmation` flag for user-scope packs, named in RFC-0004's Unresolved Questions) are out of scope.
- **No Codex *plugins* install route.** Codex ships [a plugins surface separate from skills](https://developers.openai.com/codex/plugins/build) — package format `.codex-plugin/plugin.json`, install location `~/.codex/plugins/cache/$MARKETPLACE/$PLUGIN/$VERSION/`, marketplace catalogue at `~/.agents/plugins/marketplace.json`. This is a *new install route* analogous to Claude plugins ([RFC-0008](0008-claude-plugins-install-route-parity.md)) and APM ([RFC-0010](0010-apm-install-route-parity.md)), not an adapter-resolution decision. A sibling RFC modeled on RFC-0008's shape — *codex-plugins-install-route-parity* — adds `codex-plugins` to the codex adapter's `install-routes`, lands per-pack `dist/codex-plugins/<pack>/.codex-plugin/plugin.json`, aggregates a marketplace, and wires the install→adapt chain. That work is orthogonal to this RFC; the two can land in either order.
- **No re-resolution on upgrade.** A pack installed at user scope is upgraded against the same adapter root it was installed under, recorded in state. Switching adapters at upgrade time is a re-install, not an upgrade — `agentbundle uninstall --scope user` followed by `agentbundle install --scope user --adapter <name>`. Upgrade's existing `_resolve_user_scope_target_adapter` call (upgrade.py:218, 228, 308, 311) reads `allowed-adapters` through the same lookup but only for the adapter the pack is already installed under.
- **No deletion of the legacy heuristic.** The agents-presence heuristic at `_resolve_user_scope_target_adapter` stays for `< 0.6` packs and v0.6 packs that omit `allowed-adapters`. Deleting it earns its own future RFC once no live pack relies on it.

## Alternatives considered

1. **Do nothing — keep the heuristic.** The four shipped user-scope packs continue to land in `~/.claude/` for every adopter; Kiro adopters keep hand-copying. RFC-0004's and RFC-0005's investment in the user-scope dimension and Kiro's `[scope]` table stays partially-realized. The install.py TODO stays open indefinitely. *Rejected.* The asymmetry between "Kiro can host user-scope content per the contract" and "no shipped pack ever lands there" is the load-bearing motivation; doing nothing perpetuates it.

2. **Imperative `--adapter` flag on `install`, no `pack.toml` field.** Adopter passes `--adapter kiro` against any user-scope-eligible pack; install writes to `~/.kiro/skills/` regardless of pack-author intent. *Rejected as the sole mechanism* — but the imperative flag is **adopted as the escape valve** in combination with the declarative field (see item 3). The flag without the field loses the publisher's portability declaration; a pack whose content is Claude-Code-specific cannot signal that, and `--adapter kiro` against it writes broken content to `~/.kiro/skills/`. The field constrains *which* adapters the flag can target.

3. **Both declarative `allowed-adapters` and imperative `--adapter`.** *Adopted as the v1 surface.* Original Draft of this RFC rejected this in favour of declarative-only; adversarial review surfaced that the declarative-only resolution routes the modal multi-IDE adopter (anyone with `~/.claude/` already on disk) silently to Claude Code with no escape valve. Adopting the flag closes that gap. The flag is `--adapter <name>`, bound to `--scope user`, refused if the requested adapter is not in the pack's `allowed-adapters`. Docker `--platform` + manifest list is the closest external precedent: manifest declares supported platforms, client picks among them. The flag's footgun (Kiro adopter passes `--adapter claude-code` against a Kiro-only pack) is closed by the schema check — `allowed-adapters` is the constraint.

4. **Auto-detect from `~/.<ide>/` presence; no `pack.toml` field.** Drop `allowed-adapters` entirely; pick whichever adapter root exists on the adopter's machine. Cheaper still. *Rejected.* Loses the publisher's portability declaration — a pack whose content is Claude-Code-specific (an agent body referencing Claude Code's `model:` frontmatter shape, a skill that names `.claude/agents/`) cannot signal that to the installer; auto-detect would land it under a Kiro adopter's `~/.kiro/`, half-broken. The four shipped user-scope packs happen to be portable; a future personal-reviewer pack with Claude-Code-shaped agents would not be, and the contract has to support both.

5. **Reuse `allowed-scopes` semantics — overload the scope field with adapter pairs (e.g. `allowed-scopes = ["repo", "user@claude-code", "user@kiro"]`).** Avoids a new field. *Rejected.* Mixes two dimensions (scope, adapter) into one string-formatted array; the schema validator has to parse the `@` separator; existing call sites that read `allowed-scopes` as a `{repo, user}` set would have to dispatch on whether each entry contains an `@`. A separate array on the same `[pack.install]` table is the boring, obvious shape.

6. **`allowed-adapters` at repo scope.** The original Draft of this RFC rejected this; an iteration adopted it; the post-merge erratum (§ *Repo-scope projection*) reverted to rejection. *Final disposition: rejected.* The "uniform-at-both-scopes" framing assumed `agentbundle install --scope repo` fans out across the four per-IDE adapter directories (`.claude/skills/`, `.kiro/skills/`, etc.), which pre-EXECUTE review against code revealed is wrong — repo-scope `install` emits dist-shaped install-route artifacts (`apm/`, `claude-plugins/`), not per-IDE-adapter directories. The repo-scope-filter mechanism the iteration adopted has nothing to filter. A future RFC may revisit per-pack install-route constraints; this RFC does not.

7. **Land `allowed-adapters` under v0.5 (no contract bump).** Add the field as optional under the existing contract version; existing packs need no version change. *Rejected.* RFC-0004's precedent is strict: a new required field gets a contract bump so adopters can detect compatibility at the schema level (a v0.5 CLI consuming a v0.6 pack rightly refuses; a v0.6 CLI consuming a v0.5 pack falls through to the heuristic). An optional field under v0.5 leaves no signal for either direction, and the AC25 corner case (Copilot-only pack with hooks, no agents) the install-time TODO names stays open because the field is opt-in.

8. **Land `allowed-adapters` for `{claude-code, kiro}` only; add Codex via amendment once RFC-0009 Accepts.** Ship two adapters now, add the third later. *Rejected* — moot now that RFC-0009 is Accepted (closed 2026-05-25). Codex's user-scope shape (`~/.agents/skills/`, per the upstream skills documentation) is documented, stable, and the live adapter-contract entry (commit 49061e6, adapter.toml:217-237). The `[adapter.codex.scope]` table is a four-line addition with no design question still open. Splitting it into an amendment would mean two contract bumps (v0.5 → v0.6 → v0.7) for what is genuinely one decision — *"which adapters are user-scope-capable, and where does each one's user root live?"*

9. **Bundle Codex *plugins* into this RFC.** Cover the `~/.codex/plugins/` install route alongside the `~/.agents/skills/` user-scope target. *Rejected.* The plugins surface is a new install route — same architectural shape as RFC-0008 (Claude plugins) and RFC-0010 (APM). Each of those landed as a single-route RFC with a per-pack `SessionStart` writer, marketplace aggregation, dist-route emission, and the install→adapt chain wiring. Folding all of that into this RFC would mix two decisions (adapter resolution at user scope; new install-route plumbing) into one PR — exactly the bundling-failure mode RFC-0008 and RFC-0010 were each split out from. See § *What this RFC does NOT do* for the sibling-RFC pointer.

10. **Heuristic refuse-and-explain — no contract bump, no pack-side field.** The smallest possible fix: amend `_resolve_user_scope_target_adapter` to refuse-and-explain when the heuristic cannot decide (multiple `~/.<ide>/` populated, pack has no agents but ships hook-wiring for a non-default adapter, etc.), instead of silently guessing. No contract bump, no `allowed-adapters` field, no four-pack updates, no RFC-0009 dependency. *Rejected for two reasons.* (a) It closes the AC25 corner case named in the install.py TODO — *but only that corner case.* The load-bearing motivation isn't AC25; it's that *the catalogue's user-scope dimension is single-adapter for skills-only packs by construction*. Refuse-and-explain on the heuristic doesn't open Kiro or Codex; it just makes the silent failure noisier. Adopters wanting `jira` in Kiro still cannot get there. (b) The heuristic's domain is bounded by what filesystem evidence the pack provides (presence of `.apm/agents/`); for skills-only packs, no amount of refuse-and-explain disambiguates which adapter the *author* wrote the pack for. The four shipped skills-only packs would either be uniformly refused (everyone now blocked) or uniformly silent-defaulted (status quo, with extra error prose). Neither closes the motivation. *Worth recording* because the heuristic-refinement path is the steelman alternative-1 ("do nothing useful") that this RFC has to beat — and the rebuttal is the load-bearing motivation, not the AC25 corner case.

## Drawbacks

- **Contract bump cost.** v0.5 → v0.6 is the fourth contract bump since RFC-0004 (v0.1 → v0.2, then v0.3 / v0.4 / v0.5 for hooks / claude-plugins / apm). The four shipped user-scope packs jump from `[pack.adapter-contract] version = "0.2"` straight to `"0.6"`; CLI versions older than the v0.6 cut cannot install them. Mitigation: the refuse-and-explain message names the required CLI version. Adopters on older CLI versions who do not need adapter selection (Claude Code users on default behaviour) can stay on the older CLI and install older versions of the four packs — but new pack versions ship under v0.6 and are not backportable. The bump is also small in surface area (one new field, one new validator branch) compared to the v0.2 / v0.3 bumps.

- **First v0.6 pack is the integration test.** Like RFC-0004 was for user scope and RFC-0005 was for Kiro user-scope hooks, this RFC's contract bump has no production consumer until the four shipped user-scope packs bump and declare `allowed-adapters`. The integration test runs against fixture `~/.kiro/`, `~/.claude/`, and `~/.agents/skills/` trees in the implementation spec; production exposure is the first Kiro or Codex adopter installing `atlassian` at user scope post-merge. The first real-adopter transcripts close documented gaps, not open them — but they do expose whatever environment-specific failure modes exist (locked `~/.kiro/`, Windows path handling for `~/.kiro/skills/`, Kiro IDE running while the install writes; for Codex, the `~/.agents/skills/` tree's interaction with whatever else writes there, since `.agents/` is also where Codex's plugins marketplace lives).

- **Builds on RFC-0009.** The codex `direct-directory` projection at `.agents/skills/` (RFC-0009, Accepted 2026-05-25, commit `49061e6`) is the live adapter-contract entry this RFC's `[adapter.codex.scope]` table extends. No standalone sequencing dependency remains.

- **The multi-IDE adopter needs to know about `--adapter`.** An adopter with `~/.claude/` already on disk (anyone who has ever used Claude Code) running `agentbundle install --pack atlassian --scope user .` resolves to Claude Code by probe order, regardless of whether they're actually trying to install into Kiro or Codex. The `--adapter` flag (§ *CLI surface*) is the documented escape valve, but adopters need to know it exists. The `installed: ... via claude-code` print line names which adapter the resolver picked but does not surface the flag's existence. **Mitigation:** the README install section and the per-adapter how-to guides name `--adapter` explicitly in their worked examples; the install-time print line is candidate for a one-line `(other declared adapters: kiro, codex; use --adapter to override)` suffix when `allowed-adapters` has more than one matching entry and `--adapter` was not passed. The implementation spec freezes whether the suffix ships in v1 or stays prose-only.

- **Two heuristics stay alive for legacy packs.** `_resolve_user_scope_target_adapter` (install.py:1249) and `_kiro_target_adapters` (validate.py:351) keep their pre-RFC behaviour for `< 0.6` packs. The repo carries both a declarative and a heuristic resolver indefinitely — `< 0.6` packs never go away (RFC-0004 set the same precedent for `< 0.2`). Mitigation: code paths are clearly versioned; the docstring TODO is rewritten to point at the v0.6 path. Deleting the heuristic earns its own future RFC once no live pack declares `< 0.6`.

- **Out-of-tree packs need to know about the change.** A third-party catalogue publishing user-scope packs under v0.6 must declare `allowed-adapters`; an out-of-tree pack at an earlier contract version continues to work via the heuristic. The migration note (see § *Follow-on artifacts*) covers the upgrade; the schema's refuse-and-explain message names the field by full path.

- **v0.6 pack with `default-scope = "user"` but omitted `allowed-adapters` falls through to the legacy heuristic.** The optional-field shape (chosen for backward-compatibility) means a v0.6 pack that *intends* user-scope use but forgets to declare `allowed-adapters` re-introduces the AC25 corner case (Copilot-only pack with hooks, no agents → silent `claude-code` resolution). The four shipped user-scope packs declare the field explicitly; third-party packs may not. **Mitigation:** the `v05-to-v06-pack-upgrade.md` how-to recommends declaring `allowed-adapters` whenever `default-scope = "user"` is set; the `agentbundle validate` warning surface (deferred per § *Drawbacks* "ignored on repo-only packs" predecessor) could escalate to a Warning here in a future minor bump. Not strict-refusal in v1 because that would break backward-compat for any v0.6 third-party pack that intentionally wants the heuristic.

- **Adapter set is read from `adapter.toml` at schema-validation time, not at install time.** See § *Schema validation — Publisher-vs-installer contract drift* for the rail and the install-time refuse-and-explain message; this Drawbacks bullet exists to surface the *cost*, not restate the mechanism. The cost is one additional refusal mode at install time that an adopter can hit on a previously-validated pack — small, but a real cliff if a future contract narrowing drops an adapter.

- **Reversal cost if RFC-0009 is later superseded.** RFC-0009 is Accepted (2026-05-25), so this is a hypothetical safety net. If a future RFC supersedes RFC-0009 and reverts the codex `direct-directory` projection mode, RFC-0011's codex paragraphs amend out: drop the `[adapter.codex.scope]` table from `adapter.toml`, remove the codex arm of `_resolve_user_scope_target_adapter` and the user-scope projection dispatch, narrow the schema's adapter enum to `{claude-code, kiro}`, and drop `"codex"` from each shipped user-scope pack's `allowed-adapters`. The flow-metrics three-adapter probe stays (correctness work independent of codex's user-scope governance). PR commit history is the executable trace; no separate inventory section needed.

## Prior art

**In repo:**

- [RFC-0004 § Per-pack default and allowance](0004-install-scope-per-pack.md#per-pack-default-and-allowance) — establishes `[pack.install]` as the declarative home for pack-author install constraints; pins the anti-silent-default rule this RFC follows for `allowed-adapters`.
- [RFC-0004 § Unresolved questions](0004-install-scope-per-pack.md#unresolved-questions) — explicitly asked: *"Should `[pack.install]` carry more fields than `default-scope` and `allowed-scopes`?"* This RFC is one answer.
- [RFC-0005 § Adapter-level scope roots](0005-user-scope-hook-support.md#proposal) — adds Kiro's `[scope]` table with `~/.kiro/` user-root; without this RFC's declarative resolver, the table is reachable only by the agents-presence heuristic.
- [RFC-0007 § Pack shape](0007-user-scope-converter-pack.md#pack-shape) — first user-scope pack (`converters`) was the first that demonstrably could not reach Kiro at user scope via the heuristic (skills-only, no `.apm/agents/`).
- [RFC-0005](0005-user-scope-hook-support.md), [RFC-0008](0008-claude-plugins-install-route-parity.md), and [RFC-0010](0010-apm-install-route-parity.md) — the three intervening contract bumps (v0.2 → v0.3 → v0.4 → v0.5) that the four shipped user-scope packs skipped past at `[pack.adapter-contract] version = "0.2"` (their content doesn't touch hooks, claude-plugins, or APM install routes). This RFC bumps them straight to v0.6.
- [RFC-0009 § Adapter contract change](0009-codex-native-skills.md#adapter-contract-change) (Accepted 2026-05-25) — flipped Codex skill projection to `direct-directory` at `.agents/skills/`. This RFC builds on that flip: the `[adapter.codex.scope]` table this RFC adds reuses the same projection target, rerooted at `$HOME`.
- `_resolve_user_scope_target_adapter` (install.py:1249) and `_kiro_target_adapters` (validate.py:351) — sibling heuristics the v0.6 path replaces; both keep their pre-RFC behaviour for legacy packs.
- `feedback_pressure_test_before_adding` — the four-question test the user-task framing invokes; applied to both candidate shapes in § *Alternatives considered* items 2 and 3.

**External:**

- [PEP 621 — Declaring project metadata](https://peps.python.org/pep-0621/) — `requires-python` is purely declarative; no install-time `--python` override. Authoritative precedent for declarative-only when the publisher has the information.
- [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html) — packages declare named features; unknown features are refused at parse time. Schema-validated enum derived from the project itself — same shape as this RFC's `adapter.toml`-derived enum.
- [Cargo `--target` + `[target.'cfg(...)'.dependencies]`](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#platform-specific-dependencies) — hybrid declarative + imperative, but the imperative half exists because the *machine* (CPU architecture) has authoritative information the publisher lacks. For IDE adapters, the adopter's filesystem provides that signal already, justifying the asymmetry: declarative-only here is not "we skipped half the pattern," it's "the imperative half was never load-bearing."
- [npm `engines`](https://docs.npmjs.com/cli/v10/configuring-npm/package-json#engines) — declares supported Node/npm versions; soft warning by default, hard refusal with `engineStrict`. No `--node` override. Precedent for the soft/hard split (we land hard; soft can wait for a documented use).
- [Docker manifest lists / `--platform`](https://docs.docker.com/build/building/multi-platform/) — closest hybrid analogue; client passes `--platform` when multiple match. Different problem: image runtime is a CPU/OS pair the publisher cannot detect; IDE adapter is a filesystem signal we *can* detect. Cited for why the analogy fails, not for why it applies.
- [Homebrew bottle DSL](https://docs.brew.sh/Bottles) — formulas declare supported macOS versions; installer picks. Pure declarative, no override flag in the user-facing CLI. Strong precedent for "publisher declares, installer picks."
- [Codex Skills documentation](https://developers.openai.com/codex/skills) — pins `$HOME/.agents/skills` as the user-level location ("any skills checked into the user's personal folder. Use to curate skills relevant to a user that apply to any repository the user may work in"), with project-level locations at `$CWD/.agents/skills`, `$CWD/../.agents/skills`, and `$REPO_ROOT/.agents/skills`. The `[adapter.codex.scope]` table in this RFC consumes that pin directly.
- [Codex Plugins documentation](https://developers.openai.com/codex/plugins/build) — separate surface; pins `~/.codex/plugins/cache/$MARKETPLACE/$PLUGIN/$VERSION/` for installed plugins and `~/.agents/plugins/marketplace.json` for the personal marketplace catalogue. Cited here as the shape a sibling RFC (codex-plugins-install-route-parity) will consume; out of scope for this RFC per § *What this RFC does NOT do*.

No external precedent found for an imperative-only adapter override without a corresponding declarative manifest — every comparable ecosystem either pairs the flag with a manifest or omits the flag entirely. § *Alternatives considered* item 2 names that absence as supporting evidence.

## Unresolved questions

- **Should the `installed: ... via <adapter>` print line surface the other eligible adapters?** When `allowed-adapters` has more than one matching CLI home and `--adapter` was not passed, the resolver picks one silently in declared order. A `(other declared adapters: ...; use --adapter to override)` suffix would make the alternatives visible. Author's lean: **yes — the suffix ships in v1.** It's two lines of code, the cost is stderr verbosity for an audience that has explicitly opted into multi-IDE complexity. The implementation spec freezes the exact wording.
- **What happens when none of `~/.claude/`, `~/.kiro/`, or `~/.agents/skills/` exists?** Author's lean: **create `allowed-adapters[0]`'s root and proceed.** Same shape as Claude Code's greenfield handling today (`~/.claude/skills/` is created on first install). The first-listed adapter becomes the implicit default for fresh-machine adopters, which gives pack authors a meaningful ordering choice. The implementation spec pins a Tests entry for the three-way greenfield case.
- **Does the `~/.codex/` probe signal hold for skills-only Codex adopters?** Author's lean: **probe both `~/.codex/` and `~/.agents/skills/` (OR-condition) until the upstream behaviour is pinned.** The upstream Codex docs name `~/.agents/skills/` as the skills home and `~/.codex/plugins/cache/` as the plugins cache, but do not pin whether the Codex CLI creates `~/.codex/` on a skills-only first run. If empirical testing shows `~/.codex/` is plugins-only, the OR-probe collapses to `~/.agents/skills/` alone (which leaves the fresh-Codex-skills-adopter case for the implicit greenfield default). The implementation spec adds a test against a fixture `$HOME` with only `~/.agents/skills/` populated, plus one with only `~/.codex/` populated, plus one with both.
- **Does the schema validator's enum hydration belong in `pack.schema.json` or in `agentbundle validate`?**  Author's lean: **in the validator** (Python code reads the contract; the JSON schema's `enum` is a documentation hint, not the load-bearing rule). Pure JSON schema can't express "enum derived from another file"; the validator already runs adapter-aware rails (RFC-0004's marker grep, RFC-0005's hook-wiring checks). Keeping the rule in code is the lower-friction shape.
- **Should the migration note for third-party pack authors live in the same how-to as the v0.1 → v0.2 upgrade?** Author's lean: **separate how-to.** The v0.1 → v0.2 guide is structured around the contract bump *and* the new `[pack.install]` table; this RFC's v0.5 → v0.6 upgrade is a one-field add against an existing table, much smaller scope. A new `docs/guides/how-to/v05-to-v06-pack-upgrade.md` keeps the cross-bump diff legible and avoids overloading the older guide.
- **Should this RFC absorb RFC-0009 outright?** Author's lean: **no — sequence, don't bundle.** RFC-0009 carries its own load-bearing decisions (orphan-skill cleanup policy, same-name-skill collision rule, legacy AGENTS.md managed-block strip, retained-vs-removed test inventory across two test roots) that have nothing to do with adapter resolution at user scope. Bundling would make this RFC a 600-line decision artifact instead of a focused one. The hard `Depends on:` declaration and the implementation-spec task ordering are sufficient to keep the work sequenced without conflating the two decision sets.

## Follow-on artifacts

On acceptance — **single PR per RFC-0004's spec-amendment-atomicity precedent** ([RFC-0004 Drawbacks line 547](0004-install-scope-per-pack.md#drawbacks)). The CLI changes, schema changes, contract bump, and pack-toml updates ship together so a partially-landed RFC does not leave the CLI in an incoherent state.

- **Spec:** `docs/specs/pack-allowed-adapters/spec.md` (via `new-spec`) — defines the work as a sequence of plan tasks. Acceptance Criteria cover: the v0.5 → v0.6 contract bump in `_data/adapter.toml` (including the new `[adapter.codex.scope]` table with `user = "~"`, `allowed-prefixes.user = [".agents/skills/", ".agentbundle/"]`); the `allowed-adapters` schema in `pack.schema.json` with `adapter.toml`-derived enum (field optional; default-to-all when omitted); the four-step dispatch in `_resolve_user_scope_target_adapter` (flag → contract gate → CLI-home probe → greenfield-constant fallback); the parallel dispatch in `_kiro_target_adapters`; the user-scope projection dispatch at install.py:1170-1178 gaining a third arm for `codex.project`; the `--adapter` argparse entry on `install` (no repo-scope projection filter — see § *Repo-scope projection* erratum); the `DEFAULT_USER_SCOPE_ADAPTER` module constant at `agentbundle/scope.py`; the four shipped user-scope packs' `[pack.adapter-contract] version` bump (0.2 → 0.6) and `allowed-adapters = ["claude-code", "kiro", "codex"]` declaration; the install-time print `installed: <pack> @ <scope> via <adapter>` and its multi-eligible suffix; the schema refuse-and-explain messages for unknown adapter, non-user-scope-adapter-in-user-scope-pack, `--adapter`-not-in-allowed-adapters, `--adapter`-at-repo-scope; the install-time publisher-vs-installer version-skew refuse-and-explain message; and the integration test matrix that installs each of the four packs against fixture `~/.claude/`, `~/.kiro/`, `~/.codex/`, and `~/.agents/skills/` trees (greenfield, single-IDE, two-of-three combinations, all-three, plus the `--adapter <name>` override). **Atlassian portability fix landed alongside this RFC.** Adversarial review surfaced that `discover_skill_path` in `packs/atlassian/.apm/skills/flow-metrics/scripts/flow_metrics/upstream.py` hardcoded `~/.claude/skills/<name>/` and `<cwd>/.claude/skills/<name>/` as the user-scope and project-scope sibling-skill probe candidates — an atlassian install at user scope under Kiro or Codex would have silently failed at runtime when flow-metrics tried to resolve `jira` or `jira-align`. **Fixed in this RFC's branch** (commit on `eugenelim/pack-allowed-adapters`): user-scope and project-scope probes now walk all three user-scope-capable adapter directories (`.claude/`, `.kiro/`, `.agents/`) in declared order, with priority-2 sibling lookup still winning when flow-metrics and its sibling skill are co-installed under the same root. The `config.py` docstring example updated alongside. Pinned in this PR by `packages/agentbundle/tests/unit/test_flow_metrics_upstream_probe.py` — 8 parametrized cases covering all three adapter dirs at user-scope, all three at project-scope, env-override precedence, and the all-miss error case. `pytest` passes locally. The implementation spec inherits this test; no new module needed. **The test surface spans two test roots** per the repo's existing convention — `packages/agentbundle/tests/` (CLI / resolver / install / upgrade integration) and `packages/agentbundle/agentbundle/build/tests/` (contract / schema / adapter-projection). The implementation spec splits its Tests entries accordingly.

- **ADR:** *Adapter selection at user scope is declarative+imperative — per-pack `allowed-adapters` declares the supported set; the adopter's `--adapter` flag picks among them at install time. A module-level constant supplies the greenfield fallback. Codex user-scope skills land in `~/.agents/skills/` per the upstream Codex skills documentation.* Records the rejection of § *Alternatives considered* items 4, 5, 7, 8, 9, 10 and the adoption of items 2/3 (combined) and 6.

- **CLI changes** (inside the implementation spec, not a separate artifact): `_resolve_user_scope_target_adapter` rewrite (install.py:1249 — four-step lookup with `--adapter` flag, contract-version gate, three-arm CLI-home probe, and module-constant greenfield fallback); `_kiro_target_adapters` literal-`!= "0.3"`-gate widening + v0.6 early-return (validate.py:351); user-scope projection dispatch at install.py:1170-1178 gains a `codex.project` branch; install-time print line with optional `(other declared adapters: ...; use --adapter to override)` suffix; refuse-and-explain on schema violations and adapter-vs-allowed-adapters mismatches. **No repo-scope projection filter** — per § *Repo-scope projection* erratum, `allowed-adapters` is user-scope-only. The argparse setup at `cli.py:199-229` gains `--adapter` (choices: every shipped adapter from the live contract; user-scope-capability check moves to the install handler; bound to `--scope user`). A new module-level constant `DEFAULT_USER_SCOPE_ADAPTER` lands at `packages/agentbundle/agentbundle/scope.py` (default value: `"claude-code"`).

- **Pack updates** (same PR): four shipped user-scope packs (`atlassian`, `figma`, `converters`, `contracts`) bump `[pack.adapter-contract] version = "0.6"` and add `allowed-adapters = ["claude-code", "kiro", "codex"]`. Repo-only packs are unchanged.

- **README updates** (file: `README.md`):
  - The `Where primitives land` table at `README.md` § *Where primitives land* is the **single canonical** source for adapter landing paths (per memory rule `feedback_writing_style`). Refreshes the Codex row to the post-RFC-0009 `.agents/skills/` shape and notes user-scope landing paths for the three user-scope-capable adapters.
  - Each user-scope-capable pack's row in the `Packs` table links into the `Where primitives land` table rather than re-listing the landing paths inline.
  - The `Install` section's `Where to run these` paragraph picks up a one-line note about user-scope adapter resolution and links to the relevant how-to.

- **How-to guides** (one per non-Claude-Code adapter at user scope):
  - `docs/guides/how-to/install-user-scope-pack-into-kiro.md` — Kiro adopter's install path: prerequisites (`~/.kiro/` exists), the `agentbundle install --pack <name> --scope user .` invocation, the `installed: ... via kiro` confirmation line, upgrade/uninstall verbs.
  - `docs/guides/how-to/install-user-scope-pack-into-codex.md` — Codex adopter's install path: prerequisites (Codex CLI with skills support, which requires RFC-0009's landing), the same invocation, the `installed: ... via codex` confirmation line, the `~/.agents/skills/` discovery model, the interaction with `~/.agents/plugins/marketplace.json` (skills and plugins share the `.agents/` parent dir but live in disjoint subtrees), upgrade/uninstall verbs.

  Both cross-linked from the README install section.

- **Author docs:** the `add-credentialed-skill` skill body and `docs/specs/skill-secrets/spec.md` each gain one paragraph: *"If your pack's content is portable across IDEs (skills-only, no IDE-specific agent shape), list every adapter in `allowed-adapters` that supports user scope. The two credentialed packs in this catalogue (`atlassian`, `figma`) list `claude-code`, `kiro`, and `codex` because their skills are pure text + Python and travel cleanly across all three adapters' user-scope skill directories."* No change to credential loading (skill-secrets AC3 untouched).

- **Migration note for third-party pack authors:** `docs/guides/how-to/v05-to-v06-pack-upgrade.md` — covers the `[pack.adapter-contract] version` bump, the `allowed-adapters` field shape, the three currently-admitted adapter values (`claude-code`, `kiro`, `codex`), the schema's refuse-and-explain messages, and the legacy path for older packs.

- **`docs/CONVENTIONS.md`** — no edit required. The pack source-of-truth section already covers the `[pack.install]` table at the right granularity; `allowed-adapters` slots in without a section addition.

- **`docs/ROADMAP.md`** — entry added under "user-scope": *"`allowed-adapters` landed — Kiro and Codex user-scope installs now exercise the integrated path; next: codex-plugins install-route parity (sibling RFC, not yet opened; will be modeled on RFC-0008)."*

- **Sibling RFC (not gated on this RFC's acceptance):** *codex-plugins-install-route-parity* — adds `codex-plugins` to `[adapter.codex.install-routes]`, lands per-pack `dist/codex-plugins/<pack>/.codex-plugin/plugin.json`, aggregates a marketplace at `dist/codex-plugins/marketplace.json`, wires the install→adapt chain via a per-pack `SessionStart`-equivalent writer. Modeled on [RFC-0008](0008-claude-plugins-install-route-parity.md) and [RFC-0010](0010-apm-install-route-parity.md); load-bearing decisions to make in that RFC's own research phase include Codex's `interface` field semantics on `plugin.json`, the marketplace-catalogue location split (`~/.agents/plugins/marketplace.json` vs `~/.codex/plugins/cache/`), and whether the existing `claude-plugins` SessionStart pattern transfers verbatim or needs a Codex-specific lifecycle hook.
