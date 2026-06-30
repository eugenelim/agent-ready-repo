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
| **A1** headless checkpoint/resume | consent-gate contract: write decision-brief to sidecar, status=awaiting-human → harness surfaces option-card → human verdict → decision-log → resume | omnigent human-in-the-loop pause; LangGraph checkpointer |
| **A2** harness-neutral decision schema | the decision-brief / option-card schema (gate · summary · decisions-requested · recommended · reversibility-class · artifacts); shipped doctrine | omnigent + our decision-log schema |
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
- *A child effort whose parent pre-decided the value calls should resolve, not re-surface.*
  Authoring the self-coverage gate's own RFC ([RFC-0051](../0051-the-self-coverage-gate.md)),
  the resolve-vs-surface pass over its open items landed on **surfacing nothing genuinely
  open** — every item (packaging, non-skippability mechanism, module set, light/full
  right-sizing, sample-bank home) was referent-grounded by RFC-0048 D5, RFC-0041, or
  `work-loop` itself. → **resolve.** The "land on nothing when research supports it" read,
  applied reflexively: a child must not re-litigate what the foundation already settled. The
  tell: when every candidate surface item traces to a referent the parent already cited, the
  honest output is a recommendation, not a question.
- *Blast radius, not topic, decides whether a naming call surfaces.* "Rename the **pack**
  `design-craft`→`experience`?" → **surface** (adopter-facing identity, mild irreversibility).
  "Name the internal `core` library `self-coverage`?" → **resolve** (the parent already calls
  it "the self-coverage gate"; an internal library name is not adopter-identity-defining and
  is cheaply changed). Same *kind* of question (what do we call our own surface), opposite
  routing — set by who sees the name and how reversibly. The tell: ask who the name is
  adopter-facing to before treating it as a value/identity call.
- *A mechanism gap is referent-groundable even when the precedent doesn't transfer verbatim.*
  "How is a gate made non-skippable when it runs in the **controller's own context**, where
  `operational-safety`'s inline-into-a-subagent-brief mechanism has no brief to inline into?"
  → **resolve** (referent: `work-loop`'s done-checklist already enforces non-skippable
  refusal items — reviewer-clean, doc-drift — by doctrine + a mechanical record, no runtime;
  the coverage record is one more of the same kind). The tell: when a cited precedent's
  *mechanism* doesn't fit, look for the *property* it delivers (here: a mechanical artifact
  the done-gate refuses to pass without) and find that property's nearest in-repo referent —
  don't escalate the gap to the human just because the first precedent didn't transfer.

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

*Sample reads appended by child-4 — the traceability lint ([`docs/specs/traceability-lint/`](../../specs/traceability-lint/spec.md)):*
- *A cited referent can say the reverse of what you claim it supports — the reviewer
  catches it, not the author.* (Child-4, the traceability lint.) I resolved "are the
  on-disk artifacts or the sidecar matrix authoritative?" in favor of artifacts and
  cited RFC-0048 D7 as the referent — but D7 says the **matrix** is the connectedness
  verifier. The fresh-context adversarial pass flagged it as a resolve-vs-surface
  violation (a referent-groundable item whose referent genuinely *failed*). Corrected
  to "matrix authoritative **when present**, derive from artifacts when absent" — which
  *aligns* with D7 and adds the standalone fallback as a tracked refinement. The tell:
  when you cite a referent to close an item, quote it — don't paraphrase it from
  memory into agreement.
- *Structure is mechanizable; "is it the right parent?" is not — and the split is the
  whole product.* (Child-4.) The lint resolves structural orphans (a node with no
  edge) and **refuses** semantic scope-creep (a node parented to the wrong outcome) —
  surfaced to the human at G1.5 (D6/O10). The tell: a presence check is a lint; a
  rightness check is a judgment — don't let a lint pretend to the second.
- *Find the artifact the ontology actually has, not the one the chain string implies.*
  (Child-4.) The chain reads `…capability→screen→action→service…`, but four of those
  are not files — `outcome`/`opportunity`/`capability` are rungs of one intent ladder,
  `action`/`service` are entries inside the journey/blueprint (note 04). The first
  draft modelled nine per-file nodes; the reviewer caught that four rows could never
  match. The tell: before keying a tool off "one marker per node", check the artifact
  inventory for which nodes are file-backed vs container-embedded.
