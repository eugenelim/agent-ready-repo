# adopter-persona — brief

**Bottom line:** The Level B pack set has six primary adopter segments across
two orthogonal dimensions — arrival pathway and role/altitude identity — that
fail in structurally different ways and cannot share a single onboarding flow.
The enterprise rollout playbook requires three distinct tracks (technical,
enterprise, non-technical), not the two originally identified. Nine cross-segment
design requirements address the most consistent failure patterns in the corpus.
A seventh segment (mid-market enterprise) is named but uncharacterised and is
the highest structural churn risk in the portfolio.

---

## What the evidence shows

### On the segmentation model

- **Arrival pathway and role/altitude identity are orthogonal dimensions; the
  round-1 FDE/solo binary described pathways, not personas.** A solo engineer
  can arrive without an FDE and occupy any task posture. An FDE client can be
  an AI-naive knowledge worker or a technical PM. Collapsing the two into one
  dimension produces a synthesis that answers "how do adopters arrive?" but not
  "who are the adopters?" — the two questions the P5 deliverables require.
  [high — adoption pathway and role identity coded separately across 13 sources;
  no source merged the two dimensions; segmentation survey explicitly coded
  posture as independent of pathway]

- **Six primary segments emerged from open-coding; five were not characterised
  in round-1.** Round-1 characterised FDE-mediated enterprise and solo engineer.
  Round-2 adds: technical PM / product engineer (altitude 1), AI-naive knowledge
  worker (altitude 0–1), enterprise AI champion (altitude 0–1), and UX /
  experience designer (altitude 2). Each segment has a distinct binding
  constraint, first-value shape, failure mode, and sustainability mechanism.
  [moderate — all six segments documented; no direct comparative study; role
  characterisations are secondary and desk-research sources, not participant
  observation]

### On binding constraints — not additive

- **Each segment has exactly one primary binding constraint; solving for multiple
  simultaneously is not possible without tracking separation.** Outcome-first
  vocabulary helps solo engineers (reduces activation window consumption) and
  AI-naive professionals (reduces cognitive load), but lowers trust for enterprise
  champions (reads as product immaturity). Preview-confirm flows are essential
  for FDE clients and governance-extras adopters, but their friction may abandon
  solo engineers within the 15-minute activation window.
  [high — binding constraint × segment matrix coded across all 13 sources;
  no source generalised one constraint across all segments; four-zone constraint
  model consistent with round-1 findings]

- **The FDE model achieves 60–80% automation rates; self-service achieves ~20%.
  The gap is structural, not marginal.** The primary variable is whether the client
  receives a human specialist during deployment. FDE-mediated deployments absorb
  installation friction; self-service deployments require the user to bear it.
  [moderate — SaaStr practitioner analysis; consistent across fde.academy,
  Baseten engineering blog, Everest Group; no RCT-level evidence]

- **95% of GenAI pilots fail to produce measurable business value.** For the
  enterprise AI champion, this is a career-consequential fact: 12+ months of
  production evidence is required before vendor selection; board-ready proof within
  one budget cycle is the binding first-value shape.
  [moderate — MIT NANDA 2025 (N=300+ enterprise GenAI deployments); directionally
  consistent with BCG AI at Work 2025, AI Assembly Lines practitioner analysis;
  no published methodology for the NANDA figure]

### On verification burden — universal churn mechanism

- **Inability to quickly verify output quality is the primary churn mechanism
  across all six segments, with distinct failure signatures.** Solo engineers:
  "almost right but not quite" debugging overhead reverses productivity gain
  (Stack Overflow 2025: 66% cite this; 45.7% distrust accuracy). AI-naive
  professionals: mental simulation of agent steps doubles effort (arXiv
  2505.17767). UX designers: identical prompts produce incompatible designs;
  output dismissed as "templatized" (NN/G 2024). FDE clients: cannot verify
  what the FDE produced post-handoff (Palantir Phase 3 documentation).
  [high — ≥5 independent sources from different disciplines; verification burden
  appears independently in each segment characterisation]

- **The remediation that works across segments: constrain the first task to a
  domain the adopter already knows well enough to verify in minutes.** Grippo
  practitioner case: UX designer's first value was a compressed synthesis of
  interviews they had already read. Microsoft WorkLab (Dow case): first
  deliverable was a white paper on a domain the user owned. Stripe/Vercel TTFHW
  benchmarks: outputs users can immediately confirm work (payment processed, site
  is live). This produces session-one trust regardless of segment.
  [moderate — practitioner consensus across disciplines; no controlled study
  isolating task-scoping as the causal variable]

### On peer adoption — universal accelerant

