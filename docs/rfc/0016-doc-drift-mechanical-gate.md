# RFC-0016: Doc-drift prevention — construction + judgment, with a catalogue-governance linter

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-05-29
- **Date closed:** 2026-05-29
- **Related:** `docs/CONVENTIONS.md` § 4 + § Document lifecycle; `packs/core/.apm/agents/adversarial-reviewer.md` #5; `packs/core/.apm/skills/work-loop/SKILL.md` § GATES / § DECIDE; `packs/core/.apm/skills/new-spec/assets/spec.md`; `packs/core/.apm/hooks/pre-pr.py`; `docs/contracts/adapter.toml`

## The ask

- **Recommendation (BLUF):** Prevent doc drift through the surfaces that **actually ship to adopters** — (1) a canonical-by-**construction** `new-spec` template, (2) a sharpened `adversarial-reviewer` drift checklist, (3) a sharpened work-loop **DECIDE** checklist, (4) the canonical contract pinned in the **CONVENTIONS seed**, and (5) a durable **in-repo deferred-work register** (rename the top-level `ROADMAP.md` → `backlog.md`; deferrals point into it; the PR description becomes a pointer, not the record). A mechanical `lint-spec-status.py` ships as **catalogue governance only** (our `tools/` + our CI), because — verified below — linters don't project to adopters, adopters have no guaranteed Python runtime, and no adapter exposes a pre-PR hook event.
- **Why now (SCQA):** *Situation* — the work-loop replaces "feel" with mechanical gates (lint/typecheck/test). *Complication* — every doc-drift control is the opposite (honor-system principle + judgmental reviewer), and `docs/ROADMAP.md` records drift caught *by accident*; a live example, `wire-session-start-hook`, is `Shipped` with 11/11 ACs unchecked. The obvious fix — ship a lint gate — turns out **not to reach adopters** (packaging, runtime, and hook-event constraints). *Question* — what doc-drift prevention can we *actually deliver* to polyglot adopters across four adapters, and what stays catalogue-internal?
- **Decisions requested:**
  1. **Delivery model.** · recommend **construction + judgment** for adopters (mechanisms 1–4), with the **mechanical lint as catalogue-governance only** (Tier 1) · default: this split · decide-by: acceptance.
  2. **Which mechanisms ship in v1.** · recommend **all five** · default: all five · decide-by: acceptance.
  3. **Deferred-work tracking.** · recommend a **version-controlled in-repo register** (`ROADMAP.md` → `backlog.md`), the canonical `(deferred: <anchor>)` marker points into it, PR description becomes a pointer, and the work-loop's "PR is the durable record" rule is replaced · default: this · decide-by: acceptance.
  4. **Convention / template / seed changes.** · recommend **yes** — pin the status vocabulary, AC notation, and `(deferred:)` token in the CONVENTIONS seed; update the `new-spec` template; seed `backlog.md`; name the catalogue lint in `work-loop` § GATES · default: yes · decide-by: acceptance.

## Problem & goals

