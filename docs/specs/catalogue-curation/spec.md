# Spec: catalogue-curation pack

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0059, ADR-0048, RFC-0055 (erratum/amendment convention), RFC-0002 (self-hosting)
- **Contract:** none (an agent-primitive pack; no REST/event/BFF surface. Two internal contracts — the strip/substitute transform manifest and the ledger schema — are defined here and in ADR-0048, not under `contracts/`.)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Ship `catalogue-curation` — a repo-scope, opt-in, **domain-agnostic** pack whose user is a *catalogue operator* (the maintainer of this catalogue or of a white-label / domain-repurposed fork). It turns four hand-run curation acts into gated, resumable, reviewable workflows: bring one external primitive in (`assimilate-primitive`), survey a whole external repo into a per-candidate verdict RFC (`assimilate-repo`), justify + scaffold a new pack area (`propose-catalogue-pack`), and export an unbranded or attributed derivative of the catalogue (`export-catalogue`). Success: an operator can curate and fork the catalogue without the private manual playbook, backed by a **fail-closed export verify** (a leak hard-fails the export) and a **barrier-plus-visibility guard** on the engine and credential brokers (a protected-tree change is blocked absent a deliberate exemption and shows up loudly in review) — the honest guarantee per RFC-0059, not cryptographic impossibility.

## Boundaries

### Always do

- Follow existing pack conventions: `.apm/skills/<name>/SKILL.md` layout, agentskills.io frontmatter, disjoint activation descriptions, `pack.toml` + `.claude-plugin/plugin.json` + `README.md`.
- Run (or prompt) `make build-self` after any skill mutates pack sources under `packs/`, and keep projections in sync so the self-coverage / build-check gates stay green.
- Source every export substitution anchor from the declared transform manifest (`0059-notes/strip-substitute-brief.md` distills it), reading identity from `.adapt-discovery.toml` markers + `pack.toml` maintainer email.
- Verify fail-closed on export: the export gate hard-fails unless the four-anchor grep (URL, email, slug, owner) passes for the chosen mode.
- Record the pack's user-scope scratch under `~/.agentbundle/catalogue-curation/` exactly per ADR-0048 (per-run purged ledger + per-source durable marker).
- Run the repo's internal lint suite + SAST/SCA scanners over ingested content before it lands; route all writes through `agentbundle.safety.write_jailed`; fetch URL sources over allowlisted schemes only.

### Ask first

- Adding any runtime dependency (the pack is stdlib-only skills + manifests; a Copybara dependency is explicitly forbidden — patterns only).
- Creating any new top-level directory, or changing the strip/substitute manifest *semantics* (not just adding a declared anchor).
- Any change that would touch `packages/agentbundle/**` behavioral code or `packs/credential-brokers/**` in this repo (requires a separate human-authored RFC).

### Never do

- Author any skill whose documented procedure targets this repo's `packages/agentbundle/**` engine *behavioral* code (resolver/installer/projection/broker modules) or `packs/credential-brokers/**`; the path-gate blocks such a changeset absent the declared exemption carrier (barrier-plus-visibility, per RFC-0059). (Editing the declarative `build/recipes/self-host.toml` include list is permitted — config, excluded from the guard.)
- Ship any upstream identity (URL, email, slug, owner) outside the sanctioned attribution surface in an `export-catalogue` run — white-label mode ships zero, attributed mode only in the declared notice.
- Add Copybara (or any code-moving tool) as a dependency.
- Auto-invoke `propose-catalogue-pack` from `assimilate-repo` — always offer, never spawn.
- Commit the assimilation ledger, or let it travel in an export.
- Append new decisions (new candidates / reversed verdicts) to a **Frozen** source-RFC's Errata — emit a fresh RFC instead (RFC-0055 D3 boundary).
- Land an ingested **hook or script** (executable code) without an explicit human confirm, or write an assimilated primitive's body without first presenting that body for review (body-preserving migration).
- Fetch a URL source over a non-allowlisted scheme (`file:`/`ftp:`/`gopher:`) or reach a private / link-local / cloud-metadata address.
- Perform any `assimilate-*` or `export-catalogue` write outside `agentbundle.safety.write_jailed` / `assert_under` (hand-rolled path handling is forbidden — a traversal or symlink must not escape the jail).
- Launder an anti-pattern into the catalogue: land an ingested primitive that triggers a skill/agent from a script or hook, or that misuses an agent (self-review, over-broad tool grant), without reshaping it to the repo's convention or rejecting it.