- *Scope the tool to the topology the system actually runs, not the one the note
  scoped for convenience.* (Child-4.) Note 08 scoped the traceability sidecar to "a
  single monorepo" and deferred the cross-repo split; the first draft inherited that
  and would have false-flagged every cross-repo reference as a dangling edge. The
  user corrected it: the loops span repos (`work-loop` per-module;
  `discovery-loop`/release-loop cross-module). The fix wasn't to invent
  cross-repo plumbing — it was to (a) link **by convention/stable-id, not path**
  (the invariant of every cross-boundary traceability system — OSLC URI, purl,
  Backstage `kind:namespace/name`, SLSA digest) and (b) **reuse the value-stream
  mechanism already decided in ADR-0022** (reference-by-version + courier snapshot +
  rollup), reconciling the drift back into RFC-0048. The tell: when a tool's scope
  note says "single repo / deferred", check whether the *system's own loops* already
  cross that boundary — and research the established cross-boundary pattern before
  designing one. (Pressure test that reframed the whole spec; logged with a wide
  prior-art sweep in the spec's `notes/`.)

*Sample reads appended by child-5 — the coordinator contract ([RFC-0053](../0053-the-discovery-loop.md)):*
- *When the parent says "empirical, not paper," building the artifact IS the resolution —
  describing it is the failure the parent pre-named.* (Child-5.) RFC-0048 D7 asked for "a
  prototype ... not a paper design." The temptation was to author the RFC *asserting* the
  note-09 resolutions hold. → **resolve by running it:** instantiate the four sidecar files
  for the worked example, walk the loop injecting the two named failure modes, and run a
  ~60-line lint over the typed state. The lint flagging real orphans pre-recovery and
  reporting converged after is the difference between "we think it's checkable" and "it is."
  The tell: when a parent demands empirical confirmation, prose that claims confirmation is
  exactly the thing it was warning against — produce the runnable artifact.
- *Calibrate the verb to the evidence; keep the strong verb only for the reproducible part.*
  (Child-5.) The spike was one example, one operator, and the outer cap converged early so
  its stall path was never hit. The draft BLUF said "confirmed the no-engine framing." The
  fresh-context adversarial pass flagged the BLUF/Evidence running ahead of the spike's own
  Threats section. → corrected to "demonstrated on one worked example (single operator, not
  replicated) **plus a reproducible connectedness lint**" — strong verb retained only for the
  part that actually reproduces. The tell: "confirmed / demonstrated / refuted" are
  load-bearing; check each against what the artifact supports, and never let the headline
  outrun the threats-to-validity you already wrote.
- *Detect-and-degrade is right for a capability lens and wrong for a safety lens on a
  safety-relevant artifact.* (Child-5, from the spec-stage security pass.) The security/
  compliance lens was "optional detect-and-degrade" like the others — but the worked
  example's whole ripple is a prompt-injection-self-modification finding, so a missing
  security lens would ship the boundary un-reviewed *silently*. → **resolve: a
  non-degradable floor** — tie the lens to a risk trigger; a security-boundary crossing with
  no lens installed *surfaces to the human* rather than degrading quietly. The tell: before
  reusing "optional detect-and-degrade" for a lens, ask whether the lens is a *capability*
  (degrade is fine) or a *safety control* (degrade needs a surfacing floor).
- *The same primitive that scopes a blast radius can amplify it — ask who benefits if they
  can drive it.* (Child-5.) Cascade-invalidation by traceability edges was framed purely as
  a safety property (it *bounds* a rejection). The security pass noted it is also a
  denial-of-convergence lever: a poisoned high-fan-out edge could invalidate the whole
  blackboard and burn the budget. → **resolve: a circuit-breaker** (fan-out threshold
  surfaces; re-runs count against the budget). The tell: when you describe a mechanism as a
  safety property, run the adversary's read of the same mechanism before declaring it safe.
- *Don't cite a backstop weaker than the failure it is invoked against.* (Child-5.) The RFC
  leaned on child-4's traceability lint as the backstop against an under-implemented sidecar
  — but the spike's demonstrator is a *presence* check, which a fabricated-edge or
  disconnected-subtree failure passes. → **resolve: name a child-4 root→leaf *reachability*
  AC** so the backstop can actually detect the failure, and flag the dependency so the claim
  isn't load-bearing on the weaker check. The tell: when you cite a check as a mitigation,
  confirm it detects the specific failure you're mitigating, not merely a related one.

