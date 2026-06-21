# RFC-0022: Split `kiro` adapter into `kiro-ide` and `kiro-cli`

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-01
- **Date closed:** 2026-06-01
- **Related:**
  - [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) — establishes the adapter spec + build pipeline
  - [RFC-0005](0005-user-scope-hook-support.md) — user-scope hook support; **this RFC amends it**
  - [RFC-0009](0009-codex-native-skills.md) — precedent for adapter migration
  - [RFC-0011](0011-pack-allowed-adapters.md) — `allowed-adapters`; packs declare `"kiro"`
  - [RFC-0012](0012-repo-scope-per-adapter-projection.md) — per-adapter projection
  - Spec: `docs/specs/distribution-adapters/` — `distribution-adapters` spec corrected here
  - Spec: `docs/specs/kiro-ide-hook/` — `kiro-ide-hook` activation
  - Spec: `docs/specs/agent-spec-cli/` — v0.4 `kiro-ide-hook` section corrected here

---

## The ask

**Recommendation (BLUF):** Split the single `kiro` adapter into two targets —
`kiro-ide` (the new default, targeting the Kiro VS Code-fork IDE) and `kiro-cli`
(targeting the `kiro` terminal binary) — retaining `kiro` as a non-expiring
deprecated alias for `kiro-ide`. Bump the contract from v0.8 to v0.9.

**Why now (SCQA):** Kiro is one vendor but two distinct surfaces: the IDE extension
(`kiro.kiro-agent`, verified against the bundled `extension.js`) and the CLI binary
(documented at `kiro.dev/docs/cli/`). *Complication:* the two surfaces differ on
agent format, tool vocabulary, and hook mechanism — and the current `kiro` adapter
was authored against the CLI, projecting hook-wiring that the IDE's live loader
silently rejects (it drops any agent carrying a CLI-only `hooks` key entirely). The
just-merged PR #221 fixed tool-name mapping; hook format and the adapter split are
the remaining structural bugs. *Question:* how do we ship both surfaces without
breaking existing packs or adopter invocations?

**Decisions requested:**

1. **Split mechanism + `kiro` name.** Adopt two canonical adapters (`kiro-ide` /
   `kiro-cli`) with `kiro` as a deprecated alias → `kiro-ide`, no removal timeline.
   _Recommended: yes._ Decide-by: RFC acceptance.

2. **Agent file format per surface.** `kiro-ide` projects `.md` (frontmatter + body
   as `prompt`); `kiro-cli` projects `.json`. _Recommended: yes._ Decide-by: RFC
   acceptance.

3. **Tool vocabulary per surface.** Two separate frontmatter-mapping tables:
   `kiro-agent-frontmatter-v0.9` (ide, existing tool-id map from PR #221) and a new
   `kiro-cli-agent-frontmatter-v1.0` (cli, maps to CLI short names). _Recommended:
   yes._ Decide-by: RFC acceptance.

4. **Hook mechanism per surface.** `kiro-ide`: activate the dormant `kiro-ide-hook`
   primitive (`.kiro/hooks/<pack>/<name>.kiro.hook`) and drop `hook-wiring`
   (merge-into-agent-json) — a CLI-only field fatal to the IDE loader. `kiro-cli`:
   keep `hook-wiring` (merge-into-agent-json) and `hook-body`. _Recommended: yes._
   Decide-by: RFC acceptance.

5. **Model ids.** Keep existing values (`claude-opus-4.6` / `claude-sonnet-4.5` /
   `claude-haiku-4.5`) in both mapping tables; manually maintained. _Recommended:
   yes._ Decide-by: RFC acceptance.

6. **Errata + spec corrections.** Record errata on RFC-0005 (single-adapter
   assumption; hook-wiring CLI-only) and corrections to `distribution-adapters` and
   `agent-spec-cli` specs. _Recommended: yes._ Decide-by: RFC acceptance.

---

## Problem & goals

### Problem

The `kiro` adapter was authored against the Kiro CLI documentation (verified:
docstrings and the `distribution-adapters` spec footnote at line 216 cite
`kiro.dev/docs/cli/custom-agents/configuration-reference/`). But adopters using the
Kiro IDE extension hit two silent breakages:

**Tool names resolve to nothing.** The IDE's `tools` filter (`p16`/`Q7` in
`extension.js`) matches entries by tool **id** (`read_file`, `grep_search`, …) or
**tag** (`read`, `write`, …), never by Claude Code names (`Read`, `Grep`, `Bash`).
Our agents projected with `"tools": ["Read", "Grep", "Glob", "Bash"]`, so every
agent landed with an empty tool set. Fixed in PR #221; included here for context
on why the split is needed.

