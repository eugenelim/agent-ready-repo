# How far can we move autonomously, and where do human gates pay for themselves

The design question reframed as economics: **gate where (probability the agent is
wrong) × (cost of that error compounding downstream) exceeds the cost of a human
check.** Everywhere else, let the agent run.

## The autonomy law (evidence-based)

**An agent runs unwatched exactly as far as it holds a verifier it can run itself.**

- *Where verifiers exist, autonomy is high and proven.* Claude Code's reliable
  loop is implement → run a verifiable check (tests/build/lint/screenshot) →
  read result → iterate. Anthropic's long-running-agent harness marks a feature
  "passing" only after the harness-enforced test gate — discipline lives in the
  harness, not the model. [Best practices for Claude Code; Effective harnesses
  for long-running agents.]
- *Where no verifier exists, agents fail at rates that forbid unwatched autonomy.*
  MAST (1,642 traces, 7 frameworks): 41–86% multi-agent failure, largest cluster
  is coordination/system-design. TheAgentCompany (CMU): best model 30.3% task
  completion; collapses on unfamiliar domains, multi-doc cross-reference, and
  reading-between-the-lines. [MAST arXiv:2503.13657; TheAgentCompany arXiv:2412.14161.]
- *Self-verification raises the floor but does not replace the human at a
  zero-verifier decision.* Reflexion +24 pts pass@1; Self-Refine +20% avg — but
  both fail without an external signal; pure self-critique anchors and can worsen
  output. [Reflexion arXiv:2303.11366; Self-Refine arXiv:2303.17651.]

**Corollary: autonomy is inversely proportional to error-compounding cost, which
is inversely proportional to verifiability.** High-altitude decisions (right
product? right domain? right scope?) have no local verifier and the largest blast
radius — a wrong Domain Framing poisons every screen, spec, and line below it.
Low-altitude decisions (does this function work?) have a cheap verifier (tests)
and a contained blast radius. So **human gates cluster at the top; agent autonomy
is greatest at the bottom.**

## Why errors compound (the token-burn mechanism)

Agents exhibit *myopic greedy commitment* — chain-of-thought optimizes the local
step and locks in early decisions; stronger reasoning doesn't fix it, it's
architectural [arXiv:2601.22311]. Combined with context anchoring and unverbalized
bias [arXiv:2510.19973; arXiv:2602.10117], a wrong high-altitude commitment is
then built on *consistently and confidently* — and the agent's own critique won't
catch it because the critique runs in the same anchored context. The error doesn't
announce itself; it multiplies. Every token spent after a wrong G1.5 anchor is
wasted, and the agent won't know. **This is the case for a human gate before the
spend, not a cap after it.**

## Risk-calibrated gate placement

| Gate | P(wrong) | Blast radius if wrong | Local verifier? | Verdict |
| --- | --- | --- | --- | --- |
| G0 Intake | med | total (everything inherits) | none | **HUMAN** |
| G1.5 Domain & MVP | **high** (agents hallucinate domains + over-scope — proven) | all features | none | **HUMAN — highest ROI gate** |
| G2 Convergence | med | N specs about to be built | none | **HUMAN** |
| G3 Spec | low–med | one feature, pre-build (cheap to revise) | adversarial + security review | auto unless risk trigger |
| G4 Build | med per task | one task, contained | **tests/lint/types** | **AUTO — run hardest here** |
| G5 Ship | low | irreversible (spend/public/IAM) | — | **HUMAN** |

The human gate's cost is *fixed and tiny* (one review); the error it prevents
*scales with everything built on top*. That asymmetry is the whole argument for
front-loading gates at G0/G1.5/G2 and trusting G4.

## The floor-raiser: a self-coverage gate (fixes the knowing-doing gap)

The gaps a human had to catch (ground the domain; hold MVP) are instances of the
agent failing to apply knowledge it already had. The structural fix is NOT "try
harder" — it's a required pre-convergence gate with non-skippable, externally-
grounded sections (recall→recognition; external scaffolds beat free recall):

| Step | Mechanism (evidence) | Blocks proceeding if… |
| --- | --- | --- |
| Domain-grounding table | taxonomy enumeration + research (WHO-checklist −36% complications) | any cell empty/"assumed" |
| Pre-mortem | prospective hindsight (+30% failure ID) | < N scenarios, untagged to design |
| Taxonomy walk | external dimension register (one para each) | any dimension blank |
| Saturation declaration | grounded-theory stop rule | declaration absent |
| Fresh-context adversarial | separate-context devil's advocate | any finding unresolved |

This raises the floor *between* human gates so the agent compounds fewer errors
unwatched — but it does not move a gate from HUMAN to AUTO, because self-critique
is unreliable at zero-verifier decisions (above).

## The Claude Code goal-structuring lesson

Plan mode works because it is a **capability constraint, not an instruction**:
the agent is structurally read-only until a human approves the plan — it *cannot*
skip breadth-before-commitment under anchoring. Two borrowable primitives: (a)
make the pre-convergence gate a hard state the agent cannot write past, not a
prompt; (b) run review in a **fresh context** so the reviewer isn't biased toward
what it just produced. Externalize the plan/goal as inspectable state (TaskCreate)
so coverage is recognition, not recall.

## Corrected gap inventory (folding the adversarial review)

**Roster-truth defect (CRITICAL):** the worked example marked `aws-bedrock-agentcore`,
`aws-cdk`, `aws-serverless-eda` as ✓ existing skills. They are NOT invokable skills
— `aws-bedrock-agentcore` is only a *reference file* inside `architect-diagram`;
the other two don't exist. The tech lens and G5 of the worked example rest
on skills that aren't there → the "only two things missing" claim is understated.
**Action:** re-audit every ✓ via `find packs -type d`; reclassify AWS items as
out-of-charter or net-new skills.

**New gaps surfaced this pass:**
- GAP-P5 self-coverage gate (the five-section primitive above).
- GAP-O11 outer-loop hard cap (MAST: termination needs cap AND saturation; proposal had only saturation — "iterate as long as possible" with no outer cap is the money-burn).
- GAP-O12 gate rejection/recovery transitions — what happens when the human says "no" at G0/G1.5/G2; today undefined (re-enter? bubble? invalidate which blackboard state?).
- GAP-O13 coordinator is specified only as a noun — define whether it's a skill, meta-skill, or agent; its state, turn structure, termination. Every orchestration gap depends on it.

## Adversarial verdict (forked-context review)

**Not yet RFC-ready.** Resolve first: (1) roster-truth defect; (2) coordinator
unspecified (GAP-O13); (3) gate recovery + outer cap (GAP-O11/O12). RFC-ready now:
the Experience pack (P1–P3) — real, correctly diagnosed, shippable standalone.
The convergence engine must NOT be RFC'd until the coordinator's contract, the
Domain Framing typed artifact (GAP-P4 — `research` applied mode does NOT emit it
for free), the scope-creep guard's mechanism (GAP-O10 — orphan-lint catches
structural orphans, NOT semantic over-scoping), live-lens review modes (GAP-O5 —
reviewers have no design-artifact mode today), and the engine's OWN charter-fit
(Principle 3: "a habit, not a tool") are answered.
