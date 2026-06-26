# RFC-0052: Shared-prefix-aware multi-adapter install

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:** 2026-06-25
- **Related:** [RFC-0012](0012-repo-scope-per-adapter-projection.md) (supersedes Alternative #7 — the rejected fan-out / one-install-one-adapter item), [RFC-0011](0011-pack-allowed-adapters.md), [RFC-0022](0022-kiro-adapter-split.md), [RFC-0009](0009-codex-native-skills.md) (codex's relied-on `.agents/skills/` home), [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md), [ADR-0013](../adr/0013-copilot-full-parity-user-scope-adapter.md) / [ADR-0015](../adr/0015-cursor-full-parity-distribution-adapter.md) / [ADR-0016](../adr/0016-gemini-cli-full-parity-adapter.md) (**skill-home decision superseded here** — see Proposal; agent/hook/command projection in each stands)

## The ask

- **Recommendation (BLUF):** Stop treating *the adapter* as the identity of an install. Make the install identity the **footprint** — the set of file paths a `(pack, adapter, scope)` install writes — and resolve "already installed" per-file by content (SHA), not by pack name. This lets the same pack coexist across adapters with disjoint footprints, co-own (within one pack, across its adapter rows) the files that genuinely share a path, and refuse only on a real content collision. Route every adapter that reads `.agents/skills/` (codex, cursor, gemini, copilot) to write skills there, so one copy serves the whole cohort — superseding the now-stale native-skill-home decision in ADR-0013/0015/0016.
- **Why now (SCQA):** *Situation* — one pack, one adapter per install; the state file records a single `adapter` per pack (RFC-0011/0012). *Complication* — installing `research` for `codex` after installing it for `claude-code` is refused with "already installed at user; use upgrade", even though the two write to entirely separate trees. The gate keys on pack name alone and is blind to the adapter; meanwhile `.agents/skills/` and `.kiro/skills/` are each read by several adapters, which the one-`adapter`-per-pack model cannot represent. *Question* — what is the right identity for an install, how should two installs that touch the same path behave, and should the adapters that all read `.agents/skills/` share one copy?
- **Decisions requested:**
  1. **Adopt footprint co-ownership as the install identity.** Recommended: yes — derive a file's owner-set from the installed rows' footprints; a file is removed only when its last owner is uninstalled. Decide-by 2026-06-29; default = adopt.
  2. **Add a `shared` prefix class to the adapter contract.** Recommended: yes — `.agents/skills/` (cohort {codex, cursor, gemini, copilot}) and `.kiro/skills/` (cohort {kiro-ide, kiro-cli}); everything else stays `private`. Decide-by 2026-06-29; default = adopt.
  3. **Route cohort skills to the shared prefix (Option A), superseding ADR-0013/0015/0016's skill-home decision.** Recommended: yes — cursor/gemini/copilot skills move from their native dirs to `.agents/skills/`, grounded in those tools' current docs (Gemini now *prefers* the alias). Their agent/hook/command projection stays native. Decide-by 2026-06-29. **This one supersedes three Accepted ADRs, so it needs an explicit Approver yes — it does not adopt by silence** (unlike Decisions 1–2, 4–8).
  4. **State-schema bump v0.3 → v0.4, keyed `[pack.<name>.adapters.<adapter>]`, with a hard cross-version refusal.** Recommended: yes — a v0.4 reader refuses an unrecognised `schema-version` on read *and* write, and a v0.4 file is not silently mis-parseable by a v0.3 reader. Decide-by 2026-06-29; default = adopt.
  5. **Conflict policy: same path + different SHA → refuse; cross-pack same path (even at equal SHA) → refuse; `--force` calls the existing Tier-2 `.upstream` companion writer.** Recommended: yes. Decide-by 2026-06-29; default = adopt.
  6. **Ownership is derived, not stored.** Recommended: yes — compute owner-sets by scanning rows' footprints; nothing stored per-file beyond the SHA already recorded. Decide-by 2026-06-29; default = adopt.
  7. **Install-time cross-adapter disclosure names shipped adapters only.** Recommended: yes. Decide-by 2026-06-29; default = adopt.
  8. **Greenfield — no migration of existing v0.3 installs.** Recommended: yes — adopters re-install rather than auto-convert. Decide-by 2026-06-29; default = adopt.

## Problem & goals

The install gate's "already installed" decision is **adapter-agnostic**. `commands/install.py` computes `installed_at_user = pack_name in user_state.packs` and refuses a second install of the same pack at the same scope regardless of adapter. The state model makes the same assumption: `State.packs` is `dict[str, PackState]` keyed by pack name, and each `PackState` carries exactly one `adapter` field (`config.py`). So at a given scope a pack is recorded once, with one adapter — there is no way to represent "`research` for claude-code **and** for codex", nor "`research` for kiro-cli **and** for kiro-ide".

This was a deliberate "one-install-one-adapter" invariant (RFC-0012 Alternative #7), justified by the claim that "multi-IDE adopters run install twice with different `--adapter` values; state file rows distinguish them by `adapter` and `scope` cleanly." That claim is **unbuildable under the current schema**: a name-keyed `dict` cannot hold two rows for one pack at one scope. The prose promised a coexistence the implementation never had, and the same Alternative admitted the fix would need "multiple rows per scope, a state-schema bump, and a new uninstall flow." This RFC builds exactly that.

A second force makes the fix more than a gate tweak. `.agents/skills/` is now an Anthropic-maintained open standard read by **codex, cursor, gemini, and copilot** (current docs below; Gemini prefers it over its own `.gemini/skills/`), and kiro-ide and kiro-cli both read `.kiro/skills/`. So a single physical skill file can serve a whole cohort of adapters, and two installs of the *same pack* can legitimately land on the same path with identical content. The adapter is no longer a partition of the filesystem — the **file path** is the real unit of collision and coexistence.

**Goals**

- One pack can be installed for multiple adapters at the same scope when their footprints are disjoint (fixes the reported bug).
- The adapters that all read `.agents/skills/` share **one** skill copy: installing the pack for any cohort member lands skills once and every cohort member reads them.
- When two adapter rows *of the same pack* touch the same path with identical content, they **co-own** it — one physical copy, removed only when the last owner goes.
- A genuine collision — same path with different content, or two *different packs* claiming one path — is refused with the conflicting paths named.
- The model is forward-ready: marking a prefix `shared` is contract data, so an adapter that adopts `.agents/skills/` later (e.g. Claude Code, [claude-code#31005](https://github.com/anthropics/claude-code/issues/31005)) joins by a one-line contract change.

**Non-goals**

- **Fan-out / "install for all detected adapters" in one command.** One install still targets one `--adapter`; coexistence accretes across repeated installs. (The shared prefix means one install already *covers* the cohort for skills — but each adapter's private primitives still need its own install.)
- **Projecting rules/steering across adapters.** Kiro reads `AGENTS.md` directly ([Kiro steering docs](https://kiro.dev/docs/steering/)), so there is no rules gap. Left untouched.
- **Migration of existing installs.** Greenfield (Decision 8) — no dist-tree-style converter.
- **Moving cursor/gemini/copilot's *agent/hook/command* projection.** Only the *skill* primitive moves to `.agents/skills/`; the rest stays on each adapter's native `.cursor/` / `.gemini/` / `.github/`+`.copilot/` paths exactly as ADR-0013/0015/0016 specify.

## Proposal

### Decision 1 + 4 + 6 — Footprint co-ownership, state v0.4, derived ownership

The install identity becomes the **footprint**: the set of relpaths (each with its content SHA) a `(pack, adapter, scope)` install writes. The per-relpath SHA tracking already exists in `PackState.files`; this RFC promotes it from a record to the identity.

State schema bumps **v0.3 → v0.4**, re-keyed so a pack can carry multiple adapter rows:

```toml
schema-version = "0.4"

[pack.research.adapters.claude-code]
installed-version = "1.2.0"
scope = "user"
# files{} with per-relpath sha, as today

[pack.research.adapters.codex]
installed-version = "1.2.0"
scope = "user"
```

**Cross-version safety (the highest-leverage AC).** Today `load_state` defaults an *unrecognised* `schema-version` to parse-through and only refuses v0.1/v0.2 on write (`config.py`). That is unsafe here: a v0.3-era binary reading a v0.4 file would parse `[pack.research.adapters.claude-code]` as a pack literally named `research` with an `adapters` sub-table and **zero files**, so a later `uninstall` drops the row deleting nothing and an `install` treats every path as unowned. Decision 4 therefore requires the v0.4 reader to **refuse any `schema-version` it doesn't recognise, on both read and write** (raise the existing `StateFileLegacy`-style error), and that a v0.4 file is structurally non-mis-parseable by a v0.3 reader. The greenfield choice (Decision 8) covers *forward* upgrade; this covers *backward* read by a stale binary across mixed CI/local CLIs.

**Ownership is derived** (Decision 6): a relpath's owner-set is computed by scanning every `[pack.<name>.adapters.*]` row's `files` map — nothing stored per-file beyond the SHA already there. Ownership answers two questions:

- **Install gate.** For each incoming relpath `R`, compare against the union of installed footprints in this scope:
  - `R` absent / unowned → write it, claim ownership.
  - `R` owned by **another adapter row of the same pack** at the **same SHA** → co-own (record `R` in the incoming row's `files`); skip the write.
  - `R` owned at a **different SHA**, **or owned by a different pack** (even at equal SHA) → conflict (Decision 5).
  - Aggregate verdict: incoming `(pack, adapter)` already owns every `R` at matching SHA → *already installed* (upgrade path); some `R` new, no conflicts → *proceed*; any conflict → *refuse*.
- **Uninstall.** Remove a relpath only when the row being removed is its **last** owner. The decision is computed once against the persisted union of all `[pack.<name>.adapters.*]` rows (mirroring the existing capture-once discipline in `uninstall.py`), then acted on without re-derivation. Every per-file reader updated to the multi-row shape — `State.projected_paths`, `PackState.file_sha`, and `safety.classify` (which today takes the *first* owner via a `break`) must resolve ownership across all adapter rows, not first-hit. The orphan/artifact scan (`safety.scan_for_pack_artifacts`) is keyed by **pack across all its adapter rows** — a file owned by any sibling adapter row of the same pack is not an orphan. Each removed file is path-jail-validated against **its own adapter row's** `allowed-prefixes`, never a sibling's.

The intra-pack scoping (co-own only across adapter rows of the *same* pack) is deliberate: two unrelated packs that happen to ship a byte-identical file (a stock boilerplate `SKILL.md`, an empty `__init__.py`, a `LICENSE`) must not silently co-own a path neither intends to share. SHA-equality is necessary but not sufficient as an ownership signal across packs.

### Decision 2 + 3 — `shared` prefix class + cohort routing (supersedes the ADR skill-home decision)

Each prefix in the adapter contract's `allowed-prefixes` gains a class: `private` (adapter-exclusive) or `shared` (a path more than one adapter reads). A `shared` prefix declares its **reader cohort** (shipped adapters) so the install-time disclosure can name them.

| Shared prefix | Reader cohort (shipped adapters) | Skill copy | Agents |
| --- | --- | --- | --- |
| `.agents/skills/` | codex, cursor, gemini, copilot (forward-ready for Claude Code) | one, co-owned across same-pack rows | private, per-adapter format |
| `.kiro/skills/` | kiro-ide, kiro-cli | one, co-owned across same-pack rows | private — `.json` (cli) vs `.md` (ide) |
| `.claude/skills/` | claude-code (island, today) | private | private |

**Option A routing.** Every cohort adapter writes the `skill` primitive to its shared prefix. Codex already targets `.agents/skills/` (RFC-0009); **cursor, gemini, and copilot move their skill output there**, which supersedes the skill-home decision in ADR-0013/0015/0016. The evidence base is those tools' *current* documentation — all three read `.agents/skills/`, and Gemini's docs now make the alias *precedence-winning* over `.gemini/skills/` (Evidence below). The ADRs' native-home stance — and ADR-0016's "the alias is not relied on" — were written before that support matured; they are stale, and this RFC is the vehicle to supersede them.

**No regression to ADR-0015's "partial native tree is worse than none" concern.** That concern was about leaving a primitive *unprojected* so the adapter's precedence masks the gap. Here skills remain fully projected — just to `.agents/skills/`, which cursor reads natively alongside `.cursor/`. Each cohort adapter still gets a complete primitive set (skills via `.agents/skills/`, agents/hooks/commands via its native tree); nothing is dropped.

The reported bug is fixed independently of routing: `claude-code` (`.claude/skills/`) and `codex` (`.agents/skills/`) have disjoint footprints, so the gate fix (Decision 1) lets them coexist regardless.

### The kiro family — worked example for co-ownership

RFC-0022 already differentiates the agent formats: kiro-ide projects `.kiro/agents/<name>.md`, kiro-cli projects `.kiro/agents/<name>.json` (`kiro.py`). Both project skills to `.kiro/skills/`. Under the footprint model:

- **Today:** installing kiro-ide after kiro-cli is refused outright — the pack-name-keyed gate fires before any path comparison. Decision 1 removes that refusal first; only then does the footprint comparison run.
- **Install kiro-cli:** writes `.kiro/skills/<s>/SKILL.md` + `.kiro/agents/<a>.json`.
- **Then install kiro-ide:** the skill paths are already present at the same SHA, owned by a sibling row of the *same pack* → **co-owned, not rewritten, not orphaned**; `.kiro/agents/<a>.md` is a new relpath (different extension) → written. Both adapters now work.
- **Uninstall kiro-cli:** removes the `.json` agents; the shared skills remain (kiro-ide is still an owner).

The same co-ownership now also governs `.agents/skills/`: install the pack for codex, then for cursor → the skills are already there at the same SHA → co-owned, and cursor's install writes only its private `.cursor/` agents/hooks/commands. The load-bearing requirement: the orphan scan during the second install must recognise the first row's shared files as owned-by-a-sibling-row, **not** sweep them (Decision 1's pack-across-adapter-rows scan).

### Decision 5 — Conflict policy

A same-path/different-SHA collision, or any cross-pack same-path collision (even at equal SHA), is **refused** with the conflicting relpaths named. `--force` calls the **existing Tier-2 `.upstream` companion writer** (`safety.write_companion`) — no new override is invented. The install path already drops `.upstream` companions on its Tier-2-squatter branch (`install.py:940`); wiring the writer onto the *new footprint-conflict verdict* this RFC adds is the only new surface, which the follow-on spec must add explicitly. This mirrors dpkg's refuse-by-default with an explicit `--force-overwrite` escape.

### Install-time disclosure (Decision 7 — shipped adapters only)

After a successful install that wrote to a `shared` prefix, stderr names the other shipped adapters in that prefix's cohort and states the boundary:

```
Installed research for codex (user).
  Skills → ~/.agents/skills/ — also read by cursor, gemini, copilot.
  Hooks & subagents → ~/.codex/ — codex only; install those adapters
  separately to get them there.
```

## Options considered

**Axis: what is the unit of install identity / collision** — exhaustive over the granularity ladder from coarsest to finest (whole-install → tuple → file), the full space of "what does the gate compare?". Option 3 is *not* a fourth rung — it is a storage-representation sub-choice *within* the file-granularity rung (Option 2), listed because it is the obvious alternative implementation of file-level identity and the one the prior art (`npx skills`) defaults to.

| Option | Compares | Coexist? | Shared-path? | Verdict |
| --- | --- | --- | --- | --- |
| 0. Do nothing | pack name | no | breaks (name-keyed) | rejected |
| 1. (pack, adapter, scope) tuple | install tuple | yes, if tuple differs | **no** — two same-pack rows sharing a path double-write under independent rows | rejected |
| 2. **Footprint, content-addressed (recommended)** | per-relpath + SHA, intra-pack | yes | yes — share-if-identical (same pack), refuse otherwise | **selected** |
| 2-rep. Symlink representation of Option 2 | per-relpath, one canonical copy + symlinks | yes | yes | rejected — violates the no-symlink security posture |

- **Option 0 (do-nothing).** Cost of delay: the reported bug persists; every multi-IDE adopter is blocked from a second adapter; the cohort cannot share one skill copy; the kiro family cannot have both variants installed. Rejected.
- **Option 1 (tuple).** The "obvious" multi-row fix; grounds in dpkg/rpm per-package file ownership. Fails on shared paths: two same-pack rows write *the same paths*, so independent per-tuple rows both claim them — double-ownership and ambiguous uninstall, the "multiple rows + new uninstall flow" RFC-0012 feared without solving the sharing. Rejected as insufficient.
- **Option 2 (footprint, content-addressed, intra-pack).** Generalises the per-relpath SHA tracking already present. Files shared at identical content *within a pack* are co-owned (the **Nix** store-path resolution: identical content resolves to one shared entity); differing content, or any cross-pack claim, is refused (the **dpkg** file-conflict resolution). Selected.
- **Option 2-rep (symlink).** The `npx skills` default — one canonical copy, per-agent symlinks. Cleanest dedup, but `lint-packs` refuses symlinks and the projectors copy with `follow_symlinks=False` / `symlinks=True`-to-avoid-dereference precisely to defend against malicious-link exfiltration. Adopting symlinks would reopen that boundary. Rejected; the content-addressed copy model gets the same single-source-of-truth outcome within the posture.

## Risks & what would make this wrong

**Pre-mortem**

- **A cohort adapter quietly drops `.agents/skills/` support** (it is young — Copilot shipped Dec 2025) → routed skills stop being discovered for that adapter. Mitigation: the cohort is contract data; demoting an adapter back to its native home is a one-line contract change, and the per-tool support is re-verifiable from docs each contract bump.
- **Cross-version state read corrupts ownership.** A v0.3 binary reading a v0.4 file mis-parses adapter rows as zero-file packs. Mitigation: Decision 4's hard cross-version refusal; falsifier — round-trip a v0.4 file through a v0.3 reader and assert it raises.
- **Derived ownership miscounts and uninstall deletes a still-needed file.** Mitigation: last-owner computed against the persisted union of *all* adapter rows of *all* packs, captured once; falsifier — install a pack for two same-pack adapter rows, uninstall one, assert the shared skill survives; uninstall the second, assert it's gone.
- **Orphan scan sweeps a sibling row's files** (kiro-ide wipes kiro-cli `.json` agents; or a cursor install sweeps codex's `.agents/skills/`). Mitigation: scan keyed by pack-across-adapter-rows; dedicated regression test.
- **`safety.classify` first-owner `break` mis-classifies a co-owned, adopter-edited file.** Mitigation: update `classify`/`projected_paths`/`file_sha` to resolve across all rows; Tier-2 regression test.

**Key assumptions (falsifiable)**

- Cursor, gemini, and copilot reliably read `.agents/skills/` today. *Confirmed* against current docs (Evidence below); *wrong if* a future release narrows it — caught at the next contract-bump re-verification.
- Co-ownership cases are byte-identical by construction (skills are direct-directory copies, no per-adapter skill rewriting). *Wrong if* a cohort adapter introduces per-adapter skill rendering — then the conflict path (Decision 5) is the correct, loud behaviour.
- The single `~/.agentbundle/state.toml` can hold multiple adapter rows per pack without lock/format contention. *Confirmed* by the spike below (concurrency under two simultaneous `install`s is a spec test).

**Drawbacks**

- Supersedes three accepted ADRs (their skill-home portion) — a real governance cost, and it couples this RFC to upstream tools' evolving skill-discovery behaviour.
- A real state-schema migration surface (v0.3 → v0.4) and a more complex, reference-aware uninstall — irreducible; the cost RFC-0012 named and deferred.
- Greenfield means an adopter mid-flight on v0.3 re-installs rather than auto-upgrading (accepted, Decision 8).
- Derived ownership is an O(rows × files) scan per install/uninstall; negligible at realistic pack counts, but computation an explicit owner list would avoid. Chose derive for forward-compatibility.

## Evidence & prior art

- **Spike / de-risk result.** Riskiest assumption: that two disjoint-footprint installs can coexist given the single shared `~/.agentbundle/state.toml`. Confirmed structurally — the state file is one TOML holding `packs: dict`, written by `safety.write_jailed`; the only blockers to a second row are the name-keyed dict (Decision 4) and the name-keyed gate (Decision 1). No second state file, lock, or per-adapter store exists, so the footprint model is representable once the key is composite. The v0.4 TOML emitter and nested `[pack.<name>.adapters.<adapter>]` round-trip are flagged as construction tests for the spec.
- **Cohort `.agents/skills/` support (the basis for superseding ADR-0013/0015/0016).** Verified against each tool's current documentation:
  - **Cursor** loads skills from `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `~/.cursor/skills/` ([Cursor skills docs](https://cursor.com/docs/skills)).
  - **Gemini CLI** reads `.agents/skills/` and `~/.agents/skills/`; within a tier the **`.agents/skills/` alias takes precedence over `.gemini/skills/`** (docs updated 2026) ([Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/)) — this directly reverses ADR-0016's "alias is not relied on".
  - **Copilot** reads `.agents/skills/` (project) and `~/.agents/skills/` (personal), alongside `.github/skills/` / `~/.copilot/skills/` ([GitHub Docs — About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [VS Code — Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)).
- **Repo precedent.** [RFC-0012](0012-repo-scope-per-adapter-projection.md) **Alternative #7** rejected fan-out and named the exact cost this RFC pays ("multiple rows per scope, a state-schema bump, and a new uninstall flow"); its line 147 records "no state-schema bump … the field already exists" — Decision 4 reverses that. [RFC-0009](0009-codex-native-skills.md) established codex's `.agents/skills/` native home; [RFC-0022](0022-kiro-adapter-split.md) split kiro-ide (`.md`) from kiro-cli (`.json`) agents. [ADR-0013](../adr/0013-copilot-full-parity-user-scope-adapter.md)/[0015](../adr/0015-cursor-full-parity-distribution-adapter.md)/[0016](../adr/0016-gemini-cli-full-parity-adapter.md) chose native skill homes when those tools' `.agents/skills/` support was absent or immature — superseded here for the skill primitive only. [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md) keeps scope a per-pack default+allowance.
- **External prior art.** File-ownership-across-packages is well-trodden: dpkg fails to install when it would overwrite another package's files unless a `Replaces` is declared (or `--force-overwrite` is forced), per the [Debian handbook §5.2](https://debian-handbook.info/browse/el-GR/stable/sect.package-meta-information.html). Nix detects and prevents conflicting files across *different* packages, while *identical* install items resolve to a single shared store path rather than colliding ([NixOS/nix#5587](https://github.com/NixOS/nix/issues/5587)). Option 2 is the union of "share if identical (Nix store path)" and "refuse if different (dpkg)" without adopting symlinks. `npx skills`' symlink-vs-copy model: [vercel-labs/skills](https://github.com/vercel-labs/skills).

## Open questions

None outstanding for research. Open question 1 of the prior draft — whether to redirect cursor/gemini/copilot skills to `.agents/skills/` — is **resolved yes** by the cohort-support evidence above; the ADR supersession is the mechanism (Follow-on artifacts). Decisions 1–2 and 4–8 adopt by silence at the 2026-06-29 decide-by; **Decision 3 is the one call that requires an explicit Approver yes**, because it supersedes three Accepted ADRs and couples the catalogue to upstream tools' skill-discovery behaviour (Drawbacks).

## Follow-on artifacts

Filled in on acceptance. Expected:

- **ADR** — record the footprint-co-ownership install identity (pairs with ADR-0002) and the `shared` prefix class.
- **ADR(s)** superseding the **skill-home decision** of ADR-0013, ADR-0015, and ADR-0016 (route cohort skills to `.agents/skills/`). Mark each prior ADR with the repo's established partial-amendment status idiom (precedent: [ADR-0001](../adr/0001-adopt-agents-md-and-doc-hierarchy.md) — `Accepted — partially amended: the skill-home sub-decision is superseded by ADR-NNNN; agent/hook/command projection stands`), not a bare "Superseded by" (which would imply the whole ADR).
- **Spec** at `docs/specs/shared-prefix-aware-multi-adapter-install/` — contract bump (prefix-class + reader-cohort fields; cursor/gemini/copilot skill target → `.agents/skills/`); state schema v0.3 → v0.4 + the **hard cross-version refusal** AC; footprint-aware install gate (intra-pack co-ownership, cross-pack refusal); reference-aware uninstall with the **capture-once last-owner** AC, the **per-row path-jail** AC, and updates to every per-file reader (`projected_paths`, `file_sha`, `safety.classify` — no first-hit `break`); the `.upstream` companion call wired onto the install conflict path; install-time disclosure rail (pinned strings); kiro-family + `.agents/skills/` cohort coexistence and Tier-2 co-owned-edit regression tests; v0.4 emitter round-trip / nested-key construction test; concurrent-install race test.
- **Erratum** appended to [RFC-0012](0012-repo-scope-per-adapter-projection.md) noting Alternative #7 is superseded here (frozen RFC → erratum block, mirroring RFC-0011's precedent).