## Testing Strategy

- **TDD** — the D6 path-gate logic (which paths trigger, which are exempt); the fail-closed export verify (four-anchor grep, mode-aware, case-insensitive, text-only, literals-only); the ledger/marker schema (append-only, purge-exempt marker, run-ledger free-text ceiling); the URL scheme allowlist + private/link-local/metadata-range + redirect block; and write-confinement via `agentbundle.safety` (a traversing/absolute path or an in-source symlink is rejected, not written outside the jail).
- **Goal-based check** — pack registers (`lint-packs`, `validate`), projects (`build-self --dry-run`), skill frontmatter (`lint-skill-spec`, `lint-agent-artifacts`), the two-hop dependency resolves (install of `catalogue-curation` requires `governance-extras`), the refusal-clause presence lint.
- **Visual / manual QA** — one real end-to-end dry run of `assimilate-primitive` (ingest a sample local skill, land it in a pack, build-self); one `export-catalogue --mode white-label` dry run whose verify gate passes on a clean target and fails on a seeded leak (exercised as an integration test); and one `assimilate-repo` survey whose recorded outcome shows it **produced an RFC file and prompted** the `propose-catalogue-pack` hand-off rather than spawning it (the offer-not-invoke Never-do — verified by observing the run's artifacts + absence of an auto-created pack shell).

## Acceptance Criteria

> **Two classes of AC.** The **checked** items are backed by an executable test,
> a lint, or a verified artifact. The **unchecked** items are **agent-behavior**:
> the skills are LLM-driven prose, so they are verified by a live-agent QA session
> (the Testing Strategy's manual-QA line), not a unit test — they stay open until
> that session runs before merge. Crucially, the *deterministic guardrails* those
> behaviors rely on — SSRF allowlist, write-jail, ledger schema, export verify,
> the D6 guard, collision check — are all tested (unit + integration), so what is
> unverified is the agent's *judgment*, not the safety machinery.

**Pack scaffolding & registration**
- [x] `packs/catalogue-curation/pack.toml` exists: `default-scope = "repo"`, `allowed-scopes = ["repo"]`, `[[pack.dependencies.required]]` on `core` and on `governance-extras` (catalogue `agent-ready-repo`), `[pack.links].documentation` → the per-pack guide.
- [x] `packs/catalogue-curation/.claude-plugin/plugin.json` and `README.md` exist; `README` gives the elevator pitch + links the guide home.
- [x] `catalogue-curation` is added to `build/recipes/self-host.toml` `[recipe.packs].include`, and is **not** listed in any default profile.
- [x] `python -m agentbundle.build lint-packs --packs-dir packs` and `... validate` pass; `... self --dry-run` succeeds; `make build-self` produces the projection with no drift.
- [x] Installing `catalogue-curation` with `governance-extras` present resolves (the first pack-on-non-core dependency); a regression test asserts the two-hop chain resolves and that installing it *without* `governance-extras` fails the dependency gate.

**`assimilate-primitive`**
- [ ] Given a local path or URL to a single skill/agent/hook (or a small bundle), the skill fetches it, diagnoses a destination pack + lifecycle from the *local* CHARTER coverage model, and migrates it to `.apm`/pack convention — or rejects with a stated reason.
- [ ] It previews the plan (files created/moved) before writing, and prompts `make build-self` after writing.
- [x] It refuses a destination under this repo's `packages/agentbundle/**` or `packs/credential-brokers/**` (Never-do).

**`assimilate-repo` (+ ledger + re-sync)**
- [ ] Given a repo/catalogue path or URL, it inventories candidates and assigns each a verdict (`assimilate` | `reject` | `needs-new-pack`), processing iteratively (one reviewable verdict at a time).
- [x] Progress is written to `~/.agentbundle/catalogue-curation/<run-id>/ledger.toml` per ADR-0048 (append-only, per-candidate); `<run-id>` is **deterministic** for a given source — a per-installation salt with **no per-invocation stamp** — so an interrupted run and a sibling worktree derive the *same* run-id: an interrupted run resumes by skipping `done` candidates, and a second worktree appending concurrently reuses the same ledger without clobbering entries.
- [ ] It emits the inventory + verdicts as an RFC (a reviewable proposal), and when any `needs-new-pack` verdict appears it *offers* — never auto-invokes — a hand-off to `propose-catalogue-pack`.
- [x] Re-pointing at a previously-assimilated source is incremental: candidates classify as unchanged (skip) / changed / new against the durable per-source `last-synced` marker; the marker is updated by dated append and is exempt from the run purge.
- [ ] The prior source-RFC records the re-sync using RFC-0055's own forms (RFC-0055 governs corrections *within* an RFC and does **not** define whole-RFC supersession): in-place **Amendment** if the source-RFC is Open; an **Erratum** if Frozen + a genuine correction; and if Frozen + new candidates/reversed verdicts (fresh decisions, not a correction) a **new RFC** is authored, recorded on the prior RFC as **an Erratum entry naming the superseding RFC** (RFC-0055's documented whole-RFC form) — never by appending new decisions to a Frozen RFC's Errata.

**Target-state craft conformance** (both assimilate skills — the migrate step's quality bar)
- [ ] Migration shapes the target state to the repo's **skill-authoring craft** (canonical in `.claude/skills/README.md` § Authoring skills), not just the file layout — a "migrate to convention" AC that means *craft*, not *reformat*:
  - **Activation + no collision:** the `description` is rewritten terse and activation-optimized, and checked for **collision against all existing skills** (disjoint activation) — an overlap is surfaced with the colliding skill named, not silently landed.
  - **Progressive disclosure with deterministic scripts:** detail moves to `references/`, mechanical/repeatable steps to `scripts/`, keeping `SKILL.md` terse — the ingested primitive is reshaped to this, not copied whole.
  - **Fresh-context / human-consumable:** coined terms are glossed for a cold reader; the target reads standalone.
  - **Guided, not flooding:** decision points in the produced skill become *offered choices with prepared context*, never a bare dump on the user.
- [ ] When migration hits a judgment only the operator can make (destination pack, naming, splitting a bundle, an activation collision), the skill **prepares the elicitation context** — what it found, the options, its recommendation — rather than asking a bare question; it guides, it doesn't flood.
- [ ] **Anti-pattern detection + steering (don't launder misuse into the catalogue).** Assimilation detects known misuse patterns in the ingested primitive and either **reshapes to the repo's right shape or rejects** — naming the anti-pattern and its correction. At minimum it catches:
  - **A script or hook that programmatically triggers a skill or agent** — a hard anti-pattern (deterministic scripts stay deterministic; skills activate by description, agents are dispatched by the loop, neither is invoked from a script). Corrected to the right shape or rejected; never landed as-is.
  - **An agent used the wrong way** — an agent that reviews/marks its own output, an over-broad tool grant, or work that should be a skill (or vice-versa) — re-scoped to the repo's agent patterns or rejected.
  - **A "skill" that is a flooding prompt** rather than terse + progressive-disclosure — reshaped, or rejected if it can't be.
  The "right shape" authority is the repo's own conventions (`.claude/skills/README.md` § Authoring skills, the agent-authoring conventions, and `AGENTS.md`); the skill cites the specific rule it steers toward.

**`propose-catalogue-pack`**
- [ ] Given a proposed pack area, it tests additivity + fit against the *local* CHARTER coverage model and the four CHARTER principles; on pass it scaffolds the pack shell and emits an RFC with a per-primitive inventory + verdicts; it can reject the area as non-additive.

**`export-catalogue`**
- [x] Produces a derivative at a target path in mode `white-label` (default) or `attributed`; governance/internal docs are stripped in **both** modes.
- [ ] Substitutes the four anchors from their declared sources (URL + slug + owner from `.adapt-discovery.toml`; email from `pack.toml` maintainer + git config); slug and owner are path/glob-scoped, URL and email blanket.
- [ ] Persists the fork's chosen defaults into the **target copy only**: `scope.py DEFAULT_ADAPTER`, `self-host.toml` `[recipe.adapters].targets` + `[recipe.packs].include`, and blanks `install-defaults.toml` `source` — a bounded re-home transform on declared anchors, never touching this repo's engine.
- [x] The fail-closed verify gate hard-fails the export on any surviving upstream URL/email/slug/owner (mode-aware: zero anywhere in white-label; only in the declared attribution surface in attributed), on a dangling `CLAUDE.md` symlink, or on a non-blank target `install-defaults.toml` source. A seeded leak fails the gate; a clean target passes.

**D6 guard**
- [x] Each skill carries an explicit refusal clause scoped to the *running* repo's protected trees; a presence lint verifies the clause exists (`export-catalogue` carries the scoped target-vs-upstream form).
- [x] A **`build-check` (CI)** path-gate hard-fails a changeset touching `packages/agentbundle/**` engine behavioral code or `packs/credential-brokers/**` **unless** it carries the declared engine/credbroker-scoped exemption reference (a commit-trailer `Engine-Change-RFC:`, readable by CI); `build/recipes/**` is excluded from the gate. The gate lives in `build-check.yml`, **not** the projected `pre-pr.py` hook — which deliberately runs none of the repo's own linters (it's the adopter-facing stub); adopter `pre-pr` wiring is optional, not required. Engine-tree carve-outs (neither is engine behaviour): `build/recipes/**` (declarative config) and `.../tests/**` (additive test coverage, e.g. the two-hop-dependency regression test). `packs/credential-brokers/**` has no carve-out.
- [x] The guard's residual is documented: the path-gate contains *changesets*, but an assimilated **hook executes at session/commit time** and could write a protected tree *before* a diff is gated — so the ingest-time hook confirm (above) is named as its compensating control, not the path-gate.

**Ingest & export security controls** (spec-stage security review, 2026-07-02)
- [ ] **Untrusted-content review before write, then a visible shape transform.** Two sequential steps, not one: **(1) security inspection** — the *raw fetched body* is shown **verbatim** (nothing hidden behind reformatting) for the operator to judge the untrusted content; **(2) craft-shaping** — only after the content is accepted as safe is the target-state reshaped to the repo's skill-authoring craft (see *Target-state craft conformance*), as a **visible transform the operator approves**. The operator sees both what was ingested (raw) and what will ship (shaped). (Supply-chain / LLM-injection: an assimilated skill/agent is instruction prose that projects into the operator's and downstream users' agents — so the raw content is judged before it is trusted, and the shaped result is judged before it lands.)
- [ ] **Ingested code is a higher-scrutiny class.** An ingested **hook or script** (executable code, not prose) is flagged distinctly and requires an explicit human confirm before it lands — it runs on the operator's machine on git/session events.
- [x] **URL-source SSRF confinement.** A URL source is fetched only over an allowlisted scheme (`https`, plus `git`/`ssh` for repo clones); `file:`, `ftp:`, `gopher:` and bare-IP link-local/private/metadata ranges (`169.254.0.0/16`, `10/8`, `127/8`, …) are rejected; redirects are revalidated against the allowlist (or disabled). Repo URLs are fetched via `git clone`/`gh` (which avoids raw-fetch `file://` reads); a single raw file uses an https-only guarded fetch. (No blessed SSRF client exists in the repo to inherit — the control is specified here.)
- [x] **Write confinement via the blessed helper.** All `assimilate-*` and `export-catalogue` writes route through the engine's `agentbundle.safety` (`write_jailed` / `assert_under` — resolve-then-verify-prefix, symlinks resolved first), never hand-rolled path handling — so a traversing/absolute path or a symlink inside a fetched source cannot escape `packs/` (assimilate) or the target root (export). Consuming this helper read-only is the sanctioned reuse posture, not a D6 engine change. The operator-supplied **export target path** is validated (non-empty, not overlapping/nested in the running repo tree) before any write.
- [x] **Export verify honest bounds.** The four-anchor verify is **case-insensitive**, scoped to **text files (binary artifacts out of scope, declared)**, and verifies declared-anchor **literals only** (not case-folded-split/encoded/base64 derived forms) after a normalization pass; the spec states this blind-spot boundary so "leak hard-fails" is not overstated.
- [x] **Ledger free-text ceiling + single-primitive residue.** The run `ledger.toml` schema **bounds/forbids a free-text reason field** (verdict is an enum; no verbatim source content) — the same schema-enforced purity ADR-0048 gives `last-synced.toml`; and `assimilate-primitive`'s fetched-but-rejected content has a named temp location + purge-on-completion, so a single-primitive ingest from a client source leaves no residue.
- [ ] **Ingested code runs the repo's own gates at ingest time.** Before an assimilated primitive lands, `assimilate-*` runs the repo's **internal lint suite** (`lint-skill-spec`, `lint-agent-artifacts`, and the other `build-check` lints that apply to the artifact kind) **and its SAST/SCA scanners** (`.snyk` / dependency scan locally where runnable; CodeQL runs automatically on the PR the change opens) over the migrated candidate — the *same* gates the repo applies to its own code, invoked proactively rather than deferred to the work-loop's `security-reviewer` alone. A lint or scanner failure **blocks the landing** (fail-closed) or is surfaced for an explicit human confirm; ingestion never bypasses these gates. (Reuses existing repo tooling — no new scanner dependency.)

**Docs & bookkeeping**
- [x] `docs/guides/catalogue-curation/` exists (Diátaxis: a tutorial + how-tos for the four skills incl. resume + re-sync + fork-export, reference for the manifest/ledger/guard, explanation of why curation is a pack + the single-authoritative-source model), authored via `new-guide`.
- [x] `docs/product/changelog.md` `[Unreleased]` gains a `catalogue-curation` entry.
- [x] `docs/backlog.md` gains greppable anchors for the deferred Non-goals (`retire-primitive`, `audit-catalogue`) and the ledger stale-run sweep.

## Assumptions

- Technical: email identity lives in `pack.toml [[pack.maintainers]].email` + git config, not in `.adapt-discovery.toml` (four markers: project-name, repo-url, owner, default-branch) (source: probe 2026-07-01).
- Technical: a `catalogue-curation → governance-extras` required dependency resolves compositionally under the existing dependency gate; it is the first pack-on-non-core dependency (source: probe of `install.py` dependency gate + `governance-extras/pack.toml` 2026-07-01).
- Technical: `self-host.toml` lives under `packages/agentbundle/agentbundle/build/recipes/` (inside the engine tree) but is declarative config, so the D6 path-gate excludes `build/recipes/**` (source: probe 2026-07-01).
- Process: RFC-0055 D3 scopes Errata/Amendments to corrections; whole-proposal replacement uses a superseding RFC (source: `docs/rfc/0055-...md` 2026-07-01).
- Product: the pack is a catalogue-operator pack, off by default, cleared CHARTER D1 as a forward bet (source: user confirmation 2026-07-01, RFC-0059 D1).
- Technical: `agentbundle.safety.write_jailed` / `assert_under` is the blessed path-confinement helper (resolve-then-verify-prefix, symlink-foiling) — assimilate/export writes reuse it read-only (source: spec-stage security review + probe 2026-07-02).
- Technical: the repo's internal gates are CodeQL (`.github/workflows/codeql.yml`, SAST), Snyk (`.snyk`, SCA), and the `build-check` lint suite (`lint-skill-spec`, `lint-agent-artifacts`, …); no bandit config is present. Assimilation invokes these existing gates on ingested content and adds no scanner dependency (source: probe 2026-07-02, user direction 2026-07-02).