*Sample reads appended by RFC-0049's child spec — the release loop ([`docs/specs/release-loop/`](../../specs/release-loop/spec.md)):*
- *When the parent pre-decided the value call, resolve the mechanics; surface only the
  residual taste.* (Integration-loop spec.) RFC-0049 carried two OQs (pack home, agent shape)
  with referent-grounded recommended defaults. The temptation was to re-open them as
  decisions for the human. → **resolve both per the defaults** (opt-in pack, not core, by the
  `discovery-lead`-in-`product-engineering` symmetry; distinct agent by the inner/outer split
  + the RFC-0053 precedent), and surface **only** the one genuinely-aesthetic residual — the
  pack *name* — as overridable. The tell: an OQ whose recommendation is grounded in a
  precedent the parent already accepted is a resolve, not a surface; isolate the sub-part that
  is pure taste and surface only that.
- *A copied control contract is necessary but not sufficient when the boundary moved.*
  (Integration-loop spec, from the spec-stage security pass.) AC10 faithfully mirrored
  RFC-0053's seven upstream integrity controls — and the security pass still found three gaps,
  because the *downstream* deploy loop crosses boundaries the *upstream* design loop never did
  (deploy credentials, ephemeral-env tenancy, deployed-artifact provenance). → **resolve: add
  the boundary-specific controls** (credential tiering so the autonomous zone *cannot*
  authenticate to the irreversible tier; env-isolation as a *carve precondition*, not just a
  reviewer lens; artifact-digest provenance across the G4→deploy handoff). The tell: when you
  port a contract across a seam, re-run the boundary inventory for the new side — "mirrors the
  sibling" proves parity, not sufficiency.
- *A label that does load-bearing safety work must name the condition that makes it true.*
  (Integration-loop spec.) The carve called the ephemeral outer loop "reversible" and ran it
  unwatched — but reversibility of the *deploy* says nothing about *isolation* of the env it
  targets. → **resolve: condition the label** — "reversible" holds only while the env is
  network/data-isolated from prod, holds no real data, and can't reach prod state; a target
  that can't be proven isolated is itself a consent-gate crossing. The tell: when a one-word
  classification (`reversible` / `safe` / `internal`) gates autonomy, write down the
  precondition that earns the word, or an agent will apply it where it doesn't hold.

*Sample reads appended by the RFC-0048 foundation reconciliation discharge — the composed-set
reconciliation ([`0048-notes/10`](10-composed-end-to-end-walkthrough.md); RFC-0048
§ Amendments 2026-06-26):*
- *A "resolved-by child X" is an orphan, not a resolution, when X closed without binding it.*
  Two children each deferred the `docs/discovery/` layout key to "the other one" — the
  frame-domain spec deferred it to "the experience-pack / layout child effort," and child-1
  (RFC-0050) bound only `[experience]→docs/design` and never touched it. The temptation was to
  read "deferred to a named effort" as closed. → **resolve by re-checking the target actually
  bound it**, and when it didn't, **assign a concrete owner** (RFC-0053's implementing spec, the
  sidecar-path owner). The tell: a deferral pointer is only discharged if you open the target and
  confirm it landed — "owned by a named effort" that closed without acting is still owned by nobody.
- *Freeze the reading-source, not just the downstream consumer.* The canonical chain terminus
  was reconciled to `component` in the traceability-lint spec, but note 02 — a canonical
  freeze-reading source — still said `code`. → **resolve by amending the source note too**, not
  only the spec that consumes it. The tell: when a reconciliation lands in the consumer, grep the
  *reading sources* an implementer is told to read at freeze; a stale source sends them down the
  pre-reconciliation path the consumer already abandoned.
- *Two siblings each shipping a default for the same artifact is resolved by which **context**
  each default serves, not which default wins.* `docs/design/` (RFC-0050, standalone) vs
  `docs/discovery/<initiative>/` (note 08, in-initiative) for the journey/blueprint/screens. →
  **resolve by context-conditioning** (in-initiative → discovery tree supplied by `discovery-lead`;
  standalone → `docs/design`), since both are legitimate and the three-tier resolve + marker make
  both reachable. The tell: when a "which path wins" conflict appears between two correct authors,
  ask whether they are serving *different invocation contexts* before picking a winner.
