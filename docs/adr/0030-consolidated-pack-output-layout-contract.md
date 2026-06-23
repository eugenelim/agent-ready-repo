# ADR-0030: Consolidated, namespaced pack-output layout contract (`agentbundle-layout.toml`)

- **Status:** Accepted
- **Date:** 2026-06-22
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0040 (the accepted decision this records); ADR-0029 (research project mode — introduced `research-layout.toml`, the file this generalises, and the only prior prompt-only-read layout precedent); ADR-0021 (`pack.toml` is the metadata source of truth — home for the `[pack.layout]` extension); RFC-0035 (`references/sso-config.toml` — namespacing + shipped-placeholder delivery, but code-read via `tomllib`, *not* a prompt-only-read precedent); RFC-0034 (`profiles/<name>.toml` config precedent); RFC-0038 (forward-only migration / one-release alias — considered, found not to apply)

## Context

Three output-producing packs each want adopters to control where their durable output lands, and each solves it differently or not at all:

- `research` (project mode) reads an adopter-created `research-layout.toml` to resolve a project corpus parent (ADR-0029) — works, but the config is research-shaped and research-only.
- `architect` re-scans `docs/design/` → `design/` → `architecture/` → `docs/` and offers the first that exists, else elicits — **every run**, with no way to fix the location once.
- `product-engineering` hardcodes `docs/product/…`, so an adopter who keeps product docs elsewhere must fork the skill.

Left alone, each pack grows its own `*-layout.toml`, and an adopter customising three packs juggles three files with three schemas. The config *shape* is the cheapest to fix now: the only existing instance (`research-layout.toml`) shipped in `research 0.4.0`, which landed **after** the last release (`agentbundle-v0.6.0`, 2026-06-21) and so is **undistributed** — no adopter holds one, and the migration is free only this release.

Constraints in force when deciding:

- **Charter Principle 3 (a habit, not infrastructure).** A skill reads config as a prompt-driven file operation. No runtime engine, index, daemon, or watcher may read the file while a skill operates.
- **Charter Principle 1 (universal across stacks).** The contract ships to every adapter; it cannot hardcode one project's storage layout.
- **A repo-root config that overrides a user default crosses a trust boundary.** An adopter who clones an untrusted repo and runs a consumer skill has the skill read an attacker-authored `./agentbundle-layout.toml` whose `parent` can point anywhere (the user-profile file is foot-gun-only — the adopter authored it; the repo-root layer is the untrusted-origin case). Because the reader is prompt-only, the control cannot be a code path-validator.

## Decision

> We will replace the research-only `research-layout.toml` with one namespaced **`agentbundle-layout.toml`** that every output-producing pack reads — one `[<pack>]` table each, whose single `parent` key names a **base directory under which each unit of work gets its own topic-named folder**.

Elaboration and boundaries:

