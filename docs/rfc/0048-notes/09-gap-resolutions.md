# Gap resolutions

Applying the operating model to the RFC's own gaps: most are **referent-groundable**
(practice / precedent / the repo / omnigent) → resolved here. Only value / scope calls
go to the human (surfaced one by one).

## Resolved — with the referent that settled it

| Gap | Resolution | Referent |
| --- | --- | --- |
| **O1** altitude-descent driver | `discovery-lead` recursively applies `decompose-intent` from the entry altitude to buildable leaves; descent stops at a feature-leaf that maps to one slice within appetite | recursive decomposition + `decompose-intent`'s existing one-level behavior |
| **O2** blackboard · **O3** open-questions · **O7** backlog/DAG | the sidecar schema (notes/08) — typed slots + queue + the backlog as the cross-component DAG | notes/04, /08; `loop-cohort` topological scheduler |
| **O4** traceability lint | a tool over the edge set (outcome→…→component); flags any node missing an up/down edge | generalizes `receive-brief`'s `lint-brief-coverage.py` |
| **O5** live-lens invocation | add a **design-artifact review mode** to `security-reviewer` + `quality-engineer` (3rd mode beyond spec/diff), invoked on a blackboard artifact when it crosses the reviewer's boundary | the existing reviewer modes + `work-loop`'s risk triggers |
| **O6** generalize saturation | lift `research-project-check`'s stop-signal: converged iff no new OQ + traceability closed + a full pass with no invalidating edit | `research-project-check` |
| **O8** spec↔artifact linkage | `new-spec` gains a `Discovery:` header (+ LLD references blueprint/screens/arch); the lint enforces the edges | the existing optional `Brief:` header pattern |
| **O10** scope-creep guard | structural orphan = the lint; *semantic* over-scoping = the human at G1.5 (split) | (decided earlier) |
| **O11** rejection/recovery | gate state-machine: reject emits reason→correction → loop re-enters that gate's phase → **cascade-invalidate downstream blackboard slots via the traceability edges** (mark stale) → re-run affected lenses; bounded by O12 | LangGraph checkpointers (pause/modify/resume); plan-mode reject→revise; `work-loop` iteration |
| **O12** outer cap | `discovery-loop` carries an outer round cap + a cost budget (tunable defaults); on cap → stall surfaces to the human (predicate c) | `work-loop`'s cap + omnigent's `cost_budget` |
| **O13** coordinator shape | `discovery-lead` agent + `discovery-loop` skill in `product-engineering`, runs on a harness | (decided — D8) |
| **A1** headless checkpoint/resume | consent-gate contract: write decision-package to sidecar, status=awaiting-human → harness surfaces option-card → human verdict → decision-log → resume | omnigent human-in-the-loop pause; LangGraph checkpointer |
| **A2** harness-neutral decision schema | the decision-package / option-card schema (gate · summary · decisions-requested · recommended · reversibility-class · artifacts); shipped doctrine | omnigent + our decision-log schema |
| **A3** team-composition | the "team" = installed lens-packs (progressive enhancement) + a thin team-manifest; omnigent YAML agent-defs as the harness expression | omnigent YAML defs + our detect-and-degrade |
| **OQ3** self-coverage packaging | reference library + doctrine, **no new reviewer** (the `operational-safety` shape) | `operational-safety` / RFC-0041 |
| omnigent commitment | keep as a **harness-neutral reference**, not a hard dependency; the portable sidecar schema is the hedge | the RFC's own no-engine principle |
| roster-truth (AWS skills) | re-audit every ✓; reclassify the AWS items as out-of-scope or net-new | (adversarial finding, actioned) |

**Net:** the Decision-7 spike shrinks to its honest core — an **empirical prototype of the
sidecar + `discovery-loop` on omnigent** to confirm these paper resolutions hold in
practice. The design blockers are closed here.

## Surfaced to the human (genuine value / scope calls) — one by one

1. **`design-craft` → `experience` rename vs grow-in-place** — pack identity + adopter-
   facing (mild irreversibility; no pack-alias mechanism exists). *Value/identity call.*
2. **Build→deploy / distributed-system boundary** — does the autonomous team stop at
   per-component deploy-readiness (agent drives IaC at G5, human ratifies), or is
   running the distributed product-as-a-service explicitly out of charter? The charter
   says "code-building catalogue" but doesn't settle *distributed-system deploy*, so the
   referent is insufficient. *Scope/charter call.*

## The resolve-vs-surface lens (sample bank — not exhaustive)

The table above is **a sample of a lens we apply to every open item in every RFC, spec,
subagent, and skill design** — not a one-off. The lens IS the system's own surfacing
predicate, turned reflexively on our own design work:

> For each open item, find its **referent**. Referent-groundable — practice, a standard,
> precedent in this repo, an external system (omnigent / LangGraph / …), or the charter —
> → **resolve it yourself and cite the referent.** Only when the item is **value
> origination, irreversible-risk acceptance, or value-conflict adjudication** — or a
> referent-groundable item whose referent genuinely *failed* — → **surface it.**

Sample reads, to calibrate the boundary:
- "How is the backlog handled?" → **resolve** (referent: how product teams work — backlog
  feeds the builder one-by-one). *Should not have waited to be asked.*