- *When wording collides, the statement that names itself a decision outranks prose that
  paraphrases it.* "No new reviewer *agent* … a mode, not a new agent" (Decision 2) vs "a
  different agent" (D7/D8, RFC-0053 D5). → **resolve to Decision 2** (the explicit ruling) and
  correct the prose to "a different *lens/invocation*." The tell: a contradiction between a
  decision and a description is not a 50/50 — the decision is the referent; reword the description.
- *Don't let an inventory assert as already-true an invariant its own backstop can't yet check.*
  Note 04's "no orphans" header, while the traceability lint cannot yet walk the unbound
  `Discovery:` edge and a persona/producer gap existed. → **resolve by rewording to target-state
  + naming the open seams**, not by deleting the goal. The tell: a guarantee stated as fact masks
  exactly the seams a reviewer must find; phrase it as "the lint enforces this once edge X lands."
- *Freeze-readiness for a provisional foundation = coherence + every seam owned, not every
  follow-on built.* The discharge faced six Blocker-tagged findings yet both fresh-context passes
  said SHIP WITH CHANGES, because each was a seam-wiring/owner-assignment item the provisional
  mechanism exists to absorb. → **resolve: fold each into a tracked amendment that resolves +
  assigns an owner, then freeze** — do not wait for the owed specs to ship. The tell: a foundation
  RFC is "aligned" when nothing is owned-by-nobody and the spine is internally consistent; the
  named follow-ons land on their own lifecycles and are not freeze preconditions.

*Appended by RFC-0053's implementing PR (child-5 — the discovery-loop build):*

- *Making `product-engineering` ship agents (it was "pure-markdown") is resolve, not
  surface.* Adding `discovery-lead` + the two discovery reviewers makes the pack ship agent
  primitives for the first time. → **resolve** (referent: the `experience` pack already ships
  `experience-reviewer` at user scope with `allowed-adapters` and `[pack.adapter-contract]`
  unchanged — the precedent settles both the posture and the no-bump). The tell: a "first of its
  kind for this pack" change is still referent-grounded when a sibling pack already did it.
- *A spec AC that asserts a dependency's behaviour can be a failed referent.* AC34 states "the
  shipped [child-4] lint performs a root→leaf reachability pass"; the shipped lint actually does
  per-node edge-**presence** (confirmed in `classify_sidecar` and the `traceability.preconverge.json`
  fixture comment). → **surface as a cross-spec finding** (the referent the AC names says the
  opposite of the AC's claim) — name the reachability dependency as AC34 requires *and* flag that
  the current backstop is presence-level until child-4 adds reachability. The tell: quote the
  referent (the code + the fixture), don't trust the AC's own description of it.
- *A core-pack format edit that adds a user-facing field is a release decision → surface.* DRIFT-G
  adds the optional `Discovery:` spec header to `new-spec` + CONVENTIONS § 4 (core). → **surface**
  the core-release decision (does this user-facing addition warrant a `core` bump + changelog?) —
  the implementing PR makes the additive, backward-compatible edit, but cutting the release is the
  owner's call. The tell: discharging an in-scope AC doesn't auto-authorize a published-package
  version bump; name it.
- *An ungated coverage gap is a tracked follow-up, not a blocker → resolve.* The three new skills
  are not added to `[pack.evals]` / ship no `eval_queries.json`. → **resolve** (referent:
  `frame-domain` — a newer PE skill — already ships without eval coverage and no gate enforces
  allowlist completeness); record eval coverage as a tracked follow-up. The tell: a missing-but-
  ungated quality item matching an existing precedent is a backlog entry, not a stop.
- *Discharging an RFC's acceptance blockers enables, but does not authorize, the status flip →
  surface.* This PR resolves RFC-0048's last open blockers (DRIFT-G, AC0, the backlog ACs), and the
  acceptance note says "Open → Accepted is a one-line status change." → **surface** the Open→Accepted
  flip to the owner rather than making it in the implementing PR. The tell: clearing the precondition
  for a governance status change is not the same as being authorized to make it.

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