- **One file, `[<pack>]` tables, one resolution rule.** Two locations with precedence — a repo-root `./agentbundle-layout.toml` **overrides** a user-profile `~/.agentbundle/agentbundle-layout.toml`, **per table** (the repo file's table is used whole; a table only in the user file survives). `research`, `architect`, and `product-engineering` are the three consumers wired in one implementing spec.
- **`parent` is a base, not the leaf.** The skill creates a topic-named child folder per unit of work using its own naming convention (`research` → `<parent>/<YYYY-MM-DD>-<topic-slug>/`; `architect` → `<parent>/<topic-slug>/`, a folder around what was a loose file; `product-engineering` → file-per-slug under `<parent>/{intents,rollups}/`, the deliberate exception).
- **`parent` is anchored by the layout file's own location.** A repo-root file's `parent` is repo-root-relative (portable across clones); a user-profile file's `parent` must be an explicit absolute (`~`-anchored) path. The skill always resolves to, and **surfaces, the full absolute path before the first write** (realpath-resolved, `~`-expanded, `..` rejected), and treats a repo-root-sourced `parent` resolving outside the repo as an untrusted-origin, Ask-first deviation.
- **Reading is prompt-only (Principle 3, hard boundary).** A skill body reads the file; **writing** is install-time code only — the `agentbundle` installer gains an **append-if-exists, never-overwrite, never-create** step (peer to the existing install-marker upsert) sourcing each pack's default from a scope-keyed `[pack.layout]` table in `pack.toml` (ADR-0021), serialised through the injection-safe emitter and written via the path-jailed atomic write.
- **The file is adopter-owned and never shipped as a projected artifact.** It exists only on an adopter's machine — hand-written, skill-scaffolded on consent, or installer-maintained. The shipped artifacts are each pack's `references/agentbundle-layout.md` schema doc and the within-pack `[pack.layout]` default; the **active** file never lives under `packs/`.
- **Migration is a clean rename, no alias.** `research-layout.toml`'s top-level `parent` becomes the `[research]` table's `parent`; because `research 0.4.0` is undistributed there is nothing in the wild to be backward-compatible with (RFC-0038's one-release-alias pattern was considered and found not to apply). Falsifiable: if a release cuts `research 0.4.0` before the implementing PR merges, the migration reverts to a one-release alias.
- Scope: this records the *contract*. Specs (`docs/specs/`), ADRs, RFCs, contracts (`contracts/<type>/`), and packages (`packages/`) stay at fixed locations — discovery and governance depend on them; only the three named packs' relocatable output is in scope.

## Decision drivers

- **Prompt-only / habit-not-infrastructure (Principle 3)** — the hard gate; rules out any runtime reader/engine for the file, forcing the security control to be prose-enforced acceptance criteria rather than a code jail.
- **Universality (Principle 1)** — rules out hardcoding a layout; the file supplies a `parent`, and each pack's default and posture stay in its own skill body (so "never the committed tree" is a research-specific default, not a property of the shared file).
- **Free migration window** — `research-layout.toml` is undistributed; consolidating now costs zero migration, and the window closes at the next release. This drove *now* over *later* and *clean rename* over *alias*.
- **Namespace as structure, not convention** — a `[<pack>]` table is the natural per-pack scope and the natural per-table override unit, and lets a prompt-only reader "read/scaffold only my section" cleanly; rules out flat prefixed keys (`research_parent`).
- **Adding the next consumer is a table, not a migration** — the contract degrades gracefully (a pack with no adopter section uses its default), so the cost of being wrong about a consumer's demand is low.

## Consequences

**Positive:**
- One file, one resolution rule, one precedence story; an adopter customising N packs edits one file. The next consumer is a `[<pack>]` table.
- `parent`-as-base with a per-unit topic folder gives a tidy `efforts/research/<topic>/` + `efforts/architecture/<topic>/` tree and ends `architect`'s every-run re-elicitation.
- The prompt-only-read boundary is preserved exactly as ADR-0029 set it; nothing new runs while a skill operates.

**Negative:**
- A shared contract is one more governed surface; the installer gains a step and `pack.toml` gains an optional table that bumps the manifest schema and touches its validator, and this repo's `.gitignore` gains the file (one-repo only; adopters ship no gitignore rule, and the migration updates the `docs/product/changelog.md` `[Unreleased]` entry that names `research-layout.toml`).
- `architect`'s output changes from a loose file to a per-effort folder — a deliberate, additive shift (a platform has many architecture topics and no single doc can carry them), documented in the spec, not silent.
- The repo-root-overrides-user precedence is the right ergonomic choice but is exactly the untrusted-origin surface; the mitigation lives in prose acceptance criteria, which are weaker than a code jail and depend on the reviewer pass to hold. **The decision-maker accepts this residual risk** because Principle 3 forecloses a code jail on the read path; exposure is bounded by the surface-the-resolved-absolute-path-before-write AC and the untrusted-origin Ask-first rail, and is reviewer-enforced (spec-stage and diff-stage security review). A prompt-only realpath/`..`-rejection rail is moreover *advisory* — a model may surface a lexical path without resolving a symlink — so the AC16 behavioural smoke is the only enforcing check, and an unresolved-symlink escape is an accepted residual of the prompt-only boundary.

**Neutral / to revisit:**
- **Per-table override** coincides with per-key merge only while each table is single-key (just `parent`). If a table ever grows a second key, the documented fallback is the per-key merge that npm/Cargo use — a superseding decision, not an edit here.
- **The three-consumer scope rests on a load-bearing assumption** — that `architect` and `product-engineering` are genuine relocation needs (Approver-confirmed, but the code survey found only `research` with an existing config). If demand is softer than stated, the contract still degrades gracefully — a pack with no adopter section uses its default — so over-fit risk is low; this is the assumption to re-check before adding a fourth consumer.
- `receive-brief` / `decompose-intent`'s `docs/product/briefs/` output stays pinned even when `product-engineering` relocates its `intents/`/`rollups/`. Core can opt in as a `[core]` consumer in a later RFC if a need appears.

## Confirmation

- The implementing spec's acceptance criteria encode the file contract, the two-location resolution, the anchoring rule, and the prompt-only constraint; adversarial + quality review checks that no runtime reader/engine creeps in.
- The four security acceptance criteria (confine + reject `..` + surface the resolved absolute path; realpath so symlinks are visible; repo-root-sourced out-of-tree `parent` is untrusted-origin Ask-first; the installer append round-trips a hostile default through the injection-safe emitter and never overwrites an existing section) are checked by the spec-stage and diff-stage security-reviewer pass.
- The manifest-schema/validator update and the contract-version bump are an explicit spec task carrying the lexical-version-compare and CI-ungated-test-root traps recorded in repo memory.

## Alternatives considered

- **Do nothing** (research keeps `research-layout.toml`; architect keeps re-eliciting; product-engineering stays hardcoded). Rejected against the *free-migration-window* driver — the next pack repeats the question, proliferation sets in, and the zero-cost window closes at the next release.
- **Per-pack files** (`research-layout.toml`, `architect-layout.toml`, …). Rejected against the *one-file* goal — an adopter customising N packs juggles N files/schemas with no shared precedence story.
- **One shared file, flat prefixed keys** (`research_parent`, `architect_parent`). Rejected against *namespace-as-structure* — the namespace lives in a key-name convention rather than structure, making "read only my section" and per-table override harder for a prompt-only reader.
- **A one-release `research-layout.toml` alias for migration** (RFC-0038 pattern). Rejected against *free-migration-window* — `research 0.4.0` is undistributed, so there is nothing in the wild to be backward-compatible with.
- **A runtime config reader/engine** to centralise resolution. Rejected against *Principle 3* — that is infrastructure; reading stays in the skill body, and only the install-time append is code.

## References

- RFC-0040 — A consolidated, namespaced pack-output layout file (the accepted decision this ADR records).
- ADR-0029 — Research pack structure (introduced `research-layout.toml`, the prompt-only-read layout precedent this generalises).
- ADR-0021 — `pack.toml` is the metadata source of truth (home for the `[pack.layout]` extension).
- RFC-0035 — `references/sso-config.toml` (namespacing + shipped-placeholder delivery; code-read, not a prompt-only-read precedent).
- Charter Principle 3 — a habit, not infrastructure (the prompt-only hard boundary the reader respects).
