# RFC-0034: Pack profiles — one-command install of a curated, single-scope pack set

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-14
- **Date closed:** <!-- filled in when status reaches a terminal state -->
- **Related:** [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) (catalogue model, "Common adoption patterns"), [RFC-0002](0002-self-hosting.md) (source-vs-projected split), [RFC-0003](0003-spec-and-cli.md) (CLI surface), [RFC-0004](0004-install-scope-per-pack.md) (install scope), [RFC-0011](0011-pack-allowed-adapters.md) (`allowed-adapters`), [RFC-0031](0031-catalogue-package-manager-posture.md) (catalogue posture: hygiene not infrastructure); distinguishes [ADR-0003](../adr/0003-credential-broker-contract.md) / [RFC-0013](0013-credential-broker-contract.md) option F (meta-pack, rejected). Charter Principle 3 (`docs/CHARTER.md`).

## The ask

**Recommendation (BLUF):** Add **pack profiles** — a first-party-curated, named, **single-scope** set of packs an adopter installs in one command. A profile is either a **user-scope role toolkit** (`install --profile solution-architect` → `architect` + `research` + `contracts` into user scope) or a **repo-scope setup bundle** (`install --profile full-ceremony` → `core` + `governance-extras` + `user-guide-diataxis` + `monorepo-extras` into a repo). **A profile never mixes scopes:** handling a repo is a separate concern from handling user space. A profile is a hand-authored `profiles/<name>.toml` file at the catalogue root, read **only** by the `agentbundle` CLI; it adds zero primitives, zero runtime, and zero adapter-contract surface — distribution hygiene in the [RFC-0031](0031-catalogue-package-manager-posture.md) lineage, not package-manager infrastructure.

**Why now (SCQA):** *Situation* — the catalogue is a collection of independently-installable packs, consumed à la carte ([RFC-0001](0001-bundle-distribution-by-adapter-spec.md)), and RFC-0001 already blesses named pack combinations (`core` + `governance-extras`; "Full ceremony" = all four repo packs) — but only in a prose table no tool can execute. *Complication* — setting up a role or a repo is N separate `--pack` invocations, and the curated knowledge (which packs go together, and for a repo bundle in *what order*, since `governance-extras`/`user-guide-diataxis`/`monorepo-extras` all require `core`) lives only in a human's head. *Question* — should the catalogue promote those blessed combinations from prose into one-command installable units, in the thinnest form that respects the charter and keeps repo setup cleanly separate from user-space setup?

**Decisions requested:**

1. **Adopt pack profiles at all** (vs. do-nothing / keep prose) — *and with it, the explicit charter call:* does one-command install clear Principle 4 ("used often enough to stick")? This is the proposal's weakest pillar and the Approver must rule on it, not wave it through. · *Recommended:* yes — the substantive kernel is encoding the curated combinations (and, for repo bundles, their dependency ordering) once, and onboarding recurs per repo *and* per new team member (see frequency argument under Risks). · decide-by: RFC acceptance; default if no objection: **adopt**.
2. **Define profiles as `profiles/<name>.toml`** (one file per profile, catalogue root, id = filename stem). · *Recommended:* yes — scales without merge conflicts, matches the repo's one-per-file grain. · decide-by: acceptance.
3. **CLI-route only in v1** — `agentbundle install --profile` + `list-profiles`; no change to `.claude-plugin/marketplace.json`, the build pipeline, or self-host. · *Recommended:* yes. · decide-by: acceptance.
4. **Profiles are scope-homogeneous — repo-only or user-only, never mixed.** Each profile declares `scope = "user" | "repo"`; every pack in it must allow that scope; `--scope` is rejected with `--profile`. Both kinds are first-party in v1. · *Recommended:* yes — handling a repo is separate from handling user space; mixing conflates two lifecycles and reintroduces a cross-scope partial-failure surface. · decide-by: acceptance.
5. **Resolution contract** — ordered, deps-first; one adapter pins the whole batch; all-pre-flight-before-any-write; skip-already-installed; a lint enforces scope-homogeneity + dep-completeness + order validity. · *Recommended:* yes. · decide-by: acceptance.
6. **First-party-curated only; no profile entity in state; no schema or contract bump.** · *Recommended:* yes; adopter-authoring is a named non-goal / follow-on. · decide-by: acceptance.