**Diagnosis.** Doc drift recurs because the rule ("spec drift is a bug — fix it in the same PR", `CONVENTIONS.md:789`) is *unenforced*: the three controls (the principle; `adversarial-reviewer` #5; the DECIDE checklist) are all honor-system or judgmental, while the only *mechanical* step (GATES: lint/typecheck/test) never reads docs. Evidence in-corpus: `wire-session-start-hook` (`Shipped`, 11/11 ACs unchecked, no deferral), `Drafting` (an out-of-vocabulary status in `lint-packs-target-vocab`), and a `docs/ROADMAP.md` whose own log repeatedly records drift "closed in-PR" after an accidental catch.

**The delivery complication (the heart of this RFC).** The intuitive fix — a `lint-spec-status.py` gate — cannot reach adopters:

- **Linters don't project.** `tools/lint-*.py` have no `packs/` source; they're catalogue-internal. The *projected* `pre-pr.py` would call linters absent from an adopter's tree. Shipping one would require the **seeds** construct — which `lint-seeds.py` (RFC-0002) restricts to *placeholder templates*, not working scripts.
- **No guaranteed runtime.** The pack ships files, not interpreters. Hooks hardcode `python …` with **no declared runtime**; a JS/Java adopter has no Python, so the script can't run locally. The only language-agnostic runtime surface is **CI** (which provisions Python regardless of project language).
- **No pre-PR hook event, and copilot can't fire hooks at all.** Per `adapter.toml`, hook *bodies* project to all four adapters, but hook *wiring* exists only for SessionStart-class events (wrong moment), and copilot's `hook-wiring` is `dropped`. There is no PR-open lifecycle event to bind to (`CONVENTIONS` § the no-PR-open-event note).

So: a hard, fail-closed gate is achievable **only inside this catalogue** (Python + CI both present). For adopters, prevention must use the surfaces that *do* project — **skills (all 4 adapters)**, **agents (3 of 4; copilot addable)**, and **seeds (all 4)** — and must be **construction + judgment**, not a script.

**Goals.** Reduce mechanical doc drift at authoring and review time on every adapter; pin the contract those judgments measure against; give deferred work a durable, tool-agnostic home; keep a hard mechanical gate where it *can* run (Tier 1). **Non-goals:** detecting *semantic* spec↔code drift (stays with `adversarial-reviewer` #5 — prior art confirms it only reduces to an LLM + human review); retro-fixing this repo's Frozen completed specs; assuming any adopter runtime or issue tracker; a fail-closed gate in adopter repos (infeasible — see above).

## Proposal

Five mechanisms, each routed to a surface that actually reaches its audience.

**1 — Canonical-by-construction `new-spec` template (skill asset; all 4 adapters).** The template already stamps canonical status vocab + `- [ ]` ACs, so an adopter's specs are canonical *from birth*. Extend it to pre-seed the `(deferred: <anchor>)` convention and the status comment. Drift you never author costs nothing to prevent — the strongest, most portable lever.

**2 — Sharpened `adversarial-reviewer` checklist (agent; claude-code + kiro + codex today, copilot addable).** Turn #5's vague "spec drift" into named, concrete checks the agent runs every review: *status flipped to match the change? every AC `[x]` or `(deferred:)`? deferred items in the register? intra-repo references resolve?* This is the four invariants delivered as **agent judgment**.

**3 — Sharpened work-loop DECIDE checklist (skill; all 4 adapters).** The same named items at finish-time, covering the adapters the agent primitive can't reach. (2)+(3) together give drift-catching on all four.

**4 — Pinned contract in the CONVENTIONS seed (seed; all 4 adapters).** Pin the canonical status vocabulary, AC notation, and `(deferred: <anchor>)` token as documented rules — the source of truth (1)–(3) measure against. Without it they enforce an unwritten contract. Add the one-line statement that this contract is metadata-only; semantic drift is `adversarial-reviewer` #5's job.

**5 — Durable in-repo deferred-work register (seed + convention; all 4 adapters).** Replace the work-loop's current "Deferred → PR description; the PR is the durable record" rule — which the research names as the lossy *"created and then forgotten"* anti-pattern — with a **version-controlled in-repo register**: rename the top-level `ROADMAP.md` (a *backlog*, misnamed) → **`backlog.md`**, seed it as a placeholder so adopters have one from day one, and make `(deferred: <anchor>)` point into it. The PR description keeps a one-line *pointer*, not the record. Mirroring to an adopter's issue tracker is a recommended option, never hardcoded (no adopter-tracker assumption). This also resolves the `ROADMAP.md` vs `docs/product/roadmap.md` confusion: "roadmap" = strategy (`docs/product/roadmap.md`), "backlog" = the tactical work/deferral index.

**Tier 1 — catalogue-governance linter (this repo only).** `tools/lint-spec-status.py` + our CI checks the same invariants mechanically against *our* spec corpus, where Python and CI exist. It does not ship to adopters. Invariants: (i) status vocabulary; (ii) ACs checked-or-`(deferred:)` at the ship transition (diff-triggered; the completed/Frozen corpus is grandfathered); (iii) dangling intra-repo references (warn-only until measured); (iv) every `(deferred:)` anchor resolves in `backlog.md`.

## Options considered

MECE along **enforcement mechanism, ordered by how strongly it binds** — the four exhaust the mechanisms (nobody / judgment / deterministic check / structurally-unrepresentable); there is no fifth.

| Option | What | Reaches adopters? | Guarantee | Verdict |
|---|---|---|---|---|
| **A. Do-nothing** | honor-system + reviewer #5 | n/a | none | the recurrence is the evidence |
| **B. Reviewer-only** | sharpen `adversarial-reviewer` | 3/4 adapters | judgmental | necessary, not sufficient alone |
| **C. Construction + judgment** ★ | template + reviewer + DECIDE + CONVENTIONS + register | **all 4** (skills/seeds) + 3/4 (agent) | soft (prevent + catch) | **recommended for adopters** |
| **D. Mechanical lint everywhere** | ship `lint-spec-status.py` to adopters | **cannot** (packaging/runtime/event) | hard, but undeliverable | **Tier 1 only** (our repo) |
| **E. By-construction status** | derive status from AC state | partial (template) | strongest | folded into C's mechanism 1 |

Deferred-work home (sub-axis, by durability): PR description (**anti-pattern**) / code TODO (pointer only) / **in-repo register (chosen)** / issue tracker (best where present, can't assume). Grounded in [ProductPlan: roadmap vs backlog](https://www.productplan.com/learn/product-roadmap-vs-product-backlog), [Stepsize](https://stepsize.com/technical-debt), [Mark Heath's debt register](https://markheath.net/post/technical-debt-register).

## Risks & what would make this wrong

**Pre-mortem.** *Soft guarantee gives false comfort* → the CONVENTIONS line states it's metadata-only; Tier 1 keeps a hard gate where it runs. *Instruction bloat — agents ignore added checklist items* → keep the items few, named, and concrete; the reviewer's report format already anchors them. *The register rots like PR comments did* → it's version-controlled, greppable, and `(deferred:)` ↔ `backlog.md` resolution is mechanically checked in Tier 1 (and by reviewer judgment in adopters). *Template/reviewer drift apart* → both ship from the same pack; a template change must update the CONVENTIONS contract in the same PR.

**Key assumptions (falsifiable).** The mechanical slice is a worthwhile fraction of real drift (spike: ≥1 live true-positive). Adopters' template-shaped specs are regular enough for judgment to be reliable (the template pins the shape). Agents honour added checklist items more than they honour the current vague #5 (unproven — the whole soft-vs-hard bet).

**Drawbacks (not "none").** No fail-closed guarantee for adopters — a real downgrade from a CI linter, accepted because the alternative is undeliverable. A rename (`ROADMAP.md`→`backlog.md`) touches links. The work-loop rule change alters a documented convention. Maintaining the Tier-1 lint + its pinned formats is ongoing cost.

## Evidence & prior art

**Spike (this repo = the self-host adopter).** "Shipped ⇒ all ACs `[x]`" false-positives on `adapt-to-project` / `apm-install-route-parity` (legitimate deferrals) → forced the `(deferred:)` hatch + register-resolution. AC notation is non-uniform across *this repo's pre-template* specs → but adopters' specs are template-shaped from birth, so this is a self-host concern, not an adopter one. Shipped specs are Frozen → grandfather them; (ii) fires only at the transition.

**Delivery facts (all verified against `adapter.toml` + tool docs, 2026-05).** Linters have no `packs/` source (repo-only). Seeds are placeholder-only (`lint-seeds.py`, RFC-0002). No runtime is declared; hooks hardcode `python …`. Agent primitive projects to claude-code/kiro/codex (`direct-file` / `codex-agent-toml`); copilot `dropped` but [Copilot added subagents in 2026](https://docs.github.com/en/copilot/how-tos/copilot-sdk/use-copilot-sdk/custom-agents) (addable). Subagents are real in [Codex (GA 2026-03-16)](https://developers.openai.com/codex/subagents) and [Kiro (IDE 0.9)](https://kiro.dev/docs/chat/subagents/).

**Catalogue-lint prior art.** [`check-peps.py`](https://raw.githubusercontent.com/python/peps/main/check-peps.py) — `_validate_status` against a frozenset; deterministic metadata lint in CI. Semantic-drift prior art: [spec-kit-sync](https://github.com/bgervin/spec-kit-sync) is AI-powered and routes drift to human review → semantic drift stays with the reviewer.

## Open questions

1. **Copilot agent enablement.** Now that Copilot supports subagents, do we flip its `agent` projection from `dropped` to enabled (extending mechanism 2 to 4/4)? · default: **separate follow-up** — it's a contract change with its own conformance work · owner: eugenelim · decide-by: implementing-spec time.
2. **`(deferred:)` token shape.** `(deferred: <anchor>)` inline vs. a `- [~]` glyph. · default: **the inline parenthetical** — carries the `backlog.md` anchor, renders in GFM · owner: eugenelim · decide-by: implementing-spec time.
3. **(iii) reference scope (Tier 1).** doc cross-refs only in v1, or code paths later? · default: **doc-refs only**, revisit after the warn-only rate is observed · owner: eugenelim · decide-by: v1.1.

## Follow-on artifacts

On acceptance:
- ADR-NNNN: "Doc drift — prevented by construction + judgment for adopters; mechanically gated only as catalogue governance."
- Spec: `docs/specs/doc-drift-prevention/` — the five mechanisms as acceptance criteria, the Tier-1 lint contract + corpus construction test, the `ROADMAP.md`→`backlog.md` rename + seed, and the living-spec normalization.
- Convention/template/seed: `CONVENTIONS.md § 4` (status vocab, AC notation, `(deferred:)` token, metadata-only note); `new-spec` `assets/spec.md`; `work-loop` § GATES (name the Tier-1 lint) + § DECIDE (register-not-PR rule); seed `backlog.md`.

## Errata

This RFC is Accepted (Frozen): the body above is preserved as the original
decision record. Corrections are appended here, Approver-signed.

- **2026-05-29 (Approver: eugenelim) — the "linters don't project" premise is
  false; delivery Decision #1 is corrected.** The § Proposal ("Tier 1"),
  § Options considered (row D, row C's "all 4 (skills/seeds)" excluding the
  lint), the § Evidence "Delivery facts" bullet ("Linters have no `packs/`
  source (repo-only)"), and **Decision #1** all rest on the claim that a
  `lint-spec-status.py` *cannot reach adopters* because "linters don't project —
  `tools/lint-*.py` have no `packs/` source." **That premise is wrong.** A
  skill's `scripts/` folder is a first-class projecting surface that already
  ships governance Python helpers to all four adapters: `governance-extras`'s
  `new-adr` / `new-rfc` `scripts/next-ordinal.py` (with their bundled tests) and
  `core`'s `work-loop` `scripts/loop-cohort.py`. A linter given a `packs/`
  source under a skill's `scripts/` projects exactly the same way.

  Of the three "cannot reach adopters" reasons, **only the third survives**:
  there is no PR-open lifecycle event to fire a *fail-closed* gate in an adopter
  repo (and copilot can't fire hooks). Reason one (projection) is false per
  above; reason two (no runtime) is the same Python bet `loop-cohort.py` and
  `next-ordinal.py` already make — the agent runs them where Python exists and
  they degrade where it doesn't. The RFC conflated "can't be a *fail-closed
  gate* for adopters" (true) with "can't be *delivered* to adopters at all"
  (false).

  **Corrected decision (supersedes Decision #1's "catalogue-governance only,
  Tier 1"):** the mechanical lint **ships to adopters as a `work-loop` skill
  script** (`packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`),
  invoked by the agent at the work-loop's finish-time checklist — *available and
  agent-invoked, not fail-closed*. The catalogue additionally runs it as a
  fail-closed CI gate via `make build-check`, where a PR event and Python both
  exist. The adopter delivery model is therefore construction + judgment **plus
  an agent-invocable mechanical check on every adapter that has Python** — not
  construction + judgment alone. Implemented in
  `docs/specs/lint-work-loop-delivery/`; the `doc-drift-prevention` spec's
  catalogue-only Boundaries carry a matching erratum.