- "Rejection/recovery transitions?" → **resolve** (referent: LangGraph checkpointers,
  plan-mode). Not a judgment call.
- "Rename the pack?" → **surface** (value/identity + adopter-irreversibility; no referent
  decides what we want to call our own surface).
- "Deploy the distributed system?" → **initially surfaced** (charter insufficient on
  distributed-deploy) → then **largely resolved** by the minimum-regret carve (RFC-0049:
  autonomous on ephemeral envs; human only at prod / irreversible exits). The lens isn't
  static — a new model (here, inner/outer loops + reversibility primitives) can convert a
  surface into a mostly-resolved call.
- *Proactive model-thinking (not strictly resolve-vs-surface, but the same self-thought):*
  "screens designed — now what?" → don't stop at per-screen output; **envision the
  verification mechanism** (make briefs consistent as a set, then wire a low-fi clickable
  prototype via an MCP tool, or a text-only steel thread, to test the whole before G4) and
  **reach for the tool** yourself. Logged from a user example (`0048-notes/07` §Consistency
  & prototyping). The tell: the model should reach for the next verification step
  unprompted.
- *Don't over-apply a cited finding — check its qualifier.* I read MAST as "single context
  beats a team" and banned lens-agents; the qualifier is "a team **that must coordinate**"
  (chat negotiation-to-consensus). A **supervisor + blackboard** lens-team doesn't
  negotiate — it's the proven topology, and it extends autonomy/parallelism at discovery
  scale. The tell: when a finding seems to forbid a whole approach, re-read its scope
  condition before banning. (Pressure test that corrected the orchestration model.)
- *Constraints are often loop-/context-scoped, not global.* The charter's "three reviewers
  ceiling" is a work-loop/code-review cap; the discovery loop legitimately has its own
  design-time lens roster (incl. a security/compliance lens distinct from the code
  `security-reviewer`). The tell: before treating a constraint as global, ask which
  context it was written for.

*Sample reads appended by child-1 — the `experience` pack ([RFC-0050](../0050-the-experience-pack.md)):*
- "Should `design-critique`'s taste mode become a reviewer **agent**?" → **resolve: no**
  (referent: ADR-0024 / RFC-0033 — the pack is all-skills-zero-agents *by decision*; the
  design-artifact live-lens reviewer is `core`/`architect`'s seat, RFC-0048 O5). The tell:
  a new capability tempts a new agent; check whether an existing posture decision already
  placed that seat elsewhere before adding one. *Scope-creep guard, resolved against
  precedent — not surfaced.*
- "Where do the `experience` artifacts get written?" → **resolve** (referent:
  `product-engineering`'s `frame-intent` layout pattern — `[<pack>]` table → `parent`
  default → discover-by-marker; default `docs/design`, paralleling `docs/product`). Never
  hardcode a path; the three-tier rule is the standing answer (RFC-0040).
- "How do I rename a *pack* with no alias field?" → **resolve** (referent: the *actual*
  `infra-contract-acquisition → contract-acquisition` rename, RFC-0047 § Errata — rename
  the live surface, bridge frozen governance in one new record, ship no alias). The tell:
  reach for the precedent that already shipped, not a new mechanism. *(RFC-0048 originally
  framed the rename mechanism as OQ1; the precedent resolved it.)*
- "Screens are inventoried — now what?" → don't stop at the screen list; **envision the
  whole-journey verification** (cross-brief consistency pass, then a low-fi clickable
  prototype via MCP or a text-only steel thread) and build it into the skill's procedure so
  the model reaches for it unprompted. Picked up from this note's own §Consistency &
  prototyping forward idea — the proactive-model-thinking tell, now realized in a skill.
- *Defer to the canonical floor, don't fork it.* notes/04's per-screen state set
  (`empty/loading/error/success/permission`) and the shipped `quality-floor` floor
  (`empty/loading/error/success/partial/disabled`) differ. → **resolve:** the per-screen
  brief *defers to the `quality-floor` floor* as the authoritative state set; `permission/
  denied` is an **additional gated-screen state**, not a replacement list. The tell: when a
  note introduces a list a canonical source already owns, reconcile to the source rather
  than shipping a second list free to drift. *(Drift reconciled in RFC-0050 D2/D4 per the
  provisional-foundation discipline.)*

**Why this is logged as a scaffold, not left to recall:** in practice the AI loop reaches
the right resolve-vs-surface call only ~half the time without a nudge (anchoring + the
knowing-doing gap — notes/03). So the lens is made an *explicit checklist step* (it lives
in the self-coverage gate, Decision 5: a "resolve-vs-surface" pass over every open item
before a design is declared converged), not a thing the model is trusted to remember.

**This is a living artifact — expectation set for the whole series.** Every effort in the
RFC-0048 series — each child RFC, spec, subagent, and skill design — is expected to (a)
run this lens in its self-coverage gate and (b) **append its own sample reads here**, so
the bank accretes calibration over time and the ~half-the-time hit rate climbs. The
samples above are a *starting* set, deliberately non-exhaustive. On RFC-0048 acceptance
the sample-bank graduates from this RFC note into the **self-coverage gate's reference
library** (its durable, cross-cutting home), since the lens applies repo-wide, not just to
this RFC.
