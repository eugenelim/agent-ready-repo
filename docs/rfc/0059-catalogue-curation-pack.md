# RFC-0059: The catalogue-curation pack

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-01
- **Date closed:** 2026-07-01
- **Decision weight:** heavy <!-- stands up a new pack (structural) and crosses a confidentiality/scrubbing boundary (white-label export) -->
- **Related** (RFC = request-for-comments proposal; ADR = architecture-decision record): RFC-0001 (bundle distribution + build pipeline), RFC-0002 (self-hosting), RFC-0003 (adapter contract + reference CLI), RFC-0031/ADR-0021 (pack manifest, lossy projection), RFC-0034 (pack profiles — a curated default-install pack set), RFC-0046 (install-source resolution), RFC-0055 (RFC erratum/amendment convention — how a published RFC records later corrections, reused on re-sync), ADR-0002 (per-pack install scope); the `frame-intent` skill's `capability` *altitude* — its product-intent zoom level, one rung of product-vision → strategy → capability → feature (terminology collision, Decision 2)

## Reviewer brief

- **Decision:** Add a repo-scope, opt-in **`catalogue-curation`** pack — four skills that ingest external agent primitives into this catalogue and export unbranded derivatives of it.
- **Recommended outcome:** accept.
- **Change if accepted:** (1) new `packs/catalogue-curation/` with four skills; (2) a resumable **assimilation ledger** under `~/.agentbundle/catalogue-curation/`; (3) a mechanical guard forbidding writes to `packages/agentbundle/**` and `packs/credential-brokers/**`.
- **Affected surface:** new pack + its skills; `self-host.toml` include list (the recipe listing which packs this repo projects onto itself); one new lint + one CI path-gate; a new user-scope scratch path; follow-on ADR (architecture-decision record) for the ledger schema. **No change to `agentbundle` engine *behavior*** (resolver/installer/projection/broker code) or `credential-brokers` (the secret-resolving pack, aka credbroker) — the only engine-tree touch is one `self-host.toml` include entry (a declarative recipe edit, exactly like every pack addition).
- **Stakes:** costly-to-reverse (a shipped pack acquires users; the export path touches confidentiality both outbound *and* inbound). Not a one-way door — the pack is opt-in and removable.
- **Review focus:** (1) does a catalogue-operator pack clear the CHARTER's four principles — *universal across stacks · substantive not duplicative · a habit not a tool · used often enough to stick* (Decision 1, esp. the last)? (2) is the export **fail-closed** enough to never leak outbound, *and* is the ledger's inbound residue contained (Decisions on export + D7)?
- **Not in scope:** any change to *this repo's* `agentbundle` engine behavior or the credential brokers (export *does* patch a **target copy's** declared anchors — see the D6 guard note); a retirement/deprecation skill (deferred — see Non-goals); a runtime multi-repo workspace or daemon.

## The ask

**Recommendation (BLUF):** Approve a new opt-in, repo-scope pack **`catalogue-curation`** carrying four skills — `assimilate-primitive`, `assimilate-repo`, `propose-catalogue-pack`, `export-catalogue` — that turn today's hand-run catalogue-maintenance into gated, resumable, reviewable workflows. The pack is **domain-agnostic catalogue infrastructure**: it grows, forks, and re-purposes *any* agent-skill catalogue, of which this repo's software-delivery (SDLC — software development life cycle) catalogue is the first instance.