## Problem & goals

**Diagnosis.** Installing a curated set of packs today is N invocations of a single-pack command (`install` takes exactly one `--pack`, no `nargs` — `cli.py:218`). The curated knowledge — *which* packs constitute a role or a repo setup, and for a repo bundle *in what order* they install (the three governance/docs/monorepo packs each require `core`) — exists only in a human's head or in RFC-0001's prose "Common adoption patterns" table (`0001…:668-677`), which no tool can execute. The friction is highest at the catalogue's most frequent events: a person taking on a role (setting up their user space) and a repo being stood up (setting up repo space).

**Two distinct lifecycles, deliberately kept apart.** Per [RFC-0004](0004-install-scope-per-pack.md), user-scope packs are the content that "travels cleanly across every repo an adopter opens" — a person's portable, cross-project toolkit — while repo-scope packs set up a *specific repo*. These are different lifecycles. **A profile therefore never mixes the two:** a user profile is a role toolkit; a repo profile is a repo setup bundle. You can have both kinds; a single profile is one or the other. Mixing them in one command would conflate the lifecycles and reintroduce a cross-scope, half-applied-install failure surface that a single-scope profile simply avoids.

This is a real but **bounded** problem: it is convenience over an existing capability. The honest case for acting is that the curated combinations — and, for repo bundles, their dependency ordering — are knowledge worth making executable, and that single-scope profiles are clean, self-contained units.

**Goals.**

- One command installs a curated, named, **single-scope** set of packs — a user-scope role toolkit or a repo-scope setup bundle.
- Keep each profile self-contained at one scope; never mix repo and user setup in one unit.
- Reuse the existing `install` pre-flight contract (resolve → check → write) so a profile is no less safe than installing each pack by hand.
- Stay adapter-neutral: a profile is a list of pack names and inherits each pack's `allowed-adapters`.
- Smallest possible surface: no new primitive type, no runtime, no state schema change, no adapter-contract bump.

**Non-goals** (could have been goals; deliberately dropped):

- **Mixed-scope profiles.** A profile is repo-only or user-only — never both. A single command that sets up *both* a repo and the user's toolkit is explicitly out: the two lifecycles stay separate.
- **Adopter-authored profiles.** v1 ships first-party-curated profiles only. Adopter authoring adds file-location (repo vs. user), discovery, and name-collision/precedence questions not needed to prove the value. Deferred to a follow-on (see Open questions).
- **A profile as a tracked, upgradable entity.** No profile membership is recorded; `upgrade` and `uninstall` stay strictly per-pack. A profile is a one-time orchestration, not an installed object.
- **Transitive dependency resolution.** A profile is an explicit, closed list; we do not compute the dependency closure at install time. ([RFC-0031](0031-catalogue-package-manager-posture.md) defers a real resolver until a second catalogue or a real diamond conflict exists.)
- **Profiles on the Claude-plugin `/plugin` and APM routes.** Those formats have no composition concept; wiring profiles into them is out of scope for v1.
- **Profiles spanning multiple catalogues.** A profile names packs within one catalogue.

## Proposal

The sections below are keyed to the Decisions requested: **D2–D6** map to Decisions 2–6. Decision 1 (adopt at all / charter gate) has no design section by nature — it is the go/no-go on everything here.

### D2 — where profiles are defined: `profiles/<name>.toml` at the catalogue root

Profiles live in a new top-level `profiles/` directory, a sibling of `packs/`, one file per profile. Two first-party examples — one of each scope:

```
profiles/
  solution-architect.toml   # user-scope role toolkit
  full-ceremony.toml        # repo-scope setup bundle
```

```toml
# profiles/solution-architect.toml — a USER-scope role toolkit
scope = "user"
description = "Solution architect: the portable cross-project toolkit — architecture, research, and contract authoring."

packs = [
  { pack = "architect" },
  { pack = "research" },
  { pack = "contracts" },
]
```

```toml
# profiles/full-ceremony.toml — a REPO-scope setup bundle
scope = "repo"
description = "Full governance ceremony for a repo: core plus RFC/ADR governance, user guides, and monorepo scaffolding."

# Ordered deps-first: governance-extras / user-guide-diataxis / monorepo-extras
# each require `core`, so `core` is listed first.
packs = [
  { pack = "core" },
  { pack = "governance-extras" },
  { pack = "user-guide-diataxis" },
  { pack = "monorepo-extras" },
]
```