**Hook-wiring drops IDE agents entirely.** The IDE's live loader
(`CustomAgentFileLoader.loadCustomAgentFile`, `extension.js` line ~740278) checks
the raw file for any of the CLI-only fields `{mcpServers, allowedTools,
toolsSettings, hooks}`. If any is present, it logs:

> `"[CustomAgentFileLoader] Agent "…" not loaded: contains unsupported fields (hooks).
> These fields are only supported in the CLI."`

…and returns without registering the agent. Our `hook-wiring` primitive merges a
`hooks` key into the agent JSON — so the moment a pack ships a hook-wiring TOML
targeting a Kiro agent, that agent **silently disappears in the IDE**. This is
latent today (no shipping pack attaches hook-wiring to a Kiro agent), but will
activate as soon as one does.

**IDE event hooks are inert.** The `kiro-ide-hook` primitive has a complete
implementation (projector `kiro_ide_hook.py`, schema extension,
`validate`-time rail, full test suite — shipped in PR #99). But it was never
declared in the adapter contract, so it produces no output. IDE adopters get no
event hooks at all.

**Cascading governance drift.** The above gaps left the `distribution-adapters`
spec (line 214–217) with a footnote claiming the CLI configuration reference
"confirming agents are JSON" — but the IDE loads **both** `.md` and `.json`
(verified in `extension.js` `p16`). The `kiro-ide-hook` and `agent-spec-cli` specs
are marked `Shipped` for the v0.4 contract bump, but the contract never declared the
primitive — the "Shipped" framing overstates the delivered state.

### Goals

- Adopt a `kiro-ide` adapter that works correctly in the Kiro IDE: `.md` agents with
  body-as-prompt, tool ids matched by the IDE, and event hooks via `.kiro.hook` files.
- Adopt a `kiro-cli` adapter that works correctly in the Kiro CLI: `.json` agents
  with CLI short-name tool tokens, and lifecycle hooks via the `hooks` key inside
  the agent JSON.
- Retain `kiro` as a deprecated alias for `kiro-ide` with no removal timeline, so
  existing packs and adopter invocations keep working.
- Record errata and corrections against the governance docs whose claims this split
  supersedes.

### Non-goals

- **Changing skill/steering/MCP projection.** These are identical across IDE and CLI;
  the current `direct-directory → .kiro/skills/` projection is correct for both.
- **Removing the `kiro` alias.** No removal timeline is set. Future maintainers may
  decide when to drop it; this RFC does not bind them.
- **Verifying Kiro IDE model ids against the binary.** Model ids are manually
  maintained. The current values (`claude-opus-4.6` / `claude-sonnet-4.5` /
  `claude-haiku-4.5`) carry forward.
- **Adding new packs that consume the new adapters.** The split is infrastructure;
  the first consumer pack is a follow-on.

---

## Proposal

### 1. Contract bump: v0.8 → v0.9

The `[contract]` block in `adapter.toml` (and its byte-identical `_data/` copy)
bumps from `0.8` to `0.9`. The contract version test in `test_contract.py` updates
to assert `"0.9"`.

### 2. New `[adapter.kiro-ide]` and `[adapter.kiro-cli]` blocks

Both new adapter blocks follow the same projection-table structure as the existing
`[adapter.kiro]` block. `kiro` is retained as a deprecated alias:

```toml
# kiro is a deprecated alias for kiro-ide. No removal timeline.
# Packs declaring allowed-adapters = ["kiro"] continue to work; the resolver
# maps "kiro" → "kiro-ide" and emits a build-time deprecation warning.
```

The Python adapter registry gains `kiro_ide` and `kiro_cli` modules; `kiro` maps
to `kiro_ide.project` (the alias). `cli.py`'s hardcoded `"claude-code, kiro, copilot, codex"` help-text string is
updated to name all five adapters with the deprecation note (see T7).

### 3. `kiro-ide` adapter

**Agent (`.md`, frontmatter + body-as-prompt).** The adapter projects `.apm/agents/`
sources to `.kiro/agents/<name>.md`. The pack-side format stays `.md`; the IDE
projection is also `.md` (body becomes the agent's system prompt — native to the
IDE's `J6` markdown parser). No CLI-only fields are emitted (`hooks`, `allowedTools`,
`toolsSettings`, `mcpServers` never appear). Frontmatter mapping table:
`kiro-ide-agent-frontmatter-v0.9` (the existing `kiro-agent-frontmatter-v0.9`
mapping, renamed for clarity; tool-id `values` map from PR #221 kept as-is).

**Hook-wiring: dropped.** The `hook-wiring` primitive is `mode = "dropped"` for
`kiro-ide`. Rationale: the IDE loader rejects any agent carrying a `hooks` key.
Lifecycle hooks for the IDE surface are covered by `kiro-ide-hook` below.

**kiro-ide-hook: activated (repo-scope only, gated on Q6).** The existing `kiro-ide-hook`
primitive is added to the `[adapter.kiro-ide]` block at repo scope only:

```toml
[adapter.kiro-ide.projections.kiro-ide-hook]
mode = "direct-file"
target.repo = ".kiro/hooks/<pack>/<name>.kiro.hook"
# target.user intentionally omitted: ~/.kiro/hooks/ is not on Kiro's read
# path (kirodotdev/Kiro#5440 still open). User-scope lift tracks that issue
# per RFC-0005 Unresolved Q9.
on-conflict = "prompt-then-preserve"
ide-event-vocabulary = [
  # E3-verified list (extension.js IDEListenableEvent enum, 2026-06-01, closes Q11).
  # T2 updates the validate rail to match; T10 records Q11 closure in probes.md.
  "fileEdited", "fileCreated", "fileDeleted", "userTriggered",
  "promptSubmit", "agentStop", "preToolUse", "postToolUse",
  "preTaskExecution", "postTaskExecution", "sessionStart",
]
ide-action-vocabulary = ["askAgent", "runCommand"]
```

Pack-side source: `.apm/kiro-ide-hooks/<name>.kiro.hook`. The projector
(`kiro_ide_hook.py`), schema, and test suite already exist (PR #99); activation is
purely a contract declaration. **T1 (contract block) is gated on Q6** — the probe
(`docs/specs/kiro-ide-hook/probes.md`) must run and record its outcome before T1 is
committed. If Q6 lands "no-recursion," the `target.repo` path shape changes and
this section must be amended before the implementing PR merges.

**IDE event vocabulary** (from `extension.js` `IDEListenableEvent` enum, verified
2026-06-01 — supersedes RFC-0005's community-inferred "best-guess" list and the
probe-gated placeholder in `distribution-adapters/spec.md:749`):
`fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`,
`agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`,
`sessionStart`. Actions: `askAgent`, `runCommand`.

**Vocabulary transition note.** The shipped `kiro_ide_hook.py` validate rail and
`adapter.schema.json` still carry RFC-0005's inferred vocabulary (`fileSave`,
`fileEdit`, `manualTrigger` instead of the verified values). The implementing spec
task (T2, below) must update the validate rail and `ide-event-vocabulary` in the
contract block in the same PR as the activation, so packs built against the old
list are caught at validate time rather than silently projecting wrong hook files.

**hook-body, skill, command:** same as today (hook-body `direct-file` → `tools/hooks/`
at repo scope, `~/.kiro/hooks/<pack>/` at user scope; skill `direct-directory` →
`.kiro/skills/`; command `dropped`).

**Scope + allowed-prefixes** (spelled out explicitly — TOML blocks are independent,
not inherited):
```toml
[adapter.kiro-ide.scope]
repo = "."
user = "~"
allowed-prefixes.repo = [".kiro/", ".agentbundle/", "tools/hooks/"]
allowed-prefixes.user = [".kiro/", ".agentbundle/"]
```

### 4. `kiro-cli` adapter

**Agent (`.json`).** Projects `.apm/agents/<name>.md` → `.kiro/agents/<name>.json`
(same JSON-emission path as the current `kiro` adapter). Frontmatter mapping table:
`kiro-cli-agent-frontmatter-v1.0` — same structure as the ide mapping but `tools`
values map to **CLI short names**:

```toml
[frontmatter-mapping."kiro-cli-agent-frontmatter-v1.0".tools]
normalize = "to-list"
# CLI canonical names (kiro.dev/docs/cli/reference/built-in-tools/).
# web_fetch and web_search are the CLI short names; the CLI has no "web"
# aggregate tag — that exists on the IDE surface only.
values = { Read = "read", Grep = "grep", Glob = "glob", Edit = "write", Write = "write", MultiEdit = "write", Bash = "shell", WebFetch = "web_fetch", WebSearch = "web_search" }

[frontmatter-mapping."kiro-cli-agent-frontmatter-v1.0".model]
rename = "model"
values = { opus = "claude-opus-4.6", sonnet = "claude-sonnet-4.5", haiku = "claude-haiku-4.5" }
```

**hook-wiring:** kept, `mode = "merge-into-agent-json"`, vocabulary
`agentSpawn / userPromptSubmit / preToolUse / postToolUse / stop` (unchanged from
the current `kiro` adapter — this is the CLI's documented hook schema).

**kiro-ide-hook: dropped.** IDE event-hook files are not consumed by the CLI.

**hook-body, skill, command:** same projection as `kiro-ide` (hook-body
`direct-file` → `tools/hooks/` at repo scope, `~/.kiro/hooks/<pack>/` at user
scope; skill `direct-directory` → `.kiro/skills/`; command `dropped`).

**Scope + allowed-prefixes** (spelled out explicitly):
```toml
[adapter.kiro-cli.scope]
repo = "."
user = "~"
allowed-prefixes.repo = [".kiro/", ".agentbundle/", "tools/hooks/"]
allowed-prefixes.user = [".kiro/", ".agentbundle/"]
```

### 5. `kiro` deprecated alias

`kiro` is kept as a first-class entry in the adapter registry, delegating to
`kiro_ide.project`. The alias mechanism has two parts:

**Python registry** — `adapters/__init__.py` maps `"kiro"` → `kiro_ide.project`
alongside the canonical `"kiro-ide"` entry.

**Contract stub** — a minimal `[adapter.kiro]` block is retained in `adapter.toml`
so that `_shipped_for_cli` (hydrated from the contract's adapter key set) continues
to include `"kiro"`, and the `allowed-adapters` validator (`validate` time) keeps
accepting `"kiro"` in existing `pack.toml` files. Without the stub, `"kiro"` falls
out of the derived enum and every pack declaring `allowed-adapters = ["kiro"]`
breaks at `validate` time. The stub carries a comment marking it deprecated:

```toml
# kiro: deprecated alias for kiro-ide. No removal timeline.
# Kept so that packs declaring allowed-adapters = ["kiro"] continue to
# pass validate and resolve to kiro-ide at install time.
[adapter.kiro]
# All projections delegate to kiro-ide; no projection table needed here.
```

The resolver logs a deprecation warning when the alias is resolved:

> `"kiro: deprecated alias for kiro-ide; update allowed-adapters in pack.toml"`

No removal timeline. Existing `packs/*/pack.toml` files declaring
`allowed-adapters = ["claude-code", "kiro", "codex"]` continue to work unchanged.

### 6. RFC-0005 errata

The following errata are added to RFC-0005 § Errata (Approver-signed):

- **E1 — Single-adapter assumption.** RFC-0005 assumed a single `kiro` adapter
  covering both IDE and CLI. RFC-0022 supersedes this; `kiro` becomes a deprecated
  alias for `kiro-ide`.
- **E2 — `hook-wiring` is CLI-only for Kiro.** The `merge-into-agent-json` mode
  (§ "hook-wiring for Kiro at both scopes") produces the CLI-correct shape but is
  fatal to the IDE loader. It moves to `kiro-cli` only; `kiro-ide` drops it.
- **E3 — `kiro-ide-hook` event vocabulary and Q11 closure method.** RFC-0005
  § "Kiro IDE event hooks" described the vocabulary as a "best-guess subject to one
  fixture-based rewrite" (RFC-0005 line ~1810) and deferred pinning as Unresolved
  Q11 ("obtain at least one IDE-UI-authored `.kiro.hook` fixture"). The spec documents
  (`distribution-adapters/spec.md:749–760`) carried the
  vocabulary as `<probe-pinned per Q11>`. RFC-0022 closes Q11 via **static analysis
  of `extension.js`** (`IDEListenableEvent` enum, verified 2026-06-01) rather than
  an IDE-UI-authored fixture — a deliberate substitution of the verification method.
  No fixture is required under this closure. The authoritative vocabulary is:
  `fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`,
  `agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`,
  `sessionStart`. Actions: `askAgent` / `runCommand`. The shipped validate rail uses
  RFC-0005's earlier inferred list (`fileSave`, `fileEdit`, `manualTrigger`); the
  implementing spec updates both the rail and the contract `ide-event-vocabulary`
  array (T2); `probes.md` Q11 is updated to record the closure (T10).

### 7. Spec corrections

- **`distribution-adapters` spec, lines 214–218:** the footnote "RFC-0005 / T7
  introduced the JSON emission once Kiro published the custom-agents configuration
  reference *confirming agents are JSON*" is incorrect. The IDE loads **both** `.md`
  and `.json` (verified in `extension.js` `p16`, `loadCustomAgentFile`). Correct to:
  "`kiro-ide` projects `.md`; `kiro-cli` projects `.json`; the IDE accepts both."
  The agent/hook-wiring rows in the primitive table update accordingly.
- **`kiro-ide-hook` spec + `agent-spec-cli` §v0.4:** the "Shipped" status correctly
  reflects that the code/schema/tests landed (PR #99). However the contract
  declaration was missing, leaving the primitive inert. Add a clarifying note:
  "Code shipped; contract activation deferred to RFC-0022."

---

## Options considered

*Axis: how to model the IDE/CLI divergence — MECE along the adapter-identity
dimension (one adapter, two adapters, or a profile flag within one adapter).*

| Option | Description | Trade-offs |
|---|---|---|
| **(A) Split — two adapters** ★ | `kiro-ide` + `kiro-cli`; `kiro` deprecated alias → `kiro-ide`. Recommended. | Clean separation; consistent with the one-adapter-per-target model used by `claude-code` / `copilot` / `codex`. Adding the 5th adapter is mechanically cheap (data-driven CLI choices, 2 registry entries, no self-host/marketplace blast radius). Packs with `allowed-adapters = ["kiro"]` work unchanged via the alias. |
| **(B) Profile flag** | Single `kiro` adapter; new `--surface ide\|cli` flag on `agentbundle install`. | Avoids a 5th adapter name; divergence lives in conditional code. But `--surface` isn't a concept elsewhere in the CLI (adapters *are* the surface), and `pack.toml` would need a new key to express per-surface default. Inconsistent with the one-adapter-one-target principle. Precedent: spec-kit uses per-format subclasses rather than a flag ([spec-kit multi-agent architecture](https://deepwiki.com/github/spec-kit/6.4-utility-scripts)). |
| **(C) kiro-ide only, no kiro-cli** | Retarget the existing `kiro` to the IDE; don't add a CLI target. | Simpler. But leaves CLI users with no supported path, and the hook-wiring primitive becomes entirely dead code. Rejected: we have adopters who use both; killing CLI support is a non-goal. |
| **(D) Do nothing** | Keep the current broken `kiro` adapter. | Every IDE adopter gets zero-tools agents and no event hooks. The latent hook-wiring bug will silently drop agents the moment any pack ships a wiring TOML. Cost compounds with each new Kiro pack. |

★ Option A was spiked against the codebase: the adapter registry is two name-keyed
dicts in `adapters/__init__.py`; `cli.py` derives `--adapter` choices from the live
contract (`_shipped_for_cli`); `SELF_HOST_ADAPTERS` excludes `kiro` already. Adding
`kiro-ide` and `kiro-cli` touches only the registry, the help-text string, and the
contract — no self-host, marketplace, or install-route blast radius.

---

## Risks & what would make this wrong

**Pre-mortem:**

- *Adopters who pinned `--adapter kiro` in scripts break.* Mitigated by the
  deprecated alias: `kiro` keeps working, the resolver warns. No removal timeline.
- *Packs that declare `allowed-adapters = ["kiro"]` resolve to the wrong surface.*
  The alias maps `kiro` → `kiro-ide`. A CLI-only pack should update to
  `["kiro-cli"]`. The build-time warning surfaces this.
- *The `kiro-ide-hook` contract activation introduces a new projection path that
  fails on edge cases.* The projector, schema, and test suite already shipped in
  PR #99; activation is a contract declaration only. The kiro-ide-hook test suite
  (`test_kiro_ide_hook_{rail,schema,projection,e2e}`) already covers the projection.
- *Model ids (`claude-opus-4.6` etc.) are wrong for the IDE.* Acknowledged as
  manually maintained; both surfaces carry the same values. Worst case: the IDE
  silently ignores an unrecognised value and falls back to its default model.
- *Packs built against the shipped (inferred) `ide-event-vocabulary` pass `validate`
  today but would fail against the corrected list.* The shipping vocabulary uses
  `fileSave`/`fileEdit`/`manualTrigger`; the verified list uses `fileEdited`/
  `fileDeleted`/`userTriggered`/`sessionStart`. Mitigation: T2 and T9 must co-land
  (vocabulary update + RFC-0005 errata in the same PR); the backlog shows no shipping
  pack yet sources `.apm/kiro-ide-hooks/`, so there are no packs to break.

**Key assumptions (falsifiable):**

1. The IDE's `CustomAgentFileLoader` path is the sole live agent-registration path.
   If another loader is added without the CLI-only-field check, `hook-wiring` would
   no longer be fatal. (Verified at `extension.js` line ~740278 as of 2026-06-01;
   a future IDE update could change this.)
2. `kiro-ide` agents in `.md` format work as intended. The IDE `p16` scanner
   accepts `*.md` and `*.json`; the `J6` markdown parser uses `gray-matter` and
   passes `body` as `prompt`. Verified in `extension.js`; assumed stable.
3. The Kiro CLI continues to accept `.json` agents with a `hooks` key. The CLI docs
   (`kiro.dev/docs/cli/custom-agents/configuration-reference/`) confirm this as of
   2026-06-01.
4. RFC-0005 Unresolved Q6 (does the IDE recurse into `.kiro/hooks/<subdir>/`?) resolves
   to the "yes-recursion" quadrant, validating the `<pack>/<name>.kiro.hook` path shape.
   The Q6 probe (`docs/specs/kiro-ide-hook/probes.md`) is "Not yet run." The implementing
   spec (T2) must run Q6 before the `kiro-ide-hook` block is merged into the contract;
   if Q6 lands "no-recursion," the target path flattens and this RFC's path shape is
   wrong. *Falsification:* the flat `.kiro/hooks/<pack>-<name>.kiro.hook` alternative
   (RFC-0005 `no-recursion × yes-extension-filter` quadrant).

**Drawbacks:**

- Five adapter names instead of four. Adopter cognitive load increases marginally.
- The deprecated `kiro` alias is maintenance surface — someone must update the
  help-text if the alias ever diverges from `kiro-ide` behaviour.
- Two frontmatter-mapping tables (`kiro-ide-agent-frontmatter-v0.9` /
  `kiro-cli-agent-frontmatter-v1.0`) whose `model` values must be kept in sync
  manually; there is no automated cross-check.

---

## Evidence & prior art

**Spike result.** The registry, CLI choices, and self-host allow-list were examined
against the actual adapter-registration call sites in `adapters/__init__.py` and
`self_host.py`. Adding a 5th adapter is data-driven end to end; the only hardcoded
string is the `cli.py:198/296` help text. `SELF_HOST_ADAPTERS` already excludes
`kiro`; the marketplace file (`/.claude-plugin/marketplace.json`) is pack-keyed, not
adapter-keyed. Blast radius: **two Python files + the contract**, no infrastructure.

**Repo precedent.**
- RFC-0009 — migrated the Codex adapter from one mode (`managed-block AGENTS.md`) to
  another (`direct-directory .agents/skills/`) in a single bump. Same pattern as
  extracting `kiro-cli` from the current `kiro`.
- RFC-0011 — added `allowed-adapters` to `pack.toml`; the existing 7+ packs
  declaring `"kiro"` will keep working via the alias without modification.
- RFC-0005 § "Kiro IDE event hooks" — designed the `kiro-ide-hook` primitive
  correctly; this RFC completes its activation.

**External prior art.**
- [spec-kit multi-agent architecture](https://deepwiki.com/github/spec-kit/6.4-utility-scripts) — uses per-format adapter subclasses (`MarkdownIntegration` / `TomlIntegration` / `SkillsIntegration`) to project one source into different target formats. Validates option A's per-adapter split over a runtime flag.
- [Terraform SDKv2 deprecation best practices](https://developer.hashicorp.com/terraform/plugin/sdkv2/best-practices/deprecations) — keep the deprecated name working (warn-not-fail); remove only at a major version boundary. Supports the no-removal-timeline policy for the `kiro` alias: adopt the warn-not-fail pattern now, decide the major-version removal later.
- [Symfony 4.3 service-alias deprecation](https://symfony.com/blog/new-in-symfony-4-3-deprecating-service-aliases) — deprecated aliases emit a warning on use; the old name resolves to the new. Same pattern as the `kiro` → `kiro-ide` alias here.

---

## Open questions

1. **User-scope `kiro-ide-hook` lift.** When does kirodotdev/Kiro#5440 close and
   `~/.kiro/hooks/` become a real read path? Default: monitor the issue; lift
   user-scope via a point amendment to this RFC (no new RFC needed if no state-file
   shape change). Owner: eugenelim. Decide-by: when #5440 closes.

2. **`kiro` alias removal.** No removal timeline is set by this RFC. Future
   maintainers decide when (or whether) to drop it in a major contract version.
   Default: keep indefinitely until a second RFC proposes removal. Owner: eugenelim.

3. **E3 errata ordering.** Resolved: T9 (errata append) is a hard prerequisite for
   T2 (validate-rail update); both co-land in the implementing PR. No further decision
   needed. Owner: eugenelim. Decide-by: N/A (resolved by this RFC).

---

## Follow-on artifacts

- **ADR-NNNN** (assign number when RFC moves to Open): Record the decision to split
  `kiro` into `kiro-ide` and `kiro-cli` with `kiro` as a deprecated alias.
- **Spec: `docs/specs/kiro-adapter-split/`** — implementation spec covering:
  (T1) contract v0.9 bump + `kiro-ide` adapter block + `kiro-ide-hook` activation
      with E3 `ide-event-vocabulary` (Q6 probe must be recorded before T1 merges;
      see Key Assumption 4) + rename `kiro-agent-frontmatter-v0.9` →
      `kiro-ide-agent-frontmatter-v0.9` in the contract **and** in every reference
      inside `kiro.py` (the named string appears at multiple call sites).
      _Depends on: Q6 probe, T9._
  (T2) validate rail update: `ide-event-vocabulary` array in `kiro_ide_hook.py` /
      `scope_rails.py` → verified E3 list. **T9 is a hard prerequisite for T2.**
      _Depends on: T9._
  (T3) `kiro-cli` adapter block + `kiro-cli-agent-frontmatter-v1.0` mapping.
      _Depends on: none._
  (T4) `kiro` stub block + adapter registry (`kiro` → `kiro_ide.project`) +
      resolver deprecation warning. _Depends on: none._
  (T5) `distribution-adapters` spec corrections (agent row, hook-wiring row,
      "agents are JSON" footnote). _Depends on: none._
  (T6) `agent-spec-cli` §v0.4 clarification ("Code shipped; contract activation
      deferred to RFC-0022"). _Depends on: none._
  (T7) `cli.py` hardcoded `"claude-code, kiro, copilot, codex"` help-text string
      updated to name all five adapters with the deprecation note.
      _Depends on: none._
  (T8) all test-suite updates (test_adapter_kiro, test_contract, contract drift gate,
      kiro_ide_hook tests for new E3 vocabulary). _Depends on: T1, T2, T3, T4._
  (T9) **Hard prerequisite for T1 and T2.** Append RFC-0005 `## Errata` table
      (E1–E3) to `docs/rfc/0005-user-scope-hook-support.md`, Approver-signed.
      _Depends on: none._
  (T10) Update `docs/specs/kiro-ide-hook/probes.md` Q11 Outcome section: record
      closure method (static analysis of `extension.js` `IDEListenableEvent` enum,
      2026-06-01), verified vocabulary, and note that no IDE-UI-authored fixture
      is required under RFC-0022's substitution. _Depends on: none._
- **Convention change:** none (adapter naming is contract-level, not in
  `docs/CONVENTIONS.md`).

### RFC-0005 errata section (T9: append to that RFC when this is accepted)

T9 appends the following block to `docs/rfc/0005-user-scope-hook-support.md`.
Approver: eugenelim. Date: filled in at time of merge.

```markdown
## Errata

Corrections below are Approver-signed amendments. The RFC body above is preserved
unchanged; errata supersede where noted. (Approver: eugenelim, DATE_OF_MERGE.)

| ID | Introduced by | Date | Correction |
|----|--------------|------|------------|
| E1 | RFC-0022 | DATE_OF_MERGE | RFC-0005 assumed a single `kiro` adapter. Superseded: `kiro` is a deprecated alias for `kiro-ide`; `kiro-cli` is the separate CLI target. |
| E2 | RFC-0022 | DATE_OF_MERGE | `hook-wiring` (merge-into-agent-json) is CLI-only for Kiro. The IDE loader drops any agent carrying a `hooks` key. `hook-wiring` moves to `kiro-cli`; `kiro-ide` drops it in favour of the `kiro-ide-hook` primitive. |
| E3 | RFC-0022 | DATE_OF_MERGE | RFC-0005 described the IDE event vocabulary as a "best-guess" (Unresolved Q11); `distribution-adapters/spec.md:749` marked it `<probe-pinned per Q11>`. RFC-0022 closes Q11 via static analysis of `extension.js` `IDEListenableEvent` enum (2026-06-01) — a deliberate substitution of RFC-0005's stated fixture-probe verification method. Authoritative vocabulary: `fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`, `agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`, `sessionStart`. Actions: `askAgent` / `runCommand`. Shipped validate rail (`fileSave`/`fileEdit`/`manualTrigger`) superseded; updates in T2. `probes.md` Q11 outcome recorded in T10. |
| E4 | RFC-0022 | DATE_OF_MERGE | The RFC specified kiro-cli and kiro-ide agent projection but omitted skill reachability for **custom** agents. On **both** targets, only the **default** agent auto-discovers `.kiro/skills/**/SKILL.md` and `~/.kiro/skills/**/SKILL.md`; a **custom** agent (`--agent <name>` on the CLI, a subagent in the IDE) loads **no** skills unless it declares them in its `resources` field via the `skill://` URI scheme (kiro #6887/#6888/#4993; verified against `kiro.dev/docs/cli/skills`, `…/custom-agents/configuration-reference`, and `kiro.dev/docs/skills` on 2026-06-19). Effect: every pack agent run via `--agent` (incl. headless `kiro --no-interactive --agent …`) or as an IDE subagent had zero skill awareness. Correction: **both** the kiro-cli and kiro-ide agent projections inject a fixed skill-resources glob for both install scopes via a new typed `inject-resources` projection-entry field (contract v0.15; `docs/specs/kiro-cli-agent-skill-resources`). CLI emits it into agent JSON; IDE emits it into the `.md` YAML frontmatter as a quoted, real-YAML-valid flow sequence (`resources` is a documented IDE agent field, so it does not trip the E2 silent-drop bug, which is for non-schema keys). Author-declared `resources` win; the deprecated `kiro` alias inherits the IDE behavior. This also sharpens RFC-0029's spike claim that "all adapters auto-discover skills" — true for **default** agents, not custom ones. |
```
