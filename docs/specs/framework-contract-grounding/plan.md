# Plan: Framework/library contract grounding — extend the EXECUTE gate, don't fork it

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A small, surgical prose + routing change to two existing `core`-pack skill sources. The riskiest part is *restraint*: the temptation is to author a parallel skill, and the whole decision (ADR-0037 D1) is that we must not. The shape: (1) widen the EXECUTE gate's trigger in `work-loop/SKILL.md` so it names the unfamiliar-framework/library case alongside the infra surfaces, pointing at the same `infra-contract-acquisition` route; (2) add the software detect-and-recommend surface to `infra-contract-acquisition/SKILL.md` so its T2 tier covers "a framework-library skill or a doc-retrieval surface or official versioned docs", mirroring the infra detect-recommend wording verbatim-in-spirit; (3) make the `quality-engineer` REVIEW bullet's re-derivation explicitly symmetric for the software slice. Then `make build-self` projects all edited sources to every adapter, and the self-host drift gate proves the projection is clean. No production code, no new dependency, no new skill — verification is goal-based (grep the source + clean build-self) plus one manual-QA pass exercising the skill behavior.

## Constraints

- ADR-0037 D1 — **one gate, two surfaces; no parallel skill** (the load-bearing rail).
- ADR-0034 Principle 1 — no bundled per-vendor/per-library data.
- RFC-0047 Decisions 1, 2 — extend the gate; source via detect-and-recommend; MCP is Tier-1 detect-and-stop.
- The 3-tier dependency policy (reviewer-enforced) — MCP/retrieval surface never Tier-2.
- `feedback_self_host_projection` — edit pack **source**, never the projection; `make build-self` is the gate.

## Construction tests

**Integration tests:** none beyond per-task checks (no production code).
**Manual verification:** (1) exercise the work-loop EXECUTE step against an unfamiliar library, both with a framework skill present and absent; record the agent's consult-and-cite vs recommend-and-surface behavior; (2) drive a `quality-engineer` REVIEW pass over a diff citing a framework contract slice and record whether it independently re-derives the slice (spec Testing Strategy; AC6).

## Tasks

### T1: The EXECUTE gate trigger names the unfamiliar-framework/library case

**Depends on:** none

**Tests:**
- `grep` in `packs/core/.apm/skills/work-loop/SKILL.md` finds the widened trigger naming "unfamiliar internal framework or third-party library" whose behavioral contract the agent does not hold, alongside the existing CLI/IaC/managed-runtime surfaces (spec AC1).
- `grep` confirms the gate still states it is **universal across light and full mode** (spec AC7).

**Approach:**
- Edit the EXECUTE contract-grounding gate paragraph to add the software surface to its trigger and route it to `infra-contract-acquisition` (the same skill), keeping the existing "infra generalization of the grep rule" framing — now restored to also cover its origin case.

**Done when:** the gate source names the software case and routes it, with the universality clause intact; `grep` green.

### T2: The detect-and-recommend tier covers the software contract source

**Depends on:** T1