- **Peer adoption consistently outperforms top-down mandates and vendor onboarding
  across all six segments.** Solo engineers: 78% primary discovery through peer
  recommendation; 52% via dark social (Slack/Discord) (daily.dev practitioner
  research). AI-naive professionals: consulted workers adopt; mandated workers
  resist (CHI 2025). Enterprise champions: champion programmes (1:15–25 ratio)
  deliver 2.1× higher sustained usage vs. top-down mandate (AI Assembly Lines;
  directionally consistent with BCG AI at Work 2025). UX designers: practitioner
  case more trusted than product marketing (NN/G 2024; Grippo case).
  [high — triangulated across 4+ independent sources from different disciplines;
  directional consistency is very strong across all segments]

### On professional identity threat — three-segment concern

- **Professional identity threat appears in three of six segments at different
  registers, not only in non-technical tiers.** AI-naive knowledge workers:
  deskilling fear; junior roles' growth path threatened; employees at AI-advanced
  organisations are MORE worried about job security (46% vs. 34% at lagging orgs)
  (BCG AI at Work 2025, N=~150,000). UX designers: craft devaluation; junior
  designers report higher threat perception than seniors (3.02/5 vs. 2.656/5)
  (arXiv 2603.05848). Technical PM/PE: authorship ambiguity (who authored the
  strategy if AI generated the brief?) — implicit in the gate-based-review
  adoption pattern.
  [moderate — well-documented for AI-naive and UX segments; inferred for PM/PE;
  no cross-segment comparative study]

### On the mid-market gap

- **The mid-market enterprise segment is the highest structural churn risk and
  is uncharacterised in the corpus.** Three independent sources name the gap:
  (1) FDE deployment patterns: "clients sold on quick FDE-assisted implementation
  who instead receive self-service documentation struggle and churn"; (2) round-1
  brief: "mid-market or less-resourced enterprise — sold on FDE-level outcomes,
  given self-service documentation — is the highest churn risk"; (3) fde.academy:
  FDE model threshold is ~5,000+ employee organisations.
  [high — gap existence confirmed by 3 independent sources. Segment
  characterisation: none — not researched]

---

## Segment profiles

### Segment 1 — FDE-mediated enterprise
**Binding constraint:** handoff quality — can the client operate independently
after the FDE exits? Four failure modes: knowledge vacuum, custom-integration
orphaning, silent system degradation, escalation-chain breakdown.
**First value:** client executes one pack task independently before engagement
closes.
**High-priority packs:** atlassian, figma (credential lifecycle); governance-extras,
user-guide-diataxis (vocabulary recurs in every artifact post-handoff).

### Segment 2 — Solo engineer
**Binding constraint:** time budget — 60–80% dropout before activation; 68%
cite "too much setup time"; sub-15-min TTFHW target.
**First value:** working result within the activation window; shareable result
for client-facing engineers.
**Lowest friction entry:** product-strategy (`write-prfaq`) — no credential,
no configuration, explicit starter prompt.

### Segment 3 — Technical PM / product engineer
**Binding constraint:** mental model shift from reactive prompting to
declarative orchestration; gate-based review vs. per-sentence checking is the
threshold.
**First value:** structured brief the engineering team can act on without a
sync meeting — cross-team handoff, not individual productivity.
**Vocabulary bridge:** brief, initiative, spec, appetite, shaping (Shape Up/OKR
native). Vocabulary barrier: skill, pack, workspace-as-context, invoke,
orchestrate.

### Segment 4 — AI-naive knowledge worker
**Binding constraint:** verification burden (mental simulation of agent steps
doubles effort) + professional identity threat (deskilling fear for junior roles);
2-week activation window.
**First value:** visible, shareable deliverable in session one — not a
capability tour. Peer champion is the activation mechanism.
**Adoption mechanism:** consulted workers adopt; mandated workers resist (CHI
2025).

### Segment 5 — Enterprise AI champion
**Binding constraint:** career-risk management; 95% of GenAI pilots produce
zero measurable return; four personal risk vectors (pilot failure, budget
overrun, regulatory exposure, adoption stall).
**First value:** board-ready proof within one budget cycle.
**Sustainability mechanism:** named internal owner at engagement close +
documented workflow operating guide + prompt library + measurement log.

### Segment 6 — UX / experience designer
**Binding constraint:** craft integrity — generic-output barrier (AI output
"templatized," below professional standard); articulation barrier (can't
describe a good journey map to AI); inconsistency barrier (identical prompts →
incompatible designs).
**First value:** compressed research synthesis → structured journey map with
emotion scores, tagged quotes, pain points. Designer retains strategic
authorship.
**Entry point:** Figma (familiar environment, plugin-shaped integration) is the
Trojan-horse integration for experience-design.

