# Spec: Framework/library contract grounding — extend the EXECUTE gate, don't fork it

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0047 (Decisions 1, 2; § Errata 2026-06-25 — full-protocol broadening), ADR-0037 (D1), ADR-0034 (Principle 1)
- **Contract:** none <!-- prose + routing change to an existing skill; no API surface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

When an agent in the work-loop is about to generate code against an **unfamiliar internal framework or third-party library** — one whose *behavioral* contract (versioned signature, deprecation, call-order constraint) it does not already hold — it should be grounded the same way it already is for infrastructure: detect whether a contract source is available this session, consult and cite it if so, and surface the gap as a decision if not — never silently guess. Today the EXECUTE contract-grounding gate (`packs/core/.apm/skills/work-loop/SKILL.md:388`) calls itself *"the infra generalization of AGENTS.md's 'Grep to verify a function exists before importing it'"* yet fires only on infra surfaces; for software the agent falls back to the bare grep rule, which confirms a symbol *exists* but never its behavioral contract. Success: the **one existing gate** widens to cover the software case it was abstracted from, routing to the **same tiered protocol** in `infra-contract-acquisition` — as **prose + routing on the existing gate and skill**, with **no new skill** and **no bundled per-library data**.

> **Scope broadened post-acceptance (RFC-0047 § Errata 2026-06-25).** The spec
> as accepted mirrored only `infra-contract-acquisition`'s **T2** (the
> supplied-not-bundled detect-and-recommend tier). On implementation that proved
> necessary-but-not-sufficient: the infra side's robustness comes from its
> **deterministic toolchain oracles**, and software has exact analogs. The
> software surface now rides the **whole** protocol — **T0** installed-version
> detection, **T1** the type checker / compiler against the call site plus an
> API-surface extract of the installed package, **T2** the curated behavioral
> skill (unchanged), **T3** versioned docs / changelog, and a **runtime
> invoke-and-observe probe** — under the same oracle-tier honesty (strong /
> medium / weak). These tiers are **toolchain-native** (the user's own installed
> `mypy` / `cargo` / `tsc` / …), so the no-bundled-data rule (Principle 1) is
> untouched. ACs 9–11 add the tiers; AC12 records the broadening in governance.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the change to **prose + routing** on the existing EXECUTE gate (`work-loop/SKILL.md`) and the existing `infra-contract-acquisition` skill — edit the pack **source** under `packs/core/.apm/skills/…`, then project via `make build-self` (never hand-edit `.claude/skills/…`).
- Frame absence as **detect-and-recommend-and-degrade**: on an unfamiliar framework with no contract source, recommend installing a published vendor skill *or* authoring an internal one via `author-a-skill` *or* pointing the loop at a doc MCP, and **surface it as a decision** — guidance only.
- Treat any optional doc-retrieval surface (Context7-style `resolve-library-id` + docs-retrieval, MCP or CLI/skill) as a **Tier-1 detect-and-stop** dependency at most, per the 3-tier dependency policy.
- Keep the `quality-engineer` REVIEW re-derivation symmetric with infra: it re-derives the cited contract slice from the source independently.

### Ask first

- Any change that would touch `infra-contract-acquisition`'s **tiering structure** rather than adding the software surface to it (the tier shape is shared with infra).
- Widening the trigger in a way that fires on *familiar* framework code (the gate is for the *unfamiliar-contract* case, not every import).

### Never do

- **Add a parallel `framework-contract-acquisition` skill or any second front door** — ADR-0037 D1 is extend-the-one-gate; a parallel skill is the rejected alternative.
- **Bundle per-library or per-vendor contract data** into the catalogue (ADR-0034 Principle 1; ADR-0037 boundary).
- **Auto-install** an MCP/retrieval backend, or mandate one (Tier-3 ban).
- Let "detected nothing" become silent progress on a guessed behavioral contract.

## Testing Strategy

- **Gate prose + routing exists (goal-based check).** `grep` the widened trigger and the software detect-and-recommend tier in the pack **source** (`packs/core/.apm/skills/work-loop/SKILL.md` and/or `infra-contract-acquisition/SKILL.md`), and confirm it projects to every adapter via `make build-self` with a clean tree afterward (the self-host drift gate).
- **No new skill, no bundled data (goal-based check).** `grep` confirms no new `framework-contract-acquisition` skill directory exists and no per-library data file was added.
- **Full-protocol software tiers exist (goal-based check, ACs 9–11).** `grep` `infra-contract-acquisition/SKILL.md` for the software treatment under T0 (installed-version detect), T1 (type checker / compiler + API-surface extract), T3 (versioned docs / changelog), and the runtime invoke-and-observe probe; `grep` the software rows of the oracle-tier-honesty table (strong / medium / weak).
- **Per-ecosystem oracle table exists (goal-based check, AC11).** `grep` `references/oracle-table.md` for the Software surface section with Python / TypeScript / Go / Rust / Java rows and the named oracle-gap caveats.
- **Behavioral happy path — EXECUTE (manual QA).** Exercise the skill as a user would: pose an EXECUTE step that writes code against an unfamiliar library with (a) a framework skill present → the agent consults and cites the contract slice; (b) no source present → the agent recommends a source and surfaces the gap as a decision rather than guessing. Record the observed agent behavior in `notes/manual-qa.md` under this spec dir.
- **Re-derivation — REVIEW (manual QA, AC6).** Drive a `quality-engineer` REVIEW pass over a diff that cites a framework/library contract slice, and record whether the reviewer **independently re-derives** that slice from the source (the framework skill / doc-retrieval surface / versioned docs) rather than trusting the implementer's citation — symmetric with its infra re-derivation. AC6 is verified by this observed reviewer behavior, not by the prose grep alone. Record the observed reviewer behavior in the same `notes/manual-qa.md`.
- **Activation eval (goal-based, if the pack carries trigger evals).** The widened gate prose is reachable from the work-loop skill's existing activation surface; no new eval pack required.