**Tests:**
- `grep` in `packs/core/.apm/skills/infra-contract-acquisition/SKILL.md` finds the software detect target — a framework-library skill (internal *or* published vendor) **or** a Context7-style `resolve-library-id` + docs-retrieval surface **or** official versioned docs via `research` (spec AC2).
- `grep` confirms the **present-source** branch reads consult-**and-cite** the contract slice (mirroring infra T2's "if present, read it"), not just the absent branch (spec AC2).
- `grep` confirms the absent-source branch reads detect-**and-recommend-and-degrade** (recommend a vendor skill / the `author-a-skill` how-to guide / doc MCP, surface as a decision), and that the doc-retrieval surface is named **Tier-1 detect-and-stop** (spec AC5).
- `grep` confirms **no** new `framework-contract-acquisition` skill directory and **no** per-library data file (spec AC3, AC4).

**Approach:**
- Add the software surface to the skill's T2 detect-and-recommend tier, mirroring the infra wording; state the MCP/retrieval surface is Tier-1 detect-and-stop and never auto-installed.

**Done when:** the tier covers the software source with the degrade wording and Tier-1 framing; no new skill or data file exists; `grep` green.

### T3: `quality-engineer` re-derives the software contract slice at REVIEW

**Depends on:** T2

**Tests:**
- `grep` in `work-loop/SKILL.md` confirms the `quality-engineer` re-derivation bullet covers the cited framework/library contract slice symmetric with infra (spec AC6).
- `grep` confirms the bullet's **firing condition** is widened too — it triggers on a diff that cites a framework/library contract slice, not only on "infra-flavored work" — so the re-derivation is reachable for a pure-software diff (pre-EXECUTE review Concern 3).

**Approach:**
- Adjust the `quality-engineer` REVIEW prose so the independent contract re-derivation is explicitly framework/library-aware, not infra-only — widening **both** the slice noun and the bullet's trigger condition so a software-contract-citing diff reaches the re-derivation.

**Done when:** the REVIEW prose names the software slice re-derivation **and** fires on a software-contract-citing diff; `grep` green.

### T4: Project and verify the change is clean and additive

**Depends on:** T1-T3

**Tests:**
- `make build-self` projects the edited sources to every adapter; `git status` is clean afterward (self-host drift gate, spec AC8).
- `python .claude/skills/work-loop/scripts/lint-spec-status.py` is clean (spec AC8).
- Manual-QA pass recorded in `docs/specs/framework-contract-grounding/notes/manual-qa.md` per the spec's Testing Strategy (both the EXECUTE happy-path observation and the AC6 reviewer re-derivation observation).
- `docs/product/changelog.md` `[Unreleased]` gains an entry for the user-visible gate-behavior change (Assumptions: changelog rule).

**Approach:**
- Run `make build-self`; clean any stray `__pycache__` first to avoid a false drift positive; verify against a clean tree.
- Add the changelog entry; exercise the skill behavior and record observations.

**Done when:** build-self clean, lint clean, changelog entry present, manual-QA observations recorded.

## Rollout

Pure prose/routing change to `core`-pack skill sources, projected by `make build-self`. No infra, no external system, no migration. Reversible by reverting the prose. Deployment sequencing: none — the projection is atomic with the source edit in one PR.

## Risks

- **Trigger over-fires** on familiar framework code, adding noise. Mitigation: the trigger names the *unfamiliar-behavioral-contract* case explicitly (Boundaries: Ask first).
- **Scope creep into a parallel skill** mid-EXECUTE. Mitigation: ADR-0037 D1 in Constraints; the structural-change trigger re-fires if any task proposes a new skill directory.

## Changelog

- 2026-06-25: initial plan (RFC-0047 Layer A follow-on).
- 2026-06-25: folded pre-EXECUTE adversarial findings — T2 present-source consult-and-cite grep (Concern 1); named `notes/manual-qa.md` recording location (Concern 2); T3 widens the re-derivation bullet's firing condition, not just the slice noun (Concern 3); `author-a-skill` referenced as the how-to guide it is (Nit 4).
- 2026-06-25: progressive-disclosure trim of work-loop REVIEW infra blocks (kept the file under the 1000-line skill-spec cap; depth already in `references/infra-verification.md`).
- 2026-06-25: **scope broadened** (RFC-0047 § Errata) from "mirror T2 only" to the **full tiered oracle protocol** for software — added T0 (version detect), T1 (type-checker/compiler + API-surface extract), T3 (versioned docs), runtime probe, and software oracle-tier honesty to `infra-contract-acquisition/SKILL.md`; per-ecosystem commands to `references/oracle-table.md`; ACs 9–12. Research-backed (type checkers / stubs / introspection / version-pinning / runtime probes as the deterministic library-contract oracles).