- **A profile declares its `scope`** (`"user"` or `"repo"`) — a required field. It is the one bit that distinguishes a role toolkit from a repo bundle, and it makes the never-mix rule lint-checkable (D4).
- **Identity is the filename stem.** `--profile solution-architect` ⇒ `profiles/solution-architect.toml`. No redundant `name` field to drift — identity has a single source of truth, exactly as a pack's identity is its directory name and an RFC's is its ordinal-filename. A lint validates the stem matches the kebab-case grammar already used for pack names (`^[a-z0-9][a-z0-9-]*$`).
- **It belongs to the catalogue, not to any pack.** `pack.toml` is per-pack and cannot own a cross-pack set; the only existing cross-pack primitive, `[pack.dependencies]`, is a *needs* graph, not a *role/setup* set. A profile is catalogue-level metadata, so it sits at the catalogue root next to `packs/` and `Makefile`.
- **One file per profile** scales without the concurrent-PR merge conflicts a single aggregated `profiles.toml` would invite (the same collision class we already hit on RFC/ADR ordinals), and matches the repo's grain: every entity that grows is one-per-file (`docs/rfc/NNNN-*.md`, `docs/adr/`, `packs/<pack>/`). The only aggregated manifest, `marketplace.json`, is *generated*, not hand-authored.
- **Flat file, not a dir-per-profile.** A profile is a scope, a description, and an ordered pack list; `profiles/<name>/…` is a trivial future migration if a profile ever needs companion files. v1 doesn't pay for it.

### D3 — CLI-route only; the catalogue serves profiles by being read directly

`agentbundle install` already resolves a catalogue URI and reads the catalogue tree directly — `resolve_catalogue(uri)` → `catalogue_dir`, then `_locate_pack(catalogue_dir, …)` looks in `packs/<pack>/` (`install.py:185-193`). It never goes through `marketplace.json`. Profiles ride the same mechanism:

- **`agentbundle install --profile <name> <catalogue>`** reads `catalogue_dir/profiles/<name>.toml`, expands it to its ordered pack list, and installs them at the profile's declared scope (see D4/D5). `--profile` and `--pack` are mutually exclusive — a small but real argparse change: `--pack` is today a bare `required=True` arg (`cli.py:218`) with no mutex group, so this converts it into a member of a **required mutually-exclusive group** with `--profile`.
- **`agentbundle list-profiles <catalogue>`** globs `catalogue_dir/profiles/*.toml` and prints each profile's id, scope, and description (parallel to the existing `list-packs`, [RFC-0003](0003-spec-and-cli.md)).
- **No server-side change.** For the CLI route the catalogue *is* the checkout/clone; the CLI reads the file, exactly as `--pack` reads `packs/*/pack.toml`. We **do not** modify `.claude-plugin/marketplace.json`, the `marketplace` build recipe, or self-host. (Self-host is internal repo tooling, not the adopter-facing catalogue; it stays untouched.)
- **Claude-plugin and APM routes** have no composition concept and are out of scope for v1 — consistent with [RFC-0003](0003-spec-and-cli.md) framing the CLI as complementary to, not a replacement for, the install routes.

The CLI delta is three small items: the `--pack`/`--profile` required-mutex conversion, a `list-profiles` subparser, and the `--profile` reader/orchestrator. No build-pipeline, marketplace, or self-host change.

### D4 — scope-homogeneous: repo-only or user-only, never mixed

A profile covers exactly one scope, declared in its `scope` field. This encodes the repo-vs-user-space separation directly:

- **A user profile** (`scope = "user"`) is a person's portable, cross-project toolkit (e.g. `solution-architect`). **A repo profile** (`scope = "repo"`) sets up a specific repo (e.g. `full-ceremony`). Both are first-party in v1.
- **Every pack in a profile must allow the declared scope** — it lists that scope in `allowed-scopes` ([RFC-0004](0004-install-scope-per-pack.md)). The lint (D5) enforces this, so a `scope = "user"` profile naming a repo-only pack (e.g. `core`, `allowed-scopes = ["repo"]`), or a `scope = "repo"` profile naming a user-only pack, fails the build. This is what makes "never mix" mechanical: no single declared scope can satisfy a set that straddles repo-only and user-only packs.
- **All packs resolve at the profile's declared scope.** No per-entry scope pin; entries are just pack names.
- **`--scope` is rejected with `--profile`** — the profile already declares its scope, so a conflicting or redundant flag is refused rather than silently reconciled.
- **Single-scope is strictly safer.** Because a profile touches one scope's state and one path-jail, there is no cross-scope, half-applied-install window (one scope's write succeeding while the other's preconditions fail) — a failure mode a mixed-scope profile would have.