## Acceptance Criteria

- [x] The EXECUTE contract-grounding gate's trigger explicitly fires when generating code against an **unfamiliar internal framework or third-party library** whose behavioral contract the agent does not hold, in addition to the existing infra surfaces, in the pack source.
- [x] The gate routes the software case to a **detect-and-recommend tier that mirrors `infra-contract-acquisition`'s T2** — detect a framework-library skill (internal *or* published vendor) **or** a Context7-style retrieval surface **or** official versioned docs via `research`; consult-and-cite if present; recommend-and-surface-as-a-decision if absent.
- [x] The change is **prose + routing only** — no new skill directory is created, and `grep` finds no `framework-contract-acquisition` skill.
- [x] **No per-library / per-vendor contract data** is added to the catalogue.
- [x] The optional doc-retrieval surface is documented as **Tier-1 detect-and-stop** (never Tier-2 auto-install); the gate language is detect-**and-recommend-and-degrade** (absence routes to a surfaced decision, never silent progress).
- [x] `quality-engineer`'s REVIEW pass re-derives the cited framework/library contract slice independently, symmetric with its infra re-derivation.
- [x] The gate's universality is preserved: it remains stated as **universal across light and full mode** (it already is for the infra case).
- [x] `make build-self` projects the edited source to every adapter and the tree is clean afterward (self-host drift gate green); `lint-spec-status.py` is clean.
- [x] The software surface rides the **whole** protocol, not just T2: `infra-contract-acquisition/SKILL.md` names a software treatment for **T0** (detect the library + installed version), **T1** (the type checker / compiler against the call site **plus** an API-surface extract of the installed package — the deterministic signature oracle), **T3** (versioned docs / changelog), and the **runtime invoke-and-observe probe**, alongside the existing T2 curated-skill tier. (RFC-0047 § Errata broadening)
- [x] **Software oracle-tier honesty** is stated: strong (typed / stub-equipped → compiler/type-checker machine-verifiable) / medium (untyped-but-introspectable) / weak (dynamic / C-extension / no-stubs → runtime probe primary), parallel to the infra rows; the protocol is explicitly robust by landing on the strongest *available* oracle and declaring confidence, not by any single oracle covering all software.
- [x] `references/oracle-table.md` carries a **per-ecosystem software** section (Python / TypeScript / Go / Rust / Java) giving the concrete T0 version-detect, T1 type-checker/compiler oracle, API-surface extract, and runtime probe commands — the reference instance, with the prose staying tool-neutral; known oracle gaps (C-extension introspection, `cargo-semver-checks` type-level, `Any`-defaulted stubgen, behavioral-contract-not-in-types) are named, not papered over.
- [x] The scope broadening beyond ADR-0037 D1's "mirror T2 exactly" is recorded in **RFC-0047 § Errata** (Approver-signed), reversing no decision; the frozen ADR-0037 body is left intact per the ADR-immutability convention.

## Assumptions

- Technical: The EXECUTE gate lives in `packs/core/.apm/skills/work-loop/SKILL.md` (the source projected to `.claude/skills/…`); the infra T2 detect-and-recommend tier is in `infra-contract-acquisition/SKILL.md`. (source: RFC-0047 § Evidence repo precedent; verified `work-loop/SKILL.md:388`, `infra-contract-acquisition/SKILL.md:85,89` 2026-06-25)
- Technical: The 3-tier dependency policy (Tier-1 detect-and-stop / Tier-2 gated install / Tier-3 banned) governs the MCP/retrieval surface and is reviewer-enforced. (source: `project_skill_prereq_pattern` memory; CONVENTIONS)
- Process: This is a `core`-pack skill-prose change → `make build-self` is the projection gate, and a user-visible skill-behavior change → a `docs/product/changelog.md` `[Unreleased]` entry lands in the **implementing** PR. (source: `feedback_changelog_for_skill_changes`, `feedback_self_host_projection` memory)
- Product: Extending the gate adds value the bare grep rule does not — confirmed in RFC-0047's de-risk spike (grep captures existence, not versioned behavior). (source: RFC-0047 § Evidence; user direction 2026-06-25)
