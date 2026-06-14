# RFC-0032: A forked-context `design-reviewer` subagent for the architect pack

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-14
- **Date closed:** 2026-06-14
- **Related:** `docs/CHARTER.md` (scope non-goal "Not a marketplace of specialized agents… Three reviewers is the ceiling"; the four principles), RFC-0007 (user-scope converter pack — architect's scope precedent), RFC-0011 (per-pack `allowed-adapters`), RFC-0024 (copilot subagent projection), `packs/research/` (precedent: an opt-in pack shipping subagents alongside skills)

## The ask

- **Recommendation (BLUF):** Add one read-only, forked-context `design-reviewer`
  subagent to the architect pack at `packs/architect/.apm/agents/design-reviewer.md`,
  alongside the existing `architect-review` skill (the two coexist; neither
  replaces the other). Record in this RFC that the charter's "three reviewers is
  the ceiling" governs the always-on *core code-review lenses*, not opt-in
  design-side review — so no charter edit is required.

- **Why now (SCQA):** *Situation* — the architect pack ships three skills and
  historically declined subagents; design review is the in-thread `architect-review`
  skill. *Complication* — `architect-design`'s own convergence loop already
  defines a reviewer-independence ladder whose **preferred** rung is a
  fresh-context review subagent, with cold re-read named as an **explicitly
  weaker floor** — and the pack ships only the floor, so every converging design
  run that lacks a harness-provided reviewer is stuck marking its own homework,
  the exact failure `architect-review` lists as a standing anti-pattern.
  *Question* — should the pack ship the preferred rung itself?

- **Decisions requested:**
  1. **Ship the `design-reviewer` subagent (skill + agent), or stay skill-only?**
     · recommended: **ship it** · why: the forked-context need is already written
     into the pack as the *preferred* path the pack can't currently supply ·
     decide-by: 2026-06-21 (default if no objection: ship).
  2. **Reconcile the charter's "Three reviewers is the ceiling."** · recommended:
     **interpret the ceiling as the core code-review lenses; record the reading
     here, no charter edit** · why: the charter's Scope text itself enumerates the
     ceiling as *"three review lenses (adversarial, security, quality)"*
     (`docs/CHARTER.md:29-30`) — a code-review enumeration · decide-by: 2026-06-21.
  3. **Agent contract** — name `design-reviewer`, tools `Read, Grep, Glob`
     (read-only), model `opus`, user-scope (inherits architect's default). ·
     recommended: as stated · decide-by: 2026-06-21.
  4. **Supersede the README "Subagents — NOT in this pack" exclusion and add a
     convergence-loop rung naming the shipped reviewer.** · recommended: fold
     into the implementing spec · decide-by: 2026-06-21.

  Right-sized: this is an additive, reversible change in one opt-in pack. The
  only charter-adjacent part is decision 2, which is why this is an RFC and not
  a plain PR.

## Problem & goals

The architect pack's design-review surface is the `architect-review` **skill**,
which runs **in-thread**. Two facts already in the pack make that insufficient
for the convergence use:

1. `architect-review/SKILL.md` carries a standing anti-pattern: *"Reviewing your
   own draft from the same session… marking your own homework. Push back and ask
   the user (or another agent) to drive the critique."*
2. `architect-design/references/convergence-loop.md` § *Reviewer independence*
   defines an isolation ladder, strongest first: **(1) Fresh context (preferred)**
   — "a new session, or the harness's review subagent where it has one"; **(2)
   Cold re-read (floor)** — "explicitly weaker isolation than a fresh context —
   name that it's the floor, not parity."

The pack ships only rung 2. Rung 1 is delegated to "the harness's review
subagent *where it has one*" — i.e. the pack ships nothing and hopes the harness
fills the gap. When it doesn't, the convergence loop self-critiques in the
authoring context, which the self-bias literature (see *Evidence*) shows
amplifies the author's own preferences rather than catching them.

**Goals.**
- Ship the preferred isolation rung as a pack primitive, so design convergence
  gets genuine context isolation without depending on the harness.
- Enforce "flag, never rewrite the design" mechanically, not just by discipline.
- Keep the critique out of the authoring thread (return a distilled,
  severity-tagged report), preserving the main session's context budget.

**Non-goals.**
- **Retiring the `architect-review` skill.** The skill serves the live-paste
  critique trigger ("review this <pasted artifact>"), which a forked-context
  agent structurally cannot — the artifact lives in the thread the agent can't
  see. Skill and agent are peers.
- **Adding code-review capability to architect.** This reviewer reads design
  artifacts (docs, diagrams, RFCs/ADRs), not code diffs. Code stays with the
  core reviewers.
- **A second always-on reviewer in the work-loop.** This agent is invoked by
  `architect-design`'s convergence loop (or by hand), not wired into the core
  per-PR gate sequence.
- **New rubric content.** The agent reuses `architect-review`'s existing
  rubrics; it changes the *execution model*, not the standard.

## Proposal

Add `packs/architect/.apm/agents/design-reviewer.md`, mirroring the shape of
`packs/research/.apm/agents/*` and `packs/core/.apm/agents/adversarial-reviewer.md`:

- **Frontmatter:** `name: design-reviewer`; `tools: Read, Grep, Glob`;
  `model: opus`; a `description` whose trigger is "an independent critique of a
  design doc / diagram / architecture artifact, seeded with the artifact + the
  agreed concept + constraints — never the authoring chain-of-thought."
- **Body:** the reviewer reuses the `architect-review` rubric set
  (genre routing → `rubric-{design-doc,c4-diagram,sequence-diagram,state-diagram,er-diagram,generic}.md`,
  plus the well-architected / lens mode → `rubric-well-architected.md`), produces
  the same verdict + severity-tagged + mechanical/judgment-tagged output shape
  the convergence loop already consumes, and returns **only** the findings block
  (no narration), matching the core reviewers' output contract.
- **Read-only by construction:** `Read, Grep, Glob` means the agent *cannot*
  edit the design — "flag, never rewrite" becomes a tool boundary, not a request.
- **Coexistence wiring:** `convergence-loop.md` § *Where the review comes from*
  gains a rung — when the `design-reviewer` agent is installed, obtain the review
  from it (rung 1, fresh context); else fall through to the existing
  `architect-review`-installed / embedded-self-check ladder. The loop remains a
  soft dependency — it degrades, never errors.

**Charter reconciliation (decision 2).** This RFC records the reading that
`docs/CHARTER.md`'s "Three reviewers is the ceiling" bounds the **always-on core
code-review lenses**. The primary-source grounding is the charter's own Scope
text, which enumerates exactly *"three review lenses (adversarial, security,
quality)"* (`docs/CHARTER.md:29-30`) — a code-review enumeration. The "ceiling" is
that enumeration; a design-side reviewer in an opt-in, user-scope pack is a
different surface and a different cadence, not a fourth code-review lens. (The
research pack's two *non-reviewer* subagents are a secondary signal that the
non-goal scopes content sprawl and a third-party agent marketplace rather than a
global agent count — but they're retrieval agents, not reviewers, so they don't
by themselves settle the reviewer question; the Scope enumeration does.) No
charter text changes; the interpretation is recorded here, and the implementing
spec's ADR pins it.

**Migration path.** None for existing state. The README's "Subagents — NOT in
this pack" exclusion is removed/revised (its rationale is now contradicted by the
pack's own convergence loop), and the pack version bumps minor (0.5.1 → 0.6.0).

## Options considered

Axis: **where the independent design-review lens originates** for the convergence
loop's preferred rung. The four options partition the origin space — the lens
originates from nothing extra (the in-pack floor), from a pack-shipped agent, from
the host harness, or from merging the skill into the agent.

| # | Option | Lens origin | Independence | Ships in pack | Verdict |
|---|--------|------------|-------------|---------------|---------|
| A | **Do nothing** — skill + cold-re-read floor / manual new session | none extra (floor) | Weak (floor) or manual | — | Leaves the preferred rung empty |
| B | **Skill + pack-shipped `design-reviewer` agent** ⭐ | the pack | Strong (forked context) | Yes | **Recommended** |
| C | **Agent only, retire the skill** | the pack | Strong | Yes | Rejected — kills the live-paste critique trigger |
| D | **Defer to a generic harness review subagent** | the harness | Adapter-dependent | No | Rejected — unshipped + un-seeded; *outcome* collapses to A's empty rung wherever the harness lacks one |

- **A (do-nothing) cost of delay:** every converging `architect-design` run on a
  harness without its own review subagent stays on the explicitly-weaker floor;
  the prior art below *suggests* that floor amplifies the author's bias — though
  that evidence is measured on translation/math, not design docs (see *Key
  assumptions*), so the cost is an extrapolation, not a measured delta.
- **Prior-art grounding:** the generator/critic separation is the established
  pattern (N-Critics; Self-Refine's self-bias failure mode) — B and C instantiate
  it; A and D do not. The repo's own `new-spec` (skill) + `adversarial-reviewer`
  (agent) pairing is exactly B's shape.

## Risks & what would make this wrong

- **Pre-mortem — "fourth reviewer" scope creep.** If approved, future packs cite
  this as licence to ship more reviewer agents and erode the charter's restraint.
  *Mitigation:* decision 2 records a *bounded* reading (core code-review lenses
  vs. opt-in design-side review), and the four principles still gate every
  future candidate. This RFC adds exactly one agent reusing existing rubrics.
- **Pre-mortem — low usage.** Design docs are authored far less often than code
  PRs; the agent could be reached rarely. *Mitigation:* it's invoked on *every*
  converging `architect-design` run (the loop's default behavior), so its cadence
  tracks design authoring, not a separate manual habit. Honest caveat retained
  under *Key assumptions*.
- **Pre-mortem — adapter gaps.** If some of architect's seven adapters don't
  project the agent primitive, the reviewer silently fails to install there.
  *Mitigation:* spiked (see *Evidence*) — all seven project it; the loop degrades
  gracefully where an install is absent.
- **Key assumptions (falsifiable):**
  - *The convergence loop's "fresh context (preferred)" rung reflects a real
    quality delta, not a stylistic preference.* Falsified if independent review
    of a design produces no better findings than a disciplined cold re-read — the
    self-bias literature says otherwise, but it's measured on translation/math,
    not design docs.
  - *Design-doc authoring is frequent enough for the agent to "stick"
    (principle 4).* Falsified if usage shows architect users rarely run the
    convergence loop.
  - *The "three reviewers" ceiling is code-side-scoped.* Falsified if the
    Approver reads it as a hard global cap — in which case decision 2 flips to a
    charter amendment or a decline.
- **Drawbacks:** one more primitive to maintain and keep in rubric-sync with the
  skill (the pack's existing duplication discipline already accepts this cost);
  a slightly larger pack surface; and the charter-interpretation precedent above.

## Evidence & prior art

- **Spike / de-risk result (riskiest assumption: adapter projection).** Resolved.
  All seven adapters architect declares in `allowed-adapters` project the agent
  primitive (verified in each module under
  `packages/agentbundle/agentbundle/build/adapters/`): `claude-code` →
  `.claude/agents/<name>.md`,
  `codex` → `codex-agent-toml`, `copilot` → `.github/agents/<name>.agent.md`,
  `kiro-ide` → `.kiro/agents/<name>.md`, `kiro-cli` → delegates to the `kiro`
  base (`kiro-cli-agent-frontmatter-v1.0`), `cursor` → `.cursor/agents/<name>.md`,
  `gemini` → `.gemini/agents/<name>.md`. The adapter contract has admitted agents
  since v0.7; architect is at v0.10, so **no contract bump is needed** — only a
  pack minor-version bump. The research pack ships two subagents to **six** of
  these adapters at user scope, proving the path end-to-end on the shared six;
  architect's seventh adapter (`kiro-cli`, which research omits) projects agents
  via the `kiro` base module (`kiro-cli-agent-frontmatter-v1.0`) — verified at the
  adapter-module level, to be confirmed by a `kiro-cli` install in the
  implementing spec.
- **Repo precedent.**
  - `packs/architect/.apm/skills/architect-design/references/convergence-loop.md`
    §§ *Reviewer independence*, *Where the review comes from* — the preferred
    fresh-context rung and the graceful-degrade ladder this agent fills.
  - `packs/architect/.apm/skills/architect-review/SKILL.md` § *Anti-patterns* —
    the marking-your-own-homework anti-pattern.
  - `packs/research/.apm/agents/evidence-retriever.md` and `source-extractor.md`
    — an opt-in pack shipping subagents alongside skills, user-scope, under this
    charter.
  - `packs/core/.apm/agents/adversarial-reviewer.md` + the `new-spec` skill — the
    authoring-skill + forked-context-reviewer-agent pairing this mirrors.
  - `docs/CHARTER.md` — the "three reviewers is the ceiling" non-goal that
    decision 2 interprets.
- **External prior art.**
  - [Pride and Prejudice: LLM Amplifies Self-Bias in Self-Refinement (Xu et al.,
    ACL 2024)](https://arxiv.org/abs/2402.11436) — abstract (verified): the
    self-refine pipeline "further amplifies self-bias" (the tendency "to favor
    its own generation"), whereas "external feedback with accurate assessment can
    significantly reduce bias." Grounds why the forked-context rung is genuinely
    stronger than same-context self-critique.
  - [N-Critics: Self-Refinement of LLMs with an Ensemble of Critics (arXiv
    2310.18679)](https://arxiv.org/abs/2310.18679) — the generator/external-critic
    separation pattern this agent instantiates.

## Open questions

1. **Charter reading vs. amendment (decision 2).** Recommended default:
   interpret the ceiling as code-side and record it here; no charter edit. If the
   Approver prefers an explicit charter line ("three *code-side* reviewers"),
   that's a one-line `update-conventions`/charter RFC follow-on. · owner:
   eugenelim · decide-by: 2026-06-21.
2. **Does the agent cover the WA-lens risk-register mode, or only the verdict
   critique?** Recommended default: it supports both `architect-review` modes,
   since both are what the convergence loop consumes. · owner: eugenelim ·
   decide-by: 2026-06-21.

## Follow-on artifacts

Filled in on acceptance:

- Spec: `docs/specs/architect-design-reviewer/` — agent file, convergence-loop
  rung wiring, README revision, pack version bump, contract/adapter test updates.
- ADR: record the charter-ceiling interpretation (decision 2) as a decision, so
  future "can we add a reviewer?" questions resolve against it.
- Edits (each an explicit acceptance criterion in the spec, not a migration
  footnote): `packs/architect/README.md` — revise the verbatim exclusion
  *"**Subagents.** Code-side reviewers cover code; design-side review is a skill,
  not a subagent"* (the sentence this RFC overturns);
  `packs/architect/.apm/skills/architect-design/references/convergence-loop.md`
  — add the shipped-reviewer rung to § *Where the review comes from*;
  `packs/architect/pack.toml` (0.5.1 → 0.6.0).