### D5 — resolution contract: ordered, one-adapter, all-pre-flight-before-any-write

A profile install is a **thin orchestrator** over the existing single-pack `install.run` path. It inherits install's documented pre-flight contract — *"every scope's preconditions run before any write to either scope"* (`install.py:1-26`) — and extends the same all-checks-before-any-write guarantee from one pack to the **whole batch** (and across adapters):

1. **Expand & filter.** Read the profile; resolve every pack at the profile's declared scope (D4). Drop packs already installed at that scope, reporting `already present, skipped` — so single-pack install's refuse-on-reinstall (`install.py:426`) is never triggered and stays untouched. A profile is declarative "ensure present."
2. **Pin one adapter for the whole batch.** Resolve a single target adapter **once** — from explicit `--adapter` if given, else by running the normal resolution for the profile's scope a single time (the per-adapter environment probe at user scope, `DEFAULT_ADAPTER` at repo scope) — then **pin that one adapter for every pack and assert each pack's `allowed-adapters` includes it**. This is the load-bearing override: left to itself, `_resolve_target_adapter` resolves *per pack* (the user-scope probe returns the first environment match; the repo-scope branch falls back to `DEFAULT_ADAPTER`, else `allowed_adapters[0]`), which could silently split a profile across adapters. If any pack disallows the pinned adapter, refuse before any write, naming the pack and suggesting a compatible `--adapter`. Every pack in a profile install therefore lands on one consistent adapter target.
3. **Validate deps against the batch.** install's required-dep gate checks `[[pack.dependencies.required]]` against union state (`install.py:3203`) — but a pack listed later in the batch isn't in state yet. The orchestrator validates each pack's required-deps against *(current union state ∪ the profile's pack set)*. This is the **one minimal `install.py` change**: the dep gate gains an "also-being-installed in this batch" set parameter. The `full-ceremony` repo profile exercises exactly this — `governance-extras`/`user-guide-diataxis`/`monorepo-extras` each require `core ^0.1`, satisfied by `core` being earlier in the same batch. All of this is pre-flight — before any byte is written.
4. **Write in listed (deps-first) order.** install is not transactionally rolled back mid-write (per-file `write_jailed`, Step 9); maximal pre-flight shrinks the residual failure window to genuine I/O errors (disk full) — the same residual single-pack install already accepts. Writing in dependency-respecting order means any aborted prefix is still internally consistent (a dependent is never on disk without its dep). On the residual, report a per-pack success/fail summary; per-pack state rows record ground truth.

