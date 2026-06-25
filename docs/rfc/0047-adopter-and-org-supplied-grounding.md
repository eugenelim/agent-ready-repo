# RFC-0047: Adopter- and org-supplied grounding for platform, framework, and verification context

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:** 2026-06-25
- **Related:** RFC-0044 (infra-contract-acquisition), RFC-0041 (infra-aware work-loop), RFC-0040 (consolidated pack layout), RFC-0046 (convenient install defaults), RFC-0034 (pack profiles), RFC-0031 (catalogue package-manager posture), RFC-0002 (self-hosting), ADR-0034 (infra-grounding doctrine, not bundled vendor data), ADR-0021 (pack manifest source of truth, scoped identity), ADR-0010 (reference-architecture foundation), ADR-0035 (architect platform grounding)

> *Post-acceptance: see [§ Errata](#errata) (2026-06-25) for a citation-precision fix to the ADR-0034 grounding rule and the withdrawal of the org-owned detached-fork distribution follow-on RFC — no decision below is reversed.*

## The ask

- **Recommendation (BLUF):** Let the work-loop be **grounded by context the adopter or their organization supplies** — platform contracts, framework/library contracts, and verification tooling — by (1) **extending the existing EXECUTE contract-grounding gate from infra-only to also cover software framework/library contracts** via the same *detect-and-recommend, never-bundle* tier already used for infra; (2) giving the adopter a **persistent recording surface** they already own (a short command block in `AGENTS.md` + the platform/framework/verification sections of `reference.md`) that the work-loop preflight reads *first*; and (3) publishing **organization guidance for building a pack that ships a pre-baked `reference.md`, conventions, and framework-library skills** for the org's own stack. Every layer is **presence-checked: read if present, degrade honestly if absent, never mandated, never bundled** — which extends ADR-0034 Principle 1's no-per-vendor-data corollary (ADR-0034:59) rather than breaking it.

- **Why now (SCQA):**
  - *Situation* — RFC-0041/0044 gave the loop rich *runtime* grounding for infrastructure: the agent acquires a platform contract at EXECUTE time by driving the toolchain's own oracles, and re-derives it independently at REVIEW. ADR-0034 deliberately ships **no per-vendor data**.
  - *Complication* — that grounding is (a) **infra-only** — the software/code side still "greps to verify a function exists" with no detect-and-recommend tier for an unfamiliar internal framework or third-party library; (b) **cold every loop** — the verify-status / teardown / smoke / seed tooling and the credential session are *rediscovered or recreated* each time because the adopter has nowhere canonical to record them; and (c) **silent about organizations** — an org with a standard stack has no documented way to ship its golden path (reference architecture, conventions, framework knowledge) as a reusable pack.
  - *Question* — how do we let an adopter and their organization *supply* this grounding to the loop, without bundling vendor data, without mandating any external file, and without inventing new machinery?

- **Decisions requested:**
  1. **Extend the EXECUTE contract-grounding gate to framework/library contracts.** Reuse the existing gate prose + the `infra-contract-acquisition` detect-and-recommend tier; do not add a parallel skill. *Recommended: accept. Default if no objection: accept. Decide-by: acceptance.*
  2. **Source library context via a detect-and-recommend tier** — a framework-library skill (an installed *internal* one, or a published cloud / application-SDK vendor skill) *or* an optional doc-retrieval MCP (Context7-style); used if present, and if absent recommend *either* installing a published vendor skill *or* authoring an internal one via `author-a-skill` (guidance only — no bundled starter); degrade honestly, never mandate or auto-install. *Recommended: accept.*
  3. **Adopt a persistent recording surface the adopter already owns** — a short infra/verification command block in `AGENTS.md`'s "Commands you'll need", plus the platform/framework/verification sections of `reference.md`; the work-loop preflight reads these *before* cold discovery. *Recommended: accept.*
  4. **Make every layer presence-checked, never mandated** — read-if-present, degrade-honestly-if-absent, never fail the loop on absence; no CI gate requires any of these files. *Recommended: accept (this is the load-bearing constraint).*
  5. **Publish organization-pack authoring guidance** — a how-to for shipping a pack that carries a filled-in `reference.md`, conventions, and framework-library skills, installed via a repo-scope profile from the **organization's own detached fork** (its own editable install per RFC-0046/ADR-0036), with no dependency on the upstream catalogue. Reuse existing primitives; do not build new catalogue-resolution machinery. *Recommended: accept.*
  6. **Make catalogue-seed linting opt-in and rename it.** Rename `lint-seeds` → `lint-catalogue-seeds`; gate all its checks on an opt-in `[pack].lint-seeds = true` carried only by the four first-party scaffold packs (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`). Every other pack — including any org pack — is unenforced **by construction** (no flag, no enforcement), so a downstream fork needs no edit to the lint or any central list. Single tool, not split. *Recommended: accept.*

  *Decide-by for all six: RFC sign-off; default if no objection is accept as written.* No open questions outstanding — all three original ones were resolved during review (see Open questions).

## Problem & goals

**Diagnosis.** The loop's grounding has three gaps, each with a concrete symptom:

1. **The grounding gate stops at the infra boundary.** `work-loop/SKILL.md:388-398` defines the EXECUTE contract-grounding gate and explicitly frames it as *"the infra generalization of AGENTS.md's 'Grep to verify a function exists before importing it'"*. But the gate only fires on a CLI invocation, an IaC resource, or app code on a managed runtime. For an **unfamiliar internal framework or third-party library**, the agent falls back to the bare grep rule — which confirms a symbol *exists* but not its *behavioral contract* (the versioned API shape, the deprecation, the call-order constraint). There is no software-side detect-and-recommend tier, and no framework-library skill precedent anywhere in `packs/`.

2. **Verification tooling is rediscovered cold every loop.** `references/infra-verification.md` instructs the agent to *find or create* the verify-status / teardown / test-data-seed / smoke scripts and to *establish a credential session* as multi-artifact "task-zero" preflight — every loop, from scratch. The adopter has no canonical place to record "the smoke check is `make smoke`, teardown is `make destroy`, we deploy to X via Terraform" so the preflight starts from coordinates instead of cold.

3. **Organizations have no documented path to ship their stack's golden path.** An org with a standard stack (its reference architecture, its conventions, its internal-framework knowledge) can already, in principle, author a pack — but nothing documents *how* to make that pack carry a **filled-in** `reference.md` and framework-library skills, install it alongside `core`, and distribute it to their teams. The capability exists in primitives; the guidance does not.

**Goals.**

- Extend grounding to the **software/framework-library** dimension using the *same* detect-and-recommend doctrine already proven for infra — one mechanism, two surfaces.
- Give adopters a **persistent, low-effort recording surface** for platform + verification coordinates, read by the preflight before cold discovery.
- Publish **organization-pack authoring guidance** so an org can ship its golden path as a reusable, installable pack.
- Keep every layer **optional and presence-checked** — the loop runs unchanged when none of it is present.

**Non-goals.**

- **Bundling per-vendor or per-library contract data.** ADR-0034 Principle 1 stands: we ship *awareness and doctrine*, not a knowledge base. Context7, internal framework skills, and curated platform skills are detected, never bundled.
- **Shipping or mandating an MCP server / retrieval backend.** We ship awareness of optional MCP surfaces; we do not run, require, or auto-install one (consistent with `architect-knowledge-surfaces/spec.md`).
- **Org-pack-over-upstream layering / multi-catalogue resolution.** The org-pack model is a **fully detached fork the organization owns outright** — the upstream catalogue is a *template to fork and own*, not a live dependency to consume, so an installed org pack has no runtime or package dependency on upstream. Layering an org pack *over* a live upstream catalogue is therefore out of scope (and would also require the unbuilt RFC-0031 D6 virtual-catalogue work). The systematic mechanics of an org-owned detached fork are a follow-on RFC, not this one.
- **A new top-level config file.** The recording surface reuses files the adopter already owns (`AGENTS.md`, `reference.md`); no `grounding.toml`.
- **Auto-populating `reference.md` from the running stack.** That is a separate detect-and-fill capability; here `reference.md` is a surface the adopter or org *writes into*.

## Proposal

Three layers, one principle. The principle — **supplied-not-bundled, present-or-not** — is the spine; the three layers are where it lands.

### Layer A — Extend the EXECUTE contract-grounding gate to framework/library contracts (Decisions 1, 2)

Today's gate (`work-loop/SKILL.md:388-398`) fires on infra surfaces and routes to `infra-contract-acquisition`. We **widen the trigger** so the same gate also fires when generating code against an **unfamiliar internal framework or third-party library** whose behavioral contract the agent does not hold — and route that to a **software detect-and-recommend tier** that mirrors `infra-contract-acquisition`'s T2 exactly:

> **Detect** whether a framework-library contract source is available this session — a framework-library skill (an installed *internal* one, **or** a published cloud / application-SDK vendor skill), *or* an optional doc-retrieval surface (a Context7-style `resolve-library-id` + docs-retrieval tool, available as an MCP server *or* a CLI/skill), *or* official versioned docs reachable via `research`. **If present, consult it** and cite the contract slice the generated code relies on (the function signature, the version-specific behavior). **If absent on an unfamiliar framework, recommend *either* installing a published vendor skill if one exists *or* authoring an internal one via `author-a-skill` (or pointing the loop at a doc MCP), and surface it as a decision** — do not guess the behavioral contract. The detect-and-recommend step makes the gap *visible*; it does not pretend the gap is closed.

This is **prose + routing, not a new skill.** The gate already calls itself the generalization of the software grep rule; we are restoring the software case it was abstracted from, with the detect-recommend tier the bare grep rule lacks. `quality-engineer` re-derives the cited contract slice at REVIEW exactly as it does for infra. MCP / Context7 is treated under the 3-tier dependency policy as a **Tier-1 detect-and-stop** surface at most — never Tier-2 auto-installed (it is a separate process with separate auth).

### Layer B — A persistent recording surface the adopter already owns (Decisions 3, 4)

Two existing files gain a sharpened, optional slot; the preflight learns to read them first.

- **`AGENTS.md` → "Commands you'll need"** gains a short, optional infra/verification block alongside the existing `install`/`test`/`lint`/`build`:
  ```bash
  <deploy command>          # push to the target environment (if any)
  <smoke / verify-status>   # confirm a deploy/run is healthy
  <teardown command>        # tear down ephemeral infra
  <seed test-data command>  # seed fixtures / mock users (if any)
  ```
  Kept short by design — the ~200-line cap is real, and the Cursor prior art is explicit: *reference files, don't copy them.*

- **`reference.md` (the arc42 golden path)** already carries the right slots — **Constraints** (runtimes, platforms), **Solution strategy → Key technology decisions** (frameworks), **Crosscutting concepts → Observability / Testing standards** (verification). We sharpen those prompts to explicitly name the managed-runtime/platform targets, the framework-library contracts in play, and *where the verification tooling lives* — so a filled-in `reference.md` is the normative home for the detail that does not belong in `AGENTS.md`.

- **The work-loop infra preflight** (`references/infra-verification.md`) gains a first step: **read the recorded coordinates** (the `AGENTS.md` command block + the `reference.md` platform/verification sections) *if present*, then fall back to cold oracle discovery. "Check recorded coordinates → acquire via oracles" — the recorded surface seeds the acquisition; it never replaces it (the agent still derives the live contract from the toolchain).

**Presence-check is absolute (Decision 4):** every read above is *if present*. Absence lowers nothing but the starting information; it never fails the loop and is never enforced by a CI gate. This matches the established repo idiom — `agentbundle-layout.toml` optional resolution, `adapt-to-project`'s "(if present)" state reads, `architect-design`'s "state which surface you detected (or 'none')".

### Layer C — Organization-pack authoring guidance (Decision 5)

An organization with a standard stack ships its golden path as **a pack, composed entirely of primitives that already exist** — the org-side mirror of Backstage golden-path templates and Cursor "Team Rules". A new how-to guide (`docs/guides/_shared/how-to/build-an-org-stack-pack.md`) walks it:

1. **Seeds carrying filled-in standards.** The org pack ships `seeds/docs/architecture/reference.md` *populated with the org's real stack* (not the placeholder template), plus optional `seeds/docs/CONVENTIONS.md` / `seeds/AGENTS.md` deltas. On install these land in the adopter repo via the existing seed-drop mechanism (RFC-0002).
2. **Framework-library skills.** The org pack ships `.apm/skills/<framework>/SKILL.md` for its internal frameworks — the Layer-A detect target. These are ordinary skills; the model auto-activates them by description-match.
3. **One-command install.** A repo-scope **profile** (RFC-0034) lists `core` first, then the org pack, so a team installs the whole golden path in one command.
4. **Distribution — a detached fork the organization owns.** The upstream catalogue is a *template* the organization forks and owns outright; it runs its **own** editable install from its **own** clone (RFC-0046 / ADR-0036 editable-install detection, with the packaged default source blanked), so installs have **no runtime or package dependency on upstream**. (`core` in step 3 is the organization's forked `core`.) The systematic mechanics of an org-owned detached fork are the subject of a follow-on RFC (see Follow-on artifacts), not this one.
5. **The seed lint won't fight the org pack.** `lint-seeds` is renamed `lint-catalogue-seeds` and all its checks are gated on an opt-in `[pack].lint-seeds = true` flag carried only by the four first-party scaffold packs. An org pack — being intentionally **instance-content-bearing** — simply omits the flag and is unenforced by construction, with no edit to the lint or any central list (Decision 6).

The lint does two things — anti-leak of *this* catalogue's strings (the blocklist) **and** first-party scaffold-shape (placeholder-required, fail-loud-on-unknown-seed, empty-`patterns.jsonl`). Both serve the single "first-party seeds are clean placeholder scaffolds" contract; both key off the same predicate (is this a first-party scaffold pack?) and share the one flag and one exemption. There is no seed check an *instance* pack would also want — placeholder-required is the exact opposite of what it needs — so the "for other things" bucket is empty and the lint stays a **single tool, not split**. The guidance is explicit that org packs are instance-content-bearing — the inverse of the first-party scaffold contract, which the opt-in flag now enforces only where it is asked for.

### Migration path

Layers A and B are additive prose/routing changes to skills and seeds; existing repos without the new `AGENTS.md` block or a filled `reference.md` keep working unchanged (presence-checked). Layer C is net-new documentation. Decision 6 has one real migration step: flipping the seed lint to opt-in means the four first-party scaffold packs must gain `[pack].lint-seeds = true` **in the same change**, or they silently stop being enforced; the CI step is renamed `lint-seeds` → `lint-catalogue-seeds`. The implementing specs land the skill/seed/lint edits; a changelog entry records the user-visible behavior change.

## Options considered

**Axis: where the grounding context comes from** — the spectrum from "the tool ships it" to "the adopter/org supplies it" to "nobody supplies it". These four points exhaust who can be the source.

| Option | Who supplies the contract | Trade-off | Rec |
| --- | --- | --- | --- |
| **1. Do nothing** | Nobody — agent guesses or greps | Zero cost now; the three gaps persist (software guessing, cold preflight, orgs reinvent). The cost of delay compounds per loop and per adopter. | |
| **2. Bundle vendor/library data in the repo** | The tool ships it | Directly violates ADR-0034 Principle 1; unmaintainable per-vendor enumeration; the failure mode that doctrine was written to avoid. | |
| **3. Supplied-not-bundled, present-or-not** (this RFC) | The adopter (Layer B) + their org (Layer C) + optional detected tools (Layer A) | Reuses the proven infra detect-and-recommend doctrine and existing primitives; optional throughout; one mechanism across infra + software. Cost: more surface for an adopter to *optionally* fill, and org-pack guidance to maintain. | ★ |
| **4. Mandate a specific external toolchain** (e.g. require Context7 / a steering-file standard) | A mandated third party | Violates the no-mandate constraint and the Tier-3 dependency ban; couples the loop to a tool that may be absent or unauthenticated; brittle. | |

**Grounding in prior art.** Option 3 is the convergent shape across the ecosystem: **Cursor** rules (`.cursor/rules` / `AGENTS.md`) are presence/relevance-scoped, "reference files don't copy", with a Team→Project→User precedence whose *Team* layer is exactly the org tier; **Context7** is an optional MCP/skill the agent uses *if present*; **Backstage golden paths** are org-shipped reusable templates+docs. Option 2 is the anti-pattern ADR-0034 already rejected. Option 4 is what every "you must install X" integration gets wrong.

A sub-axis under Option 3 — **how to extend the gate to software** — has its own three points (do-nothing-manual-grep / extend-existing-gate / new-parallel-skill); extend-existing-gate wins because the gate already names itself the generalization of the software grep rule, so a parallel skill would be a redundant second front door.

## Risks & what would make this wrong

**Pre-mortem.**

- **The recording surface drifts.** An adopter fills the `AGENTS.md` block / `reference.md`, the stack changes, the file lies, and the agent grounds on stale coordinates. *Mitigation:* the preflight treats recorded coordinates as a *seed for* oracle acquisition, never a replacement — the agent still derives the live contract; a recorded value that contradicts the oracle is a drift signal, surfaced, not trusted. Same posture as AGENTS.md's own "when this file is wrong".
- **Layer A becomes a guessing license.** The agent "detects nothing", then proceeds on a guessed library contract instead of surfacing the gap. *Mitigation:* the gate language is detect-**and-recommend-and-degrade**, copied verbatim-in-spirit from the infra tier — absence routes to a surfaced decision, never silent progress; `quality-engineer` re-derivation catches a guessed contract slice.
- **Org packs leak the wrong way.** An org pack's filled-in seeds either get rejected by the seed lint, or — conversely — a first-party scaffold pack silently stops being checked. *Mitigation:* the renamed `lint-catalogue-seeds` is opt-in (`[pack].lint-seeds = true`) carried only by the four first-party scaffold packs; an org pack omits the flag and is unenforced by construction, while a first-party pack that drops the flag loses enforcement — caught by the migration step that adds the flag to all four in the same change (Migration path).
- **MCP/Context7 dependency creep.** A framework-library skill quietly starts auto-installing an MCP server. *Mitigation:* the 3-tier dependency policy (reviewer-enforced) bans Tier-3 auto-install; MCP is Tier-1 detect-and-stop.

**Key assumptions (falsifiable).**

- *Extending the gate to framework-library contracts adds value the bare grep rule doesn't.* Falsified if "grep to verify a function exists" already captures the behavioral contract — it does not (it captures existence, not versioned behavior); confirmed in De-risk.
- *Adopters will fill the optional surface.* Falsified if the surface stays empty in practice — but because it is presence-checked, an empty surface costs nothing (the loop degrades to today's cold discovery), so the downside of a wrong assumption here is bounded.
- *Org packs can ship filled-in seeds with no new machinery.* Falsified if seed-drop or profiles can't carry instance content — confirmed they can (RFC-0002 seeds + RFC-0034 profiles); the only friction is the lint scope (resolved: Decision 6).

**Drawbacks.**

- More optional surface for an adopter to understand (mitigated by keeping the `AGENTS.md` block short and pointing detail to `reference.md`).
- Org-pack guidance is documentation the catalogue must maintain as the pack/profile/fork mechanics evolve.
- The org-owned detached-fork model puts fork-maintenance on the organization: pulling improvements from upstream is a deliberate re-sync, not an automatic dependency update. That is an accepted cost of the no-upstream-dependency posture; the systematic mechanics are the named follow-on RFC.

## Evidence & prior art

**Spike / de-risk result.** *Riskiest assumption — extending the gate to framework-library contracts is useful, not redundant with the existing grep rule.* The gate text (`work-loop/SKILL.md:388-398`) describes itself as *"the infra generalization of AGENTS.md's 'Grep to verify a function exists before importing it'"* — i.e. the software case is the *original*, infra was the abstraction. The bare grep rule confirms a symbol exists; it does not supply the versioned behavioral contract (signature, deprecation, call-order) that an internal framework skill or a Context7 `get-library-docs` call provides. The extension therefore adds the detect-and-recommend tier the grep rule lacks — not redundant. *Second spike — org filled-in seeds vs the seed lint.* Reading `tools/lint-seeds.py` firsthand corrected an early assumption: **three** of its checks bite a downstream fork, not just the a-r-r blocklist — fail-loud-on-unknown-seed (`:172`) and placeholder-required (`:198`) fire on any new or filled-in seed, and `RFC-00\d\d` / `K-00\d\d` false-positive on an org that numbers its own RFCs. Also confirmed: only four packs ship seeds at all (`core`/`governance-extras`/`monorepo-extras`/`user-guide-diataxis`, all repo-scope); the nine user-scope packs ship none and are already outside the lint. Resolved (Decision 6): flip the lint to opt-in (`[pack].lint-seeds = true`) on those four and rename it `lint-catalogue-seeds`, so org packs are unenforced by construction.

**Repo precedent.**

- `packs/core/.apm/skills/infra-contract-acquisition/SKILL.md:84-89` — the T2 "detect-and-recommend, never bundle (Principle 1)" tier this RFC mirrors for software.
- `packs/core/.apm/skills/work-loop/SKILL.md:388-398` — the EXECUTE gate to widen; `references/infra-verification.md` — the multi-artifact preflight to seed with recorded coordinates.
- `packs/core/.apm/skills/adapt-to-project/assets/reference.md` — arc42 golden-path with the Constraints/Crosscutting slots; ADR-0010 (reference-architecture foundation).
- `packs/architect/.apm/skills/architect-design/SKILL.md:34-43` and `docs/specs/architect-knowledge-surfaces/spec.md:61,111` — the "detect surface or 'none', degrade honestly, ship awareness not a backend" idiom.
- ADR-0034 Principle 1 (no per-vendor data); ADR-0035 (curated platform skill is external/optional, not a repo pack).
- RFC-0046:22,80-90 — `_data/install-defaults.toml` fork blanking; ADR-0021 D7 — `@catalogue/pack` scoped identity. RFC-0034 — profiles. RFC-0002 — seeds + the placeholder-only `lint-seeds` contract.

**External prior art.**

- [Cursor Rules](https://cursor.com/docs/rules) and [Cursor Docs](https://cursor.com/docs) — `.cursor/rules` / `AGENTS.md` are presence/relevance-scoped, version-controlled, "reference files instead of copying their contents"; precedence **Team Rules → Project Rules → User Rules** — the Team layer is the org-shared analog of Layer C.
- [Context7 (Upstash)](https://github.com/upstash/context7) — MIT-licensed open-source tool serving up-to-date library documentation to LLMs/AI code editors; exposes a `resolve-library-id` + docs-retrieval tool and runs in two modes — a CLI+Skills mode (no MCP required) *or* a registered MCP server. The concrete optional public-API framework-grounding tool Layer A detects — never bundles.
- [What is a Golden Path? (Red Hat)](https://www.redhat.com/en/topics/platform-engineering/golden-paths) and [Building Golden Paths with Backstage software templates](https://medium.com/@rameshavutu/how-to-build-golden-paths-in-backstage-idp-with-software-templates-170adce436fe) — platform-engineering teams ship opinionated, reusable templates + documentation as an org standard; the external model for Layer C's org-stack pack.

## Open questions

None outstanding — all three original open questions were resolved during review:

- **Catalogue-seed lint scope** → Decision 6 (rename `lint-seeds` → `lint-catalogue-seeds`; opt-in `[pack].lint-seeds` flag on the four first-party scaffold packs; org packs unenforced by construction; single tool, not split).
- **Org-pack-over-upstream layering** → Non-goal (the org-pack model is a fully org-owned detached fork; the systematic mechanics are a named follow-on RFC).
- **Framework-library-skill starter** → guidance only (Decision 2: when absent, recommend installing a published cloud / application-SDK vendor skill, or authoring an internal one via `author-a-skill`; no bundled starter — it has no proven recurring shape yet and would sit against the no-bundle principle).

## Follow-on artifacts

Filled in on acceptance:

- **ADR** — record the load-bearing decision: grounding is *adopter/org-supplied and presence-checked*, extending (not breaking) ADR-0034 Principle 1; the gate generalizes from infra to framework/library via one detect-and-recommend tier.
- **Spec: `docs/specs/framework-contract-grounding/`** — Layer A: widen the EXECUTE gate trigger + the software detect-and-recommend tier (recommend installing a published cloud / application-SDK vendor skill *or* authoring an internal one via `author-a-skill`; guidance only, no bundled starter); `quality-engineer` re-derivation.
- **Spec: `docs/specs/adopter-grounding-surface/`** — Layer B: the `AGENTS.md` command block + sharpened `reference.md` prompts + the preflight "read recorded coordinates first" step; `adapt-to-project`/`init-project` elicitation.
- **Spec: `docs/specs/catalogue-seeds-lint/`** — Decision 6: rename `lint-seeds` → `lint-catalogue-seeds`; add the opt-in `[pack].lint-seeds` flag to the four first-party scaffold packs; rename the CI step; confirm whether the new optional `pack.toml` field needs a manifest contract-version bump (ADR-0021).
- **Guide: `docs/guides/_shared/how-to/build-an-org-stack-pack.md`** — Layer C: org-pack authoring (filled-in seeds + framework skills + repo-scope profile from the organization's own detached fork; omit the `lint-seeds` flag).
- **RFC (backlog): org-owned detached-fork distribution** — ~~how an organization forks the catalogue into one it owns outright and distributes internally with no upstream dependency~~. **Withdrawn — see [§ Errata](#errata) (2026-06-25).** The distribution mechanism is already the shipped RFC-0046 / ADR-0036 editable-install path; no separate RFC is warranted.
- **Changelog** — `docs/product/changelog.md` `[Unreleased]` entry for the user-visible grounding behavior.

## Errata

This section is append-only; it records refinements made after acceptance that the recording ADR-0037 and the implementing specs reflect, so they do not silently diverge from the frozen RFC body above. No decision in the body is reversed.

- **2026-06-25 — citation precision for the ADR-0034 grounding rule (no decision changed). Approver: eugenelim.** The BLUF (§ The ask, Recommendation) and the first § Non-goal phrase the constraint this RFC extends as *"ADR-0034 Principle 1's no-per-vendor-data corollary (ADR-0034:59)"*. That attribution is imprecise: `ADR-0034:59` is a **decision-driver bullet** ("Principle 1 (universal across stacks) — rules out a per-vendor knowledge base…"), and "Principle 1" there is **CHARTER Principle 1 (universality across stacks)**, not a standalone ADR-0034 principle — there is no labeled "corollary". The precise reading, which the recording ADR-0037 uses, is: **the no-per-vendor-knowledge-base rule ADR-0034 *derives from* CHARTER Principle 1 (universality across stacks)** — seen at the driver bullet `0034:59`, the Alternatives rejection `0034:97`, and the honest "mitigated, not closed" residual `0034:80`. The substance is unchanged: this RFC still *extends, not breaks* that rule; only the citation is sharpened.
- **2026-06-25 — Layer A's software grounding is realized as the *full* tiered oracle protocol, broadening ADR-0037 D1's "mirror T2 exactly" (no decision reversed). Approver: eugenelim.** Decision 1 / ADR-0037 D1 scoped the software surface to *"a software detect-and-recommend tier that mirrors `infra-contract-acquisition`'s T2 exactly"* — the supplied-not-bundled curated-skill / doc-retrieval tier RFC-0047 is about. On implementation that proved **necessary but not sufficient**: the gate calls itself "the generalization of AGENTS.md's grep-to-verify rule", and the infra side's robustness comes from its **deterministic toolchain oracles** (T0 detect + T1 `validate`/`plan`/schema-slice), not from T2 alone. The software surface has exact analogs — **T0** installed-version detection (the contract is version-specific), **T1** the type checker / compiler against the call site (`mypy`/`pyright`, `tsc --noEmit`, `go build`/`vet`, `cargo check`) plus an API-surface extract of the installed package, **T3** versioned docs / changelog, and a **runtime invoke-and-observe probe** — and the same oracle-tier-honesty axis (typed/stub-equipped = strong → untyped-introspectable = medium → dynamic / C-extension / no-stubs = weak, probe-primary). The implementing skill (`infra-contract-acquisition`) and its `oracle-table.md` reference now carry software across **all** tiers, not just T2. This **broadens** D1, reversing nothing: the T2 detect-and-recommend supplied-not-bundled tier stands unchanged (still Principle-1 no-bundled-data, still Tier-1 detect-and-stop for the optional doc MCP), and these added tiers are toolchain-native (the user's own installed `mypy`/`cargo`/etc.), so they introduce no bundled per-library data. The frozen ADR-0037 body is left intact per the ADR-immutability convention; this erratum is the governance record of the broadening, and the spec `framework-contract-grounding` reflects it. *Skill renamed in this PR: **`infra-contract-acquisition` → `contract-acquisition`**, to reflect that it now grounds both surfaces equally. The live surface carries the new name — the skill directory, its `name`, the cross-links in `work-loop` / `operational-safety` / `infra-verification`, the `core` pack manifests, and this RFC's implementing spec / changelog / backlog. **Frozen governance keeps the original name as historical record, bridged here:** RFC-0044 (filenamed `0044-infra-contract-acquisition`, which created the skill), RFC-0045, the immutable **ADR-0034** and **ADR-0037 D1** ("mirrors `infra-contract-acquisition`'s T2"), the `docs/rfc` & `docs/specs` README index rows, and the Shipped `infra-grounding` spec all name it `infra-contract-acquisition` — **that is the same skill, now `contract-acquisition`.** No ADR body is edited (immutability convention); this erratum is the old→new bridge. The skill's `description` also gives the software surface equal billing, so discoverability never rested on the name.*
- **2026-06-25 — the org-owned detached-fork *distribution* follow-on RFC is withdrawn. Approver: eugenelim.** § Follow-on artifacts named a *RFC (backlog): org-owned detached-fork distribution*, with companion mentions in § Non-goals, § Drawbacks, and § Open questions. On review that RFC is **redundant and is withdrawn**: the "systematic mechanics of an org-owned detached fork" it would own are **already realized** by the shipped RFC-0046 / ADR-0036 path — an editable install from the org's own clone with the packaged default source blanked, giving no upstream runtime or package dependency — and the *org-side authoring* is covered by Decision 5's org-stack-pack guide (Layer C). No new distribution machinery is warranted, so no separate RFC is opened. The recording ADR-0037 reflects this (D3: "distribution rides the existing RFC-0046 / ADR-0036 editable-install path", not a new RFC). This drops a speculative follow-on (pressure-test-before-adding); it reverses no decision in the body — the detached-fork *posture* and its drawbacks still stand, now with their mechanics located in the existing shipped path.