**Why now (SCQA):**
- *Situation.* This repo is a **catalogue** — a set of independently-installable **packs** (a pack = a bundle of agent **primitives**: skills, subagents, hooks, commands) consumed by adopters via package managers or a CLI (RFC-0001/0002/0003). Each pack's source lives under `.apm/` (the tool-neutral primitive source) and is *projected* — mechanically rendered into each editor's native layout — by the `agentbundle` build engine; `make build-self` **projects the packs into this very repo** ("self-hosting"), so the catalogue runs on its own output and the `self-coverage`/`build-check` gates fail if a projection drifts from its source.
- *Complication.* Growing the catalogue (pulling in a good skill someone else wrote), proposing a new pack, and producing an unbranded fork of the whole catalogue are all done **by hand** today — the maintainer runs a private, step-by-step migration playbook with no resumability, no idempotency, and a manual "did any branding leak?" grep at the end. Long jobs (assimilating a whole repo) have no stop/start mechanics.
- *Question.* Should the catalogue carry **its own curation tooling** as a first-class, opt-in pack — and if so, how do we make ingestion resumable and export leak-proof without a new engine or a heavyweight dependency?

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Ship this as a pack at all, and to whom? | **Opt-in, repo-scope, catalogue-operator pack** (requires `core` + `governance-extras`; excluded from default profiles) | Only option that lets the export/assimilate skills travel into a fork (so it can self-curate) while keeping the general-adopter surface clean | this review | Confirm it clears the four CHARTER principles for its audience |
| D2 | Umbrella noun for an ingested unit? | **"primitive"** (drop "capability") | `capability` is a defined intent *altitude* in `frame-intent`; `primitive` is already the repo's word for skills/agents/hooks | this review | Confirm |
| D3 | Skill roster | **Four** skills (merge original ingest #1+#4) | Fetch-and-fit is one act; source-first vs. justification-first stay distinct for activation | this review | Confirm |
| D4 | Pack name | **`catalogue-curation`** | British spelling matches the `catalogue =` contract field; avoids "-tools" (vs. "a habit, not a tool") | this review | Confirm |
| D5 | Deployment / projection | **Self-projecting repo-scope pack**; cross-repo ops take a path/URL arg | No runtime multi-repo infra (out of charter); reuses the existing self-host model | this review | Confirm |
| D6 | Engine/credbroker guard | **Two layers**: presence-linted refusal clause + a `pre-pr`/`build-check` **path-gate** on the two protected trees (change there requires an engine/credbroker-scoped RFC) | A lint can't adjudicate LLM prose; gating the *destination path* enforces "never through this pack" regardless of what wrote the diff | this review | Confirm the barrier-plus-visibility guarantee (not cryptographic impossibility) is sufficient |
| D7 | Long-running ingest resumability + inbound confidentiality | **Resumable ledger** at `~/.agentbundle/catalogue-curation/<run-id>/`, per-candidate append-only, keyed on stable identity; `<run-id>` hashed, minimal fields, cleanup/expiry contract | Copybara's state-in-destination pattern, hardened against its history-rewrite fragility; the ledger is also unscrubbed inbound residue, so it gets a retention contract | this review | Confirm the scratch location, the confidentiality/retention contract, + schema-in-ADR plan |
| D8 | Other curation tools now? | **No** — record `retire-primitive`/`audit-catalogue` as Non-goals | Rare or duplicative of existing lints; build on demand | this review | Confirm |

## Problem & goals

**Diagnosis.** The catalogue has a *build* side (author a primitive → project it to adapters) and a *governance* side (RFC → ADR → spec), but **no curation side**: no supported way to (a) bring an external primitive *in*, (b) survey a whole external repo for ingestion candidates, (c) justify and scaffold a new pack area, or (d) emit an unbranded, re-purposable derivative of the catalogue. Today (a)–(d) are a private hand-run playbook. The two grounding sweeps for this RFC confirmed: **no ingest/assimilate/import or white-label tooling exists in the tree** — only the manual playbook and the identity-marker substitution (`.adapt-discovery.toml`) that a fork fills in.

**Goals.**
- Make catalogue growth (ingest one primitive; survey a repo) and forking (export an unbranded derivative) **gated, resumable, and reviewable** — the repo's step-gated style, not a batch tool.
- Keep the machinery **domain-agnostic**: the same skills grow an SDLC catalogue, a creative-writing catalogue, or an investment-research catalogue. Fit-tests read the *local* CHARTER, never a hardcoded SDLC taxonomy.
- **Never** mutate the `agentbundle` engine or the credential brokers through these skills; **never** leak upstream branding or catalogue-governance into an export.
- Introduce **no new engine, scheduler, or service** — skills + declarative manifests only (consistent with this catalogue's existing no-engine "loops" — the discovery loop and release loop, both of which coordinate work purely through skills + files, with no runtime service).

**Non-goals.**
- **A retirement/deprecation skill** (`retire-primitive`, `deprecate-pack`) — the honest counterpart to assimilation, but rare; build it when the need is real, not speculatively.
- **A catalogue-audit skill** (`audit-catalogue`) — cross-pack duplicate/activation-collision detection largely duplicates existing lints (`conventions-check`, `self-coverage-gate`); not additive.
- **Modifying *this repo's* `agentbundle` engine or `credential-brokers`** — out of bounds by construction (D6). Any such change is a separate, human-authored RFC. (Export's bounded re-home transform on a *target copy*'s declared anchors is the sole exception, scoped to the export target, never this repo — see the D6 guard note.)
- **A runtime multi-repo workspace, daemon, or scheduler** — that is runtime infrastructure, which the CHARTER excludes (precedent: the browser-bridge design, ruled out of charter on the same principle).
- **Adopting Copybara (Google's code-moving tool) as a dependency** — we mine its *patterns* only (see Evidence).

## Proposal

A new pack `packs/catalogue-curation/`, `default-scope = "repo"`, `allowed-scopes = ["repo"]`, requiring `core` and `governance-extras`, **not** in any default profile, added to `self-host.toml`'s `include` list so it projects into this repo. Four skills:

> **First-of-its-kind dependency (flagged).** Every existing pack that declares a dependency depends only on `core`; `catalogue-curation → governance-extras` is the catalogue's first pack-on-a-non-core-pack dependency. It's required because two skills *emit RFCs*, which are a `governance-extras` construct. It resolves compositionally under the existing dependency gate — each pack's install gate checks its own direct deps, and `governance-extras` already gates `core`, so the two-hop chain holds without new resolver logic. The spec will add a regression test asserting the two-hop install resolves.

### 1. `assimilate-primitive`
Ingest **one** primitive — a single skill, subagent, hook, command, or a small connected bundle (e.g. a skill + its hook + a script) — from a **local path or URL**. Steps: fetch → identify what it is → **diagnose destination** (which existing pack, at which lifecycle stage) by reading the local CHARTER's coverage model → **migrate to `.apm`/pack convention** (frontmatter, layout, references, evals scaffold) → or **reject with a reason**. Ends by prompting `make build-self`. Refuses any destination under `packages/agentbundle/**` or `packs/credential-brokers/**` (D6). Previews the plan before writing (dry-run).

### 2. `assimilate-repo`
Point at a **whole external repo or catalogue** (path or URL). Inventory every ingestion candidate; assign each a **verdict** — `assimilate` (→ names the destination pack), `reject` (→ reason), or `needs-new-pack`. Process candidates **iteratively** (one reviewable verdict at a time), writing progress to the **resumable ledger** (D7) so the job survives interruption, session end, or a switch of coding harness, and so **parallel git worktrees** can share the run. Emits the inventory + verdicts as an **RFC** (a reviewable proposal, not a silent commit). When any `needs-new-pack` verdict appears, it **offers** — never auto-invokes — a hand-off to `propose-catalogue-pack`.

**Re-assimilation (incremental re-sync + migration log).** Pointing at a source that was assimilated before is an **incremental sync**, not a fresh run (Copybara's incremental-import model): the ledger's stable-identity + content-hash entries classify each candidate as *unchanged* (skip), *changed* (re-surface for a verdict), or *new*, so only genuine deltas are re-reviewed. Sync tracking:
- **Time-of-sync record = the git commit log.** Each sync lands as commits, so the commit log *is* the timestamped migration history — no parallel bespoke log. Backing it, the durable per-source **`last-synced` marker** (see the ledger section — separate from the purged per-run ledger) tells the next re-sync what to diff against.
- **How the re-sync is recorded depends on whether it's a *correction* or a *new decision*** — respecting RFC-0055 D3's scope boundary (its Errata/Amendment mechanism is for corrections *within* an RFC and additive record-fixing; *whole-proposal replacement* is out of scope and handled by a superseding RFC):
  - *Still-Open source-RFC* → record the delta **in-place as an Amendment** (the convention's in-flight case), regardless of whether it's a correction or new candidates — the proposal is still being worked.
  - *Frozen (Accepted/Rejected) source-RFC, genuine correction* (a verdict typo, a moved destination) → an **Erratum** entry, additive, per RFC-0055.
  - *Frozen source-RFC, but the re-sync introduces new candidates or reverses verdicts* → this is fresh proposal content, **not** a correction, so emit a **fresh RFC** (and drop a superseding-RFC Erratum entry on the prior one, per RFC-0055's own whole-RFC path). Never append new decisions to a Frozen RFC's Errata.

### 3. `propose-catalogue-pack`
Justification-first. Given a proposed pack area (a vendor ecosystem, a company stack, a new domain), test whether it is **additive and fits *this catalogue's* declared coverage model** (read from the local CHARTER — SDLC coverage here, a different model in a re-purposed fork) and clears the four CHARTER principles. If it passes: scaffold the pack shell (`pack.toml`, `.claude-plugin/plugin.json`, `README.md`, empty `.apm/`) and emit an **RFC** with the per-capability inventory + verdicts. Can **reject** the pack as non-additive. Consumes `assimilate-repo`'s output when chained.

### 4. `export-catalogue`
<!-- renamed from `export-white-label`: white-label is now one *mode*, not the whole skill — see Open question 1 -->
Produce a **redistributable derivative** of the catalogue at a target path. Two supported uses — **(a)** an organization rebrand; **(b)** a domain re-purposing (a non-SDLC catalogue — creative writing, investment research, legal, …) — under **two attribution modes**:
- **`white-label`** (default): strip *all* upstream identity — zero trace. For private/org forks and any derivative that must not leak provenance.
- **`attributed`**: strip catalogue-governance and colliding branding, but **preserve a declared attribution-back** to the upstream catalogue (a controlled `NOTICE`/README credit block naming the upstream, e.g. "derived from `<upstream>`"). This is the **ecosystem-growth lever** — a public domain-repurposed catalogue can credit its origin so the ecosystem compounds. Attribution lives **only** in the sanctioned notice surface, never scattered.

Mechanism (both modes):
- **Strip** (deny-by-default, mode-independent): catalogue-governance-about-itself (`docs/rfc/`, `docs/adr/`, `docs/specs/`, `docs/backlog.md`), the repo's own working `CHARTER.md`/`CONVENTIONS.md`/`AGENTS.local.md`, the internal doc site, build/scan/release tooling — per the declared strip manifest. **Governance and internal docs are stripped in *both* modes** — attribution never re-admits them.
- **Substitute** identity anchors, each declared in the transform manifest with its **source** and its **scope** (full anchor set in [`0059-notes/strip-substitute-brief.md`](0059-notes/strip-substitute-brief.md)). Sources are the running catalogue's *own* declared identity, so shipped tooling carries no hardcoded upstream literal:
  - **Full repo URL** — source `.adapt-discovery.toml [markers].repo-url` (`.adapt-discovery.toml` = the repo's install-time marker file, whose `[markers]` table a fork fills with its own identity). **Blanket-safe** (compound).
  - **Full maintainer email** — source `pack.toml [[pack.maintainers]].email` + git config. **Blanket-safe** (compound). *(There is no email marker in `.adapt-discovery.toml`; the four markers are `project-name`, `repo-url`, `owner`, `default-branch` — email is sourced from the maintainer field, not invented as a marker.)*
  - **Slug** (`project-name`) — source `.adapt-discovery.toml [markers].project-name`. **Not blanket-safe:** path/glob-scoped **and coupled** to every `pack.toml catalogue =` field + test fixtures (a slug is a contract value; a bare-token blanket replace corrupts unrelated text — the playbook's explicit rule).
  - **Owner** (bare) — source `.adapt-discovery.toml [markers].owner`. Path/glob-scoped, not blanket.
- **Include-set:** the operator picks which packs travel (drop SDLC packs for a creative-writing catalogue; always keep the engine, a core, and `catalogue-curation` itself so the fork can self-curate).
- **Persisted fork defaults (remembered forever, not per-machine).** The export bakes the fork's own distribution defaults into the *target copy* so every future user of that fork inherits them without a command:
  - **Default adapter** — patches the target copy's `scope.py DEFAULT_ADAPTER` (the playbook's sanctioned rebrand lever; today `install-defaults.toml` carries no adapter field, so the constant is the only distribution-wide lever). A per-machine `config set adapter` still overrides at runtime; this sets the fork's *default*.
  - **Self-host set** — writes the target's `self-host.toml` `[recipe.adapters].targets` (which adapters the fork projects onto itself) and `[recipe.packs].include` (which packs), and blanks `install-defaults.toml` `source` so the fork never defaults to the upstream URL.
  These are a **bounded, declared re-home transform allowlist** applied *only to the target copy* — they are not edits to the running catalogue's engine, so they do not trip the D6 guard (which protects *this* catalogue's engine tree; see the guard note). The full anchor+transform set is in [`0059-notes/strip-substitute-brief.md`](0059-notes/strip-substitute-brief.md).
- **Verify (fail-closed, mode-aware):** end with a **mandatory** gate that **hard-fails** the export — grep for surviving upstream **URL, email, slug, and owner** (the same **four** anchors the substitute step rewrites, so verify and substitute agree; owner is only *scope*-substituted but must still be *verified*, because it ships as a bare `[[pack.maintainers]] name` in always-kept packs), plus dangling symlinks and a non-blank install-source (`install-defaults.toml` `source`, which must be blank in a fork so it never defaults to the upstream URL). In `white-label` mode **zero** upstream URL/email/slug/owner may survive anywhere; in `attributed` mode they are permitted **only** inside the declared attribution surface. This promotes the playbook's manual "Closing checks" into an enforced step.

### The resumable ledger (D7)
`~/.agentbundle/catalogue-curation/<run-id>/ledger.toml`. **Per-candidate append-only entries** (`path`, `name`, `content-hash`, `verdict`, `status`, `destination`) so concurrent worktrees don't clobber each other and a re-run (any worktree, any harness) resumes by skipping done candidates. Distinct from the per-run ledger is a **per-source `last-synced` marker** (`~/.agentbundle/catalogue-curation/sources/<source-hash>/last-synced.toml`) — a *durable, cross-run* record of a source's last content baseline that the next re-sync diffs against. It is scoped per source (not per run), written as dated append entries (never overwritten), and is **exempt from the per-run completion purge** — reconciling "the run ledger is append-only + purged" with "re-sync needs a surviving baseline." State is keyed on **stable identity** (path + name + content hash), never commit SHAs (Git commit identifiers — fragile under history rewrite). Schema pinned by a follow-on ADR.

**Ledger confidentiality & retention (the inbound residue).** The ledger is the *inbound* counterpart to the export's *outbound* scrub: assimilating from a private or client repo durably records that repo's structure and the maintainer's rejection reasons in a user-global scratch that no export scrub touches and no repo `.gitignore` governs. Contract:
- `<run-id>` is a **hash** of the source URL/path, so the directory name does not disclose the source *in plaintext*. (An unsalted hash of a low-entropy input like a git URL is confirmable by guessing, not secret — a salted/keyed derivation if stronger confidentiality is needed is deferred to the ledger ADR.)
- Recorded fields are the minimum needed to resume; rejection reasons are terse, no verbatim source content.
- A **cleanup/expiry** contract: `assimilate-repo` offers to purge a run's ledger on completion, and a stale-run sweep is documented; the run ledger is never committed and never travels in an export. (The durable per-source `last-synced` marker is exempt from this purge — it holds only a content baseline + dates, no surveyed content or rejection reasons.)
- This is an explicit decision, not silence — see D7 and the pre-mortem.

### The engine/credbroker guard (D6)
A skill body is LLM-executed prose; a lint cannot adjudicate whether prose "sanctions a write" (the credentialed-lint substring trap in this repo's history is the cautionary case). So the guard is **two honest layers**, not one theatrical one:
1. **Behavioral (presence-checked):** each skill carries an explicit refusal clause in its anti-patterns naming the two protected trees, scoped to the **running repo's** engine tree. A lint checks the clause is **present** (a structural fact a lint *can* verify) — it does not claim to prove the prose is obeyed. **`export-catalogue` carries the scoped form**: it refuses to write the *running* catalogue's `packages/agentbundle/**` / `packs/credential-brokers/**`, while its sanctioned re-home transforms on a *target copy*'s declared anchors are explicitly excepted (the target-vs-upstream carve-out below). The follow-on spec's clause-presence lint recognizes this scoped form rather than requiring an unqualified blanket refusal that would contradict `export-catalogue`'s own job.
2. **Mechanical backstop (the real gate):** a `pre-pr`/`build-check` path-gate hard-fails any changeset that touches the engine's **behavioral code** — the resolver/installer/projection/broker modules — or `packs/credential-brokers/**`, **unless** the change carries an explicit engine/credbroker-scoped RFC reference. **Scope carve-out:** the gate **excludes** `packages/agentbundle/agentbundle/build/recipes/**` — the declarative build recipes (`self-host.toml`, `marketplace.toml`, `per-pack-*.toml`) that ordinary pack work edits (adding *any* pack to `self-host.toml`'s include list touches this path, including RFC-0059's own follow-on). The gate protects engine *behavior*, not engine *config*. This protects the behavioral trees *regardless of what wrote the change* — a `catalogue-curation` skill, an operator, or the LLM at runtime cannot land a behavioral-code change there without deliberate, human-authored ceremony. **Exemption carrier:** the engine/credbroker-scoped RFC reference travels as a **commit trailer** (or an in-diff marker) — readable by *both* the local `pre-pr` hook and CI, since a `pre-pr` hook cannot read a PR body; the exact carrier is pinned in the follow-on spec.

**Honest residual:** for LLM-driven skills the guarantee is *barrier + visibility*, not cryptographic impossibility — layer 2 makes a forbidden change require a separate RFC and show up loudly in review; it does not make the write physically impossible mid-session.

**The guard protects the *running* catalogue's engine, not a forked copy.** `export-catalogue` re-homes the engine into a *target* fork and applies a **bounded, declared re-home transform allowlist** to that copy — URL/email/slug substitution, blank `install-defaults.toml` source, set `scope.py DEFAULT_ADAPTER`, set `self-host.toml` targets/include (the persisted fork defaults). These touch the *target* tree at *declared anchors only*, never the upstream engine, and never arbitrarily — so they are sanctioned re-home transforms, not the "change to `agentbundle`" the D6 guard forbids. The guard's path-gate is scoped to `packages/agentbundle/**` and `packs/credential-brokers/**` *within this repo*, not to an export target path.

### Discovery & upskilling (how a maintainer learns the pack)
Curation is a new discipline for most operators — and a fork inherits it **cold** — so the pack must teach itself. Four discovery surfaces, in order of first contact:
- **Skill activation descriptions** — the first-contact surface: each skill's `description` is written so an operator's natural phrasing ("bring in this skill from a URL", "survey this repo for things we can adopt", "make an unbranded copy for our org") activates the right skill, and the roster is mutually disjoint (no cross-activation). The sharpest boundary is `assimilate-primitive` vs. `assimilate-repo`: the former activates on **one named unit at a location** (single fetch-and-fit, no ledger, no RFC); the latter on **surveying a whole repo/catalogue** (many candidates → ledger-backed iteration → an emitted RFC). `assimilate-repo` may *reuse* single-unit ingest internally, but the human triggers them for different jobs — this is why the 5→4 merge folds #1+#4 (two framings of one single-unit act) yet keeps single-unit and survey distinct.
- **Pack `README.md`** — the elevator pitch: what curation is, the four skills as one workflow (ingest → survey → propose pack → export), and a link to the guide home.
- **`pack.toml` `[pack.links].documentation`** → the per-pack **guide home** (`docs/guides/catalogue-curation/`), following the repo's Diátaxis convention. Because per-pack guides **ship with the pack** (playbook Module 7 keeps them; only catalogue-governance docs are stripped), a fork's operators get the same upskilling material.
- **The guide set itself** (Diátaxis quadrants): a **tutorial** (a maintainer's first end-to-end assimilation of one primitive); **how-tos** (survey a repo, propose a pack, export a white-label/re-purposed fork, resume an interrupted assimilation); **reference** (the strip/substitute manifest, the ledger schema, the engine/credbroker guard); an **explanation** (why curation is its own pack, the single-authoritative-source model, and why export is fail-closed).

### Migration path
No existing state to convert. The private manual playbook becomes the source material for the strip/substitute **declared manifests** (repo-owned reference files) — parameterized on markers, so nothing catalogue-specific ships. The playbook is retired once the skills reach parity.

## Options considered

**Axis: where the curation capability lives** (D1) — exhausts the placement space from "nowhere formal" to "shared everywhere":

| Option | What it is | Trade-off | Verdict |
| --- | --- | --- | --- |
| Do nothing | Keep the hand-run playbook | Zero build cost; but the cost of delay *is* the playbook — un-versioned, non-resumable, manual leak-check | Rejected |
| Repo-local skills only | Skills that live only here, never distributed | Simplest; but the white-label requirement forces the export/assimilate skills to **travel** into a fork so it can self-curate | Rejected |
| Fold into `governance-extras` | Add the skills to the existing governance pack | No new pack; but pollutes a general-adopter pack with operator machinery most adopters never touch | Rejected |
| **New opt-in `catalogue-curation` pack** | Repo-scope, requires core+governance-extras, off by default | Satisfies the travel requirement, keeps the adopter surface clean, matches the `governance-extras` precedent one meta-level up | **Recommended** |

Prior art for the taxonomy: package registries model this as a distinct **maintainer/publisher** surface (npm `publish`, a Homebrew **tap**), separate from the consumer surface — the same split as an opt-in operator pack. Backstage separates **plugins** (tooling) from cataloged **entities** — curation tooling is not itself a cataloged unit, which is why it belongs in its own pack, not in `core`.

**Axis: unit terminology** (D2) — `capability` (collides with `frame-intent`'s intent altitude) vs. `artifact` (collides with governance artifacts: RFC/ADR/spec) vs. **`primitive`** (the repo's existing word for skills/agents/hooks, no collision) vs. `entity`/`component` (Backstage's, but foreign here). → `primitive`.

**Axis: ingest resumability** (D7) — no state (re-do from scratch each run: wasteful, non-idempotent) vs. **state in the destination tree** (Copybara's model; but couples to commit history) vs. **state in a user-scope scratch keyed on stable identity** (harness-agnostic, worktree-safe, history-rewrite-proof). → the third; it takes Copybara's resumability while fixing its fragility.

**Axis: export scrubbing posture** (D6/export) — allow-by-default (strip a denylist: one missed rule leaks) vs. **deny-by-default** (ship an allowlist + fail-closed verification: a missed rule *omits*, never leaks). → deny-by-default; leaking is the higher-stakes error (Copybara's documented worst case).

## Risks & what would make this wrong

**Pre-mortem.**
- *A branding/confidentiality leak reaches a fork.* Mitigation: deny-by-default strip + a **mandatory fail-closed** verification gate that hard-fails the export; substitution reads markers, so no literal identity is in the tooling to leak.
- *The pack fails the CHARTER bar and clutters the catalogue.* Mitigation: opt-in, off by default, off every profile; D1 is a human sign-off, not a self-grant.
- *A skill silently mutates the engine or credbroker.* Mitigation: the D6 lint fails the build; refusal clauses in each skill.
- *The ledger corrupts under concurrent worktrees.* Mitigation: per-candidate append-only entries (no shared mutable doc); idempotent, identity-keyed resume.

**Key assumptions (falsifiable).**
- *Catalogue curation is a real, recurring habit for its audience* — the genuinely weakest pillar, and stated honestly: there is **no historical cadence to cite**, because the capability doesn't exist yet — the manual playbook's cost has *suppressed* the practice (an ingest today is a multi-step hand-run, so it happens rarely). The recurrence bet is forward-looking: (a) lowering the cost turns occasional forks into routine curation, and (b) the `attributed`-mode ecosystem-growth thesis means usage scales with adoption — every public derivative is a curation surface. If the bet is wrong (forks/ingests stay once-a-year even with tooling), the pack fails CHARTER principle 4. There is no evidence that forecloses this; **D1 is the Approver's judgment call on the forward bet, not a claim backed by a count.**
- *The strip/substitute rules are fully expressible as a declared manifest* — the maintainer's proven manual playbook is the executed precedent that they are.
- *A user-scope scratch is reachable and shared across worktrees/harnesses* — `~/.agentbundle/` is already used this way by `adapt-to-project` and credbroker.

**Drawbacks.** A new pack is new surface to maintain and lint. The export skill's fail-closed posture will sometimes **omit** a file that was actually safe, requiring an explicit allowlist edit — accepted, because the alternative error (a leak) is worse. The skills mutate pack *sources*, so an operator who forgets `make build-self` will trip the self-coverage gate (the skills prompt for it).

## Evidence & prior art

**De-risk / spike result.** The riskiest assumption — that the transform (strip + substitute) is fully expressible declaratively and verifiable — is **already de-risked by the maintainer's proven manual white-label migration playbook** (repo-private, gitignored, not shipped). Its transform is distilled — redacted and generalized — into [`0059-notes/strip-substitute-brief.md`](0059-notes/strip-substitute-brief.md) so a reviewer can *check* the claim: three declared lists (strip globs, substitute anchors with sources+scope, include-set) plus a grep gate — no content-regex, no DSL, no engine. The skills promote that hand-run procedure into declared manifests + a fail-closed gate; no novel mechanism is invented. The one correction the distillation surfaced (folded into the Proposal): email has no marker — source it from the maintainer field; the slug is a scoped/coupled anchor, not a blanket one. No further spike needed.

**Repo precedent.** RFC-0001/0002/0003 (catalogue, self-hosting, adapter contract); RFC-0031/ADR-0021 (`pack.toml` as lossy-projected manifest, `@catalogue/pack` identity); RFC-0034 (profiles — the "curated single-scope pack set" this pack stays out of); RFC-0046 (install-source resolution — the `install-defaults.toml` blank-source fork lever); ADR-0002 (per-pack scope). The `.adapt-discovery.toml` marker table and `adapt-to-project`'s path-jail (the existing skill that customizes freshly-installed packs to an adopter's repo, confining its writes to an allow-listed set of paths) are the existing identity-substitution and scope-confinement precedents the export skill reuses.

**External prior art — Google Copybara** (patterns mined, *not* a dependency). *The mechanism characterizations below are drawn from Copybara's upstream README and `docs/reference.md`; they were fetched and read, but not independently reproduced by running Copybara — treat them as external prior art, not in-repo-verified fact. The design choices they inform stand on their own merits regardless.*
- Stores the last-migrated origin revision as a **`GitOrigin-RevId`** label in the destination → stateless, idempotent, resumable. We adopt the resumability but key on stable identity instead of a commit label (Copybara's history-rewrite weak point). [google/copybara README + docs/reference.md]
- `core.replace` auto-reverses (swap `before`/`after`) and is **glob-scoped**; broad regex is the footgun → our transforms are a declared, path/glob-scoped manifest; only the two compound anchors are blanket-safe. [docs/reference.md]
- `metadata.scrubber()` removes confidential blocks for public↔private mirroring; Copybara's highest-stakes failure is a scrubbing leak → our export is deny-by-default + fail-closed verification. [docs/reference.md]
- Requires **one authoritative repository**; bidirectional sync invites divergence → upstream is authoritative, forks are read-only-derived; the only "back" flow is a fresh, reviewed assimilation of a specific unit, never a merge-back. [README]
- Workflow modes **SQUASH / ITERATIVE / CHANGE_REQUEST** → `assimilate-repo` processes candidates ITERATIVELY (one reviewable verdict each) and emits an RFC (the CHANGE_REQUEST analog). [docs/reference.md]
- Its **Starlark config** draws a steep-learning-curve criticism → we stay declarative-TOML + prose, no DSL, no engine.

Sources: [github.com/google/copybara](https://github.com/google/copybara) · [docs/reference.md](https://raw.githubusercontent.com/google/copybara/master/docs/reference.md) · [Backstage software catalog](https://backstage.io/docs/features/software-catalog/) (entity vs. plugin split) · [Backstage glossary](https://backstage.io/docs/references/glossary/).

## Open questions

1. **Ledger schema depth.** Minimal (path/name/hash/verdict/status/destination) vs. richer (per-candidate provenance, transform log). *Recommended default:* start minimal; extend if `assimilate-repo` needs it. Owner: eugenelim. Decide by: ADR (follow-on).

*(The former "is `export-white-label` too narrow?" question is now resolved and applied in the draft: the `attributed` mode makes "white-label" one mode, not the skill, so the skill is `export-catalogue` with a `white-label|attributed` mode. A reviewer who prefers the old name can veto in D-table review; it is no longer carried as open.)*

## Follow-on artifacts

Filled on acceptance:
- **ADR-00NN:** the resumable assimilation ledger — path, `<run-id>` derivation, per-candidate append-only schema, concurrency contract.
- **Spec:** `docs/specs/catalogue-curation/` — the four skills, the strip/substitute manifests, the D6 guard lint, the fail-closed export gate; built via `work-loop`.
- **Per-pack guide:** `docs/guides/catalogue-curation/` (Diátaxis: tutorial + how-tos + reference + explanation) authored via `new-guide` — the maintainer discovery & upskilling surface, and the one that ships to forks (playbook Module 7). Pack `README.md` + `pack.toml` `[pack.links].documentation` point to it.
- **`self-host.toml`:** add `catalogue-curation` to `[recipe.packs].include` (the one declarative recipe edit; excluded from the D6 path-gate).
- **`docs/backlog.md`:** add greppable anchors for the deferred Non-goals (`retire-primitive`, `audit-catalogue`) and the ledger stale-run sweep, so the deferrals don't rot in the RFC body.
- **CHANGELOG:** `[Unreleased]` entry for the new pack.