**Order is load-bearing, and authored, not computed.** Profiles are an ordered list authored deps-first. A **lint** enforces three invariants: *scope-homogeneity* (every pack allows the profile's declared scope — D4), *dependency-completeness* (the set is closed under each pack's required-deps — no "install X first" surprise; for `full-ceremony`, `core` must be present), and *order validity* (each pack's required-deps appear earlier in the list — `core` before `governance-extras`). Correctness is pushed to author-time lint; the orchestrator stays a dumb iterator with no runtime graph logic.

### D6 — curated-only; no state entity; no schema or contract bump

- **First-party-curated.** The catalogue ships a small starter set (`solution-architect` at user scope, `full-ceremony` at repo scope); adding a profile is a normal PR adding one `profiles/<name>.toml`.
- **No profile in state.** Each pack writes its normal row at the profile's scope (a repo profile → repo `.agentbundle-state.toml`; a user profile → user `~/.agentbundle/state.toml`); no profile membership is recorded. The state schema stays at v0.3 — **no bump**. (Optional provenance: the existing per-row `install_route` field could carry `"profile"` instead of `"cli"`. This is zero-schema-change but not free: `install_route` is a hardcoded literal at `install.py:851`, so it requires parameterizing that write-site. Recommended but severable — see Open question 3.)
- **No adapter-contract bump.** A profile carries no adapter information; adapter resolution reuses `_resolve_target_adapter` + each pack's `allowed-adapters` ([RFC-0011](0011-pack-allowed-adapters.md)) unchanged. The contract governs per-pack projection shape; profiles sit above it and touch neither projection nor schema.

### Migration path

None — this is additive. No existing state, file, or manifest changes shape. The first profiles (`profiles/solution-architect.toml`, `profiles/full-ceremony.toml`) and the CLI surface land together; existing per-pack install/upgrade/uninstall is untouched.

## Options considered

**Axis A — how much machinery the composition needs** (the load-bearing axis: a profile can be anything from prose to a tracked package-manager entity; the options below span that spectrum from least to most machinery):

| Option | Machinery | Verdict |
|---|---|---|
| **A0 — Do nothing** (keep RFC-0001 prose patterns) | none | Cost of delay: the most frequent setup moments stay N commands, and the curated combinations + repo dep-ordering stay prose no tool can execute. Honest contender; loses on the executable-mapping kernel. |
| **A1 — Thin CLI orchestrator + `profiles/<name>.toml`** ★ | one catalogue-root dir, one CLI flag + `list-profiles`, one dep-gate parameter, one lint | Smallest design that executes the blessed combinations. **Recommended.** |
| **A1b — A1, also surfaced on the plugin/APM routes** (profiles declared in/alongside the generated `marketplace.json`, still CLI-orchestrated, no state entity) | A1 + a marketplace-manifest field + per-route projection | More reach, but those formats have no composition concept yet, so it adds projection surface for unproven demand. Deferred to OQ2. |
| **A2 — First-class profile entity** (tracked in state, profile `upgrade`/`uninstall` lifecycle) | state schema bump, profile lifecycle, membership tracking | Collides with [RFC-0031](0031-catalogue-package-manager-posture.md) non-goals (no registry mechanics, no resolver) and Principle 3 (infrastructure). Rejected. |

Prior art for A1: package ecosystems add "a named set installed in one command" *without* new runtime infrastructure — Python **extras** (`pip install 'pkg[PDF,EPUB]'`), **dnf groups** ("virtual collections of packages"; `dnf group install`), and VS Code **Extension Packs** (`extensionPack` field, "a set of extensions installed together"). All three are thin composition layers over an existing per-unit installer — exactly A1's shape. A2's "tracked entity" is what dnf groups add (group state in the package DB); we deliberately stop short.

**Axis B — how profile definitions are laid out on disk** (exhaustive over the storage shape of the manifest):

| Option | Verdict |
|---|---|
| **B1 — Single `profiles.toml`** (all profiles) | Merge-conflict magnet on concurrent PRs; cuts against the repo's one-per-file grain. Rejected. |
| **B2 — `profiles/<name>.toml`, one per profile** ★ | Scales, conflict-free, clean per-profile diff/review/ownership. Mirrors `docs/rfc/`, `docs/adr/`, `packs/<pack>/`. **Recommended.** |
| **B3 — `profiles/<name>/profile.toml`** (dir per profile) | Right shape only once a profile needs companion files; premature now. Trivial future migration from B2. Deferred. |

**Axis C — install order** (exhaustive over "who orders the batch"):

| Option | Verdict |
|---|---|
| **C1 — Authored deps-first order + lint** ★ | Dumb orchestrator, no runtime graph logic, transparent (what you list is what runs). **Recommended.** |
| **C2 — Orchestrator topologically sorts an unordered set** | Friendlier authoring, but adds runtime graph logic and hides order. Rejected for v1 (revisit if author burden proves real). |
| **C3 — No order guarantee** | Breaks intra-batch deps (`full-ceremony`'s `core`-first requirement) and partial-failure consistency. Rejected. |

**Axis D — whether a profile spans scopes** (exhaustive: a profile either mixes scopes or it doesn't; if it doesn't, it is repo-only or user-only):

| Option | Verdict |
|---|---|
| **D-homogeneous — repo-only *or* user-only, never mixed** ★ | Keeps the two lifecycles separate (per-repo setup vs. cross-project toolkit), self-contained at one scope, no cross-scope partial-failure window. Both kinds shipped. **Recommended.** |
| **D-mixed — one profile spans user + repo** (e.g. `core` + `architect`) | Conflates two lifecycles in one command and reintroduces a cross-scope half-applied-install surface. Rejected — see Problem & goals. |

**Distinguished — meta-pack (not on the axes; a different thing that looks similar).** [ADR-0003](../adr/0003-credential-broker-contract.md) / [RFC-0013](0013-credential-broker-contract.md) option F ("Pack bundling": a pack that depends on its consumer packs) was **rejected** for portability coupling. A profile is *not* a meta-pack: it is an external manifest with no pack→pack hard dependency and no pack identity, so the coupling objection does not transfer.

## Risks & what would make this wrong

**Pre-mortem.**

- *It ships and is just sugar no one reaches for.* Mitigation: scope the v1 surface to two proven profiles (one per scope) and the CLI verbs; adding a profile is a one-file PR, so the cost of being wrong is near-zero and removal is `rm profiles/*.toml` + the flag. If after a release no third profile earns authoring, that is the signal it was sugar — and it cost almost nothing to learn.
- *Profiles drift from reality* (a pack is renamed, removed, or flips scope). Mitigation: the scope-homogeneity + dep-completeness/order lint runs in CI against the live `packs/` tree; a profile naming a non-existent pack, a wrong-scope pack, or a broken dep order fails the build.
- *Silent adapter split.* Mitigated by D5 step 2 — one adapter pins the whole batch, refusing before any write if a pack disallows it.
- *Partial install on I/O failure.* Mitigated by deps-first write order (consistent prefix) + per-pack summary; this is the same residual single-pack install already carries, not a new exposure. The single-scope-per-profile rule (D4) keeps it strictly simpler — there is no cross-scope half-applied state to reason about.

**Key assumptions (falsifiable).**

- *The curated combinations are non-obvious enough to be worth encoding.* This is the substantive-kernel claim. For a repo profile it is strongest: `full-ceremony` encodes both the set *and* the install order (`core` before its three dependents) — genuine executable knowledge, not just a command-count saving. For a user profile it is the role→toolkit mapping. A reviewer's fair attack: each set is a short, same-scope chore that prose (A0) could document well enough. The spike (below) measures the chore; whether the *mapping/ordering* is valuable is the Approver's call, paired with Principle 4.
- *Setup is frequent enough to clear Principle 4.* This is the weakest pillar and the explicit charter call in Decision 1. The frequency argument *for*: setup fires per repo **and** per new team member — for the charter's stated "team of fifty," a profile is reached every time someone joins or a repo is stood up, not once a year. The argument *against* (a fair reviewer position): for a solo adopter it is closer to once-per-repo, and "document the patterns better in prose" (A0) might suffice. There is **no spike for this** — it is an unfalsified frequency assumption, called out plainly rather than dressed up.
- *Claude-plugin/APM users won't feel left out.* If profiles prove valuable, demand to surface them on those routes will appear; v1 deliberately defers that (Open question 2).

**Drawbacks.** It is convenience over an existing capability, not new capability — it adds a (small) CLI surface and a lint to maintain, and it introduces a second way to express "these packs go together" alongside `[pack.dependencies]` (orthogonal in intent — *curated set* vs. *needs* — but a reader must learn the distinction). The first-party-only constraint means an adopter who wants their own bundle still loops `--pack` until the follow-on lands.

## Evidence & prior art

**Spike / de-risk result.** The spike measures the manual chore and confirms both starter profiles install as self-contained single-scope units, against the live catalogue:

- **`solution-architect` (user):** three invocations — `install --pack architect`, `--pack research`, `--pack contracts`. Verified all three are `default-scope = "user"` with **no `[pack.dependencies]`** — self-contained at user scope.
- **`full-ceremony` (repo):** four invocations — `install --pack core`, then `--pack governance-extras`, `--pack user-guide-diataxis`, `--pack monorepo-extras`. Verified `core` is repo-scope with no deps, and the other three are repo-scope and **each declare a catalogue-qualified required dep `{ catalogue = "agent-ready-repo", pack = "core", version = "^0.1" }`** — so `core` must install first or the dep gate (`install.py:3203`) refuses with "install core first." This ordering (and the catalogue-qualified match the dep-completeness lint must reproduce) is exactly the knowledge a repo profile encodes.

Verdict: the spike establishes feasibility, the chore size (3–4 → 1 command), and — for the repo bundle — that real dependency ordering is at stake. It deliberately does **not** claim to settle Principle 2 (whether encoding the combinations is *substantive* vs. *sugar* is the Approver's call, paired with Principle 4). Both are surfaced, not papered over.

**Repo precedent.**

- [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) "Common adoption patterns" (`:668-677`) blesses named pack combinations *as prose* — it literally lists "Plus RFC/ADR ceremony = `core` + `governance-extras`" and "Full ceremony = all four [repo] packs." These *are* repo profiles; this RFC promotes that exact table to an executable unit. RFC-0001's anti-mega-bundle reasoning (`:388-392`) — packs stay independently installable so downstream can depend on specifics — is honored: a profile is a thin pointer list, not a pack, and creates no new dependency edges.
- [RFC-0004](0004-install-scope-per-pack.md) is the conceptual precedent for the user-scope kind: it defines user-scope content as "genuinely cross-project … primitives that travel cleanly across every repo an adopter opens" and names "an IDE-personalisation profile" as the shape (Motivation). A user profile is exactly that — a role's portable toolkit — which (with repo-scope packs being inherently per-repo) is why a profile is single-scope (D4). RFC-0004's `default-scope`/`allowed-scopes` and [RFC-0011](0011-pack-allowed-adapters.md)'s `allowed-adapters` supply the per-pack scope and adapter resolution a profile reuses verbatim.
- [RFC-0031](0031-catalogue-package-manager-posture.md) D1 (`:55-57`): *"No runtime, no server, no daemon… this RFC adds zero primitives. Principle 3 is honored."* This proposal is structurally identical (enrich distribution, zero primitives, zero runtime) and reuses that framing; it also respects RFC-0031's deferred-resolver and no-registry non-goals by staying an explicit, closed, CLI-only list.
- [RFC-0002](0002-self-hosting.md) source-vs-projected split: profiles are hand-authored *source* read by the CLI, never a projected artifact — so self-host and the build pipeline are untouched.

**External prior art** (each fetched and confirmed to contain the cited claim):

- Python **extras** — `pip install 'SomePackage[PDF,EPUB]'` installs a named optional dependency set in one command. [pip install documentation](https://pip.pypa.io/en/stable/cli/pip_install/)
- **dnf groups** — *"Groups are virtual collections of packages"*; `dnf group install <group-spec>`. [dnf command reference](https://dnf.readthedocs.io/en/latest/command_ref.html)
- VS Code **Extension Packs** — *"a set of extensions that will be installed together,"* via the `extensionPack` manifest field. [VS Code extension manifest](https://code.visualstudio.com/api/references/extension-manifest)

Takeaway: "a named set of units installed in one command" is well-established across three independent ecosystems, each implemented as a thin composition layer over an existing per-unit installer — none required new runtime infrastructure. This supports the A1 "hygiene, not infrastructure" framing.

## Open questions

1. **Adopter-authored profiles — when, and where do they live?** *Recommended default:* defer to a follow-on RFC; v1 is first-party only. The hard part is file location (repo-local vs. `~/.agentbundle/`) and name-collision/precedence with curated profiles, none of which is needed to prove the value. · owner: eugenelim · decide-by: after v1 ships and a concrete adopter demand exists.
2. **Surface profiles on the Claude-plugin / APM routes?** *Recommended default:* no for v1 (those formats lack a composition concept); revisit if profiles prove valuable enough that route parity is demanded. · owner: eugenelim · decide-by: post-v1, demand-driven.
3. **Record `install_route="profile"` provenance in state?** *Recommended default:* yes — it aids "how did this pack get here?" debugging and is zero-schema-change (the field already exists on every row), though it costs a one-line write-site change to parameterize the hardcoded literal at `install.py:851`; severable from the core proposal if a reviewer objects. · owner: eugenelim · decide-by: acceptance.

## Follow-on artifacts

Filled in on acceptance. Anticipated:

- ADR — record the "profiles are catalogue-level, CLI-route-only, single-scope (repo-only or user-only, never mixed) curated source files" decision and the meta-pack distinction.
- Spec — `docs/specs/pack-profiles/` for the `profiles/<name>.toml` schema (incl. the `scope` field), the `install --profile` / `list-profiles` CLI surface, the dep-gate batch parameter, and the scope-homogeneity + dep-completeness + order lint.
- Possible later RFC — adopter-authored profiles (Open question 1).