### Segment 7 — Mid-market enterprise (uncharacterised)
Named but not characterised. FDE scale threshold: ~5,000+ employee organisations.
Mid-market accounts sold on FDE-level outcomes but given self-service
documentation. Churn risk is the highest in the portfolio. No viable self-serve
path for enterprise-complexity packs (atlassian, figma, governance-extras) has
been characterised; the rollout playbook must name this gap honestly.

---

## Three-track rollout requirement

A single onboarding flow cannot address binding constraints that are
structurally incompatible. Minimum three tracks:

**Technical track** (solo engineer + technical PM/PE): outcome-first vocabulary
for the activation window; gate-based review vocabulary for the mental model
shift; constrained first task on a real problem.

**Enterprise track** (FDE client + enterprise champion): handoff documentation
completeness; governance depth for trust; measurement infrastructure; champions
programme before org-wide rollout.

**Non-technical track** (AI-naive professional + UX designer): constrained
first task the user can verify; peer champion in the same role; identity-safe
framing ("AI amplifies your expertise"); shareable deliverable in session one.

---

## Nine cross-segment design requirements

**Five from round-1 (apply to all six segments):**

1. **Prerequisites at the decision point, not on failure.** "Do you have X?"
   before the attempt; a blocking error mid-attempt burns both the activation
   window (solo) and the client's confidence (FDE).
2. **Outcome-first vocabulary at every entry point.** Plain-language outcome
   label before internal pack terminology. All Level B packs.
3. **Explicit artifact status in every receipt.** Chat-only OR exact path,
   stated — never implied. Affects architect (concept), converters (output
   file), figma (render vs. remote), governance-extras (ADR/RFC path + index).
4. **Credential lifecycle documentation.** Atlassian OAuth refresh tokens
   expire after 90 days of inactivity; Figma OAuth access tokens expire after
   90 days unconditionally. Re-authentication section (trigger, steps, storage
   location) is required in both packs.
5. **Mutation status stated, not implied.** "No Figma changes made" / "no Jira
   items modified" in every read-only receipt. Verified post-fix for figma;
   atlassian requires equivalent treatment.

**Four from round-2 (triangulated across ≥3 independent sources):**

6. **Constrain the first task to a domain the user can verify in minutes.**
   The user must know enough to confirm the output is right; this is the
   universal remediation for verification burden as a churn mechanism.
7. **Name human control points explicitly.** "You decide here" moments must be
   visible by design; loss-of-controllability anxiety is present in AI-naive and
   UX segments and must be remediated structurally, not in copy.
8. **Peer-champion the demo and onboarding.** Peer discovery is primary for
   engineers (78%); champions programmes deliver 2.1× for enterprise; practitioner
   case beats product marketing for designers; consulted workers beat mandated
   workers for AI-naive professionals. The demo should be peer-shaped, not vendor-shaped.
9. **Frame value at the shareable artifact, not at system capability.** Each
   segment's first value is defined by who they share the artifact with. The demo
   must end at the sharing moment: the brief the engineer acts on, the metric the
   board reviews, the journey map presented at the design review.

---

## Known unknowns

- **Known-unknown:** What is the mid-market enterprise segment's binding
  constraint? Is it inherited from the FDE model, inherited from the solo
  model, or a third structural form? Would be closed by: FDE practitioner
  interviews + mid-market self-serve attempt sessions. Until closed: the
  rollout playbook must name this as an unresolved track, not promise a path
  that doesn't reliably succeed.

- **Known-unknown:** Does a non-technical enterprise client trust and act on
  the governance-extras preview-confirm flow without external reassurance? The
  mechanical fix documented the cues; client first-use trust is unverifiable
  without participant observation. Would be closed by: a moderated first-use
  session with a non-technical governance-extras adopter.

- **Known-unknown:** What proportion of Level B deployments are FDE-mediated
  versus self-service? No activation or deployment-pathway data exists. Would
  be closed by: deployment telemetry or FDE practitioner survey.

- **Known-unknown:** Does the technical PM/PE segment's authorship-ambiguity
  identity concern require explicit design remediation? The pattern is inferred
  from gate-based-review adoption; it is not directly observed. Would be closed
  by: structured interviews with practitioners who use agent-skills platforms
  for brief generation.

- **Unknowable:** Which provisional segment labels adopters will self-identify
  with before experiencing the product. Segment identity is behavioural and
  contextual; self-identification cannot substitute for observed task behaviour.

- **Unknowable:** Whether the nine cross-segment design requirements will hold
  stable as pack designs change in response to these findings. The requirements
  are inferred from documentation and secondary research; they will require
  revision as the product evolves and as participant observation data becomes
  available.
