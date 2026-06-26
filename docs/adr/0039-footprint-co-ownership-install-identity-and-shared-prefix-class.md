# ADR-0039: Install identity is the content-addressed footprint, with a `shared` prefix class

- **Status:** Accepted
- **Date:** 2026-06-26
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0052](../rfc/0052-shared-prefix-aware-multi-adapter-install.md) (the decision this records), [ADR-0002](0002-install-scope-per-pack-default-and-allowance.md) (install scope is a per-pack default + allowance — this ADR pairs with it as the *identity* half of the install model), [ADR-0040](0040-route-cohort-skills-to-shared-agents-skills-home.md) (the sibling decision that routes cohort skills to the shared prefix this ADR introduces), [RFC-0012](../rfc/0012-repo-scope-per-adapter-projection.md) (Alternative #7 — the rejected one-install-one-adapter fan-out, reversed here)

## Context

The install gate's "already installed" decision was **adapter-agnostic**. `commands/install.py` computed `installed_at_user = pack_name in user_state.packs` and refused a second install of the same pack at the same scope regardless of adapter. The state model carried the same assumption: `State.packs` was `dict[str, PackState]` keyed by pack name, each `PackState` holding exactly one `adapter` field (`config.py`). At a given scope a pack was recorded once, with one adapter — there was no way to represent "`research` for claude-code **and** for codex", nor "`research` for kiro-cli **and** for kiro-ide".

This was a deliberate "one-install-one-adapter" invariant (RFC-0012 Alternative #7), justified by the claim that multi-IDE adopters run install twice with different `--adapter` values and state-file rows distinguish them by `adapter` and `scope` cleanly. That claim was **unbuildable under the name-keyed schema**: a `dict` keyed by pack name cannot hold two rows for one pack at one scope. The prose promised a coexistence the implementation never had, and the same Alternative admitted the fix would need "multiple rows per scope, a state-schema bump, and a new uninstall flow."

Two forces made this more than a gate tweak:

- **A real reported bug.** Installing `research` for `codex` after installing it for `claude-code` was refused with "already installed at user; use upgrade", even though the two write to entirely separate trees (`.agents/skills/` vs `.claude/skills/`). The gate keyed on pack name alone and was blind to the adapter.
- **Genuinely shared paths.** `.agents/skills/` is read by codex, cursor, gemini, and copilot; `.kiro/skills/` is read by both kiro-ide and kiro-cli. A single physical skill file can serve a whole cohort, and two installs of the *same pack* can legitimately land on the same path with identical content. The adapter is no longer a partition of the filesystem — the **file path** is the real unit of collision and coexistence.

The question this ADR answers: **what is the right identity for an install, and how should two installs that touch the same path behave?**

## Decision

> **The identity of an install is its footprint — the set of relpaths, each with its content SHA, that a `(pack, adapter, scope)` install writes — and "already installed" is resolved per-file by content, not by pack name. Ownership of a path is *derived* by scanning installed rows' footprints, not stored. A path is co-owned when more than one adapter row *of the same pack* claims it at identical content; it is removed only when its last owner is uninstalled. A genuine collision — same path at different content, or any cross-pack claim on one path even at equal content — is refused.**

This rests on a contract addition: each prefix in an adapter's `allowed-prefixes` gains a **class** — `private` (adapter-exclusive) or `shared` (a path more than one adapter reads) — and a `shared` prefix declares its **reader cohort** (the shipped adapters that read it) so install-time disclosure can name them.

The model is realized through these concrete rules:

- **State schema bumps v0.3 → v0.4**, re-keyed `[pack.<name>.adapters.<adapter>]` so a pack can carry multiple adapter rows at one scope. The per-relpath SHA tracking already present in `PackState.files` is promoted from a record to the identity.
- **Cross-version refusal is hard.** A v0.4 reader refuses any `schema-version` it does not recognise, on **both read and write** (not only the legacy v0.1/v0.2 write-refusal that exists today), and a v0.4 file is structurally non-mis-parseable by a v0.3 reader. Without this, a stale v0.3 binary parses `[pack.research.adapters.claude-code]` as a pack literally named `research` with zero files, and a later uninstall/install corrupts ownership.
- **Ownership is derived, not stored.** A relpath's owner-set is computed by scanning every `[pack.<name>.adapters.*]` row's `files` map; nothing is stored per-file beyond the SHA already there.
- **Co-ownership is intra-pack only.** Two adapter rows co-own a path only when they belong to the *same* pack and the content SHA matches. Two unrelated packs that happen to ship a byte-identical file (a stock boilerplate `SKILL.md`, an empty `__init__.py`, a `LICENSE`) must not silently co-own it — SHA-equality is necessary but not sufficient across packs.
- **Conflict policy.** Same path at a different SHA, or any cross-pack same-path claim (even at equal SHA), is refused with the conflicting relpaths named; `--force` routes through the **existing Tier-2 `.upstream` companion writer** (`safety.write_companion`) rather than inventing a new override.
- **Uninstall removes a path only when the removed row is its last owner.** The last-owner decision is computed once against the persisted union of all `[pack.<name>.adapters.*]` rows (mirroring the existing capture-once discipline in `uninstall.py`), then acted on without re-derivation. Every per-file reader — `State.projected_paths`, `PackState.file_sha`, and `safety.classify` (which today takes the first owner via a `break`) — resolves ownership across all adapter rows, and the orphan scan (`safety.scan_for_pack_artifacts`) is keyed by pack-across-its-adapter-rows so a sibling row's files are never swept.

The reported bug is fixed independently of the routing decision in ADR-0040: claude-code (`.claude/skills/`) and codex (`.agents/skills/`) have disjoint footprints, so the footprint gate lets them coexist regardless of where cohort skills land.

## Decision drivers

- **Represent legitimate coexistence** — a pack installed for two adapters at one scope must be expressible and must work; the name-keyed model cannot express it.
- **Share one copy where the path is genuinely shared** — a cohort that all reads `.agents/skills/` should not double-write or fight over the same file.
- **Refuse only real collisions** — a same-path/different-content clash, or a cross-pack land-grab, must be loud; everything else proceeds.
- **No new storage and no new override surface** — reuse the per-relpath SHA already recorded and the Tier-2 `.upstream` companion writer already wired, so the model adds identity semantics, not new persisted fields.
- **Forward-readiness** — marking a prefix `shared` is contract data, so an adapter that adopts `.agents/skills/` later joins the cohort by a one-line contract change.

## Consequences

**Positive:**

- The reported multi-IDE bug is fixed: disjoint-footprint installs of one pack coexist at one scope.
- A cohort shares one physical skill copy, co-owned across same-pack rows and removed only when the last owner goes.
- Real collisions stay loud (named relpaths; `--force` → `.upstream`), reusing the existing companion machinery — no new override invented.
- The `shared` prefix class makes cohort membership declarative contract data; a future cohort adapter joins by editing the contract, not the engine.

**Negative:**

- A real state-schema migration surface (v0.3 → v0.4) and a more complex, reference-aware uninstall — the irreducible cost RFC-0012 Alternative #7 named and deferred.
- Derived ownership is an O(rows × files) scan per install/uninstall — negligible at realistic pack counts, but computation an explicit stored owner-list would avoid. Derivation was chosen for forward-compatibility (no per-file owner field to migrate when a cohort changes).
- The first-owner `break` in `safety.classify`, and the per-file readers around it, must all move to resolve ownership across rows; a missed reader silently mis-classifies a co-owned, adopter-edited file.

**Neutral / to revisit:**

- Migration is greenfield (RFC-0052 Decision 8) — existing v0.3 installs re-install rather than auto-convert. If field reports show that hurts, an auto-converter is a later, separable decision.
- Ownership is derived today; if the O(rows × files) scan ever bites at scale, switching to a stored owner-set is a contained change behind the same gate.

## Confirmation

The model is enforced by the implementing spec's acceptance criteria and their construction tests in `docs/specs/shared-prefix-aware-multi-adapter-install/` — in particular: a v0.4 file round-tripped through a v0.3 reader must raise; install of one pack for two same-pack adapter rows followed by uninstall of one must leave the shared skill in place, and uninstall of the second must remove it; an orphan scan during the second cohort install must not sweep the first row's shared files; and a cross-pack same-path claim must refuse. There is no separate mechanical ADR-status lint (per ADR-0027); conformance is otherwise reviewer-checked against this ADR.

## Alternatives considered

The axis is *what is the unit of install identity / collision*, exhaustive over the granularity ladder from coarsest to finest (whole-install → tuple → file).

- **Do nothing (compare pack name).** The status quo. Rejected against *represent legitimate coexistence*: the reported bug persists, every multi-IDE adopter is blocked from a second adapter, the cohort cannot share one copy, and the kiro family cannot have both variants installed.
- **(pack, adapter, scope) tuple identity.** The "obvious" multi-row fix, grounded in dpkg/rpm per-package file ownership. Rejected against *share one copy where the path is genuinely shared*: two same-pack rows write the *same* paths, so independent per-tuple rows both claim them — double-ownership and ambiguous uninstall, the exact "multiple rows + new uninstall flow" RFC-0012 feared without solving the sharing.
- **Footprint, content-addressed, intra-pack (selected).** Generalises the per-relpath SHA tracking already present. Files shared at identical content *within a pack* are co-owned (the Nix store-path resolution: identical content resolves to one shared entity); differing content, or any cross-pack claim, is refused (the dpkg file-conflict resolution). Selected.
- **Symlink representation of the footprint model.** The `npx skills` default — one canonical copy, per-agent symlinks. Cleanest dedup, but `lint-packs` refuses symlinks and the projectors copy with `follow_symlinks=False` precisely to defend against malicious-link exfiltration. Rejected against the repo's no-symlink security posture; the content-addressed copy model gets the same single-source-of-truth outcome without reopening that boundary.

## References

- [RFC-0052](../rfc/0052-shared-prefix-aware-multi-adapter-install.md) — the proposal this ADR records (Decisions 1, 2, 4, 5, 6).
- [RFC-0012 Alternative #7](../rfc/0012-repo-scope-per-adapter-projection.md) — the rejected fan-out / one-install-one-adapter item this reverses; an erratum there points here.
- [Debian handbook §5.2](https://debian-handbook.info/browse/el-GR/stable/sect.package-meta-information.html) — dpkg's refuse-on-file-conflict-unless-`Replaces` model.
- [NixOS/nix#5587](https://github.com/NixOS/nix/issues/5587) — Nix's identical-content-resolves-to-one-store-path model.
