# Comparison matrix — adopter-persona (round 2)

**Verdict:** The Level B pack set has six primary adopter segments across two
orthogonal dimensions. Arrival pathway (FDE-mediated vs. self-directed) and
role/altitude identity are independent; the round-1 FDE/solo binary described
pathways, not personas. These segments fail in structurally different ways; a
single onboarding flow cannot serve all six. Nine cross-segment design requirements
address the most consistent patterns. The enterprise rollout playbook requires
three tracks, not two. Mid-market enterprise is a seventh, uncharacterised segment
and the highest structural churn risk.

---

## Segment profiles across dimensions

### Arrival pathways

| Segment | Arrival | Controls installation | Binding constraint |
|---|---|---|---|
| **FDE-mediated enterprise** | FDE installs/configures on behalf of client org | FDE (external) | Handoff quality: can client operate independently after FDE exits? |
| **Solo engineer** | Self-installs; installer = end user in one person | Self | Time budget: 5–15 min activation window before abandonment |

### Role / altitude identities

| Segment | Altitude | Primary packs | Binding constraint |
|---|---|---|---|
| **Technical PM / product engineer** | Altitude 1 (initiative shaping) | product-engineering, workspace.toml, shaping queue | Mental model shift: reactive prompting → declarative orchestration |
| **AI-naive knowledge worker** | Altitude 0–1 (strategy/research) | product-strategy, desk-research | Verification burden + professional identity threat |
| **Enterprise AI champion** | Altitude 0–1 (strategic oversight) | Cross-pack | Career-risk management; 95% of GenAI pilots produce zero return |
| **UX / experience designer** | Altitude 2 (project/design) | experience-design, figma | Craft integrity: generic-output and articulation barriers |

---

## Full segment comparison

### FDE-mediated enterprise

| Dimension | Characterisation |
|---|---|
| **Binding constraint** | Handoff quality — CoE resourcing (7 named permanent roles); FDE absorbs installation friction but not vocabulary transfer |
| **First-value shape** | Client operates one pack task independently after FDE exits; one client-independent run before engagement closes |
| **Vocabulary bridge/barrier** | Bridge: determined by what FDE translates before exit. Barrier: any pack vocabulary the FDE didn't cover = post-handoff blocker |
| **Trust mechanism** | FDE absorbs installation trust; post-handoff trust rebuilt from documentation alone |
| **Failure modes** | Four: knowledge vacuum, custom-integration orphaning, silent system degradation, escalation-chain breakdown |
| **Sustainability driver** | Named domain owners who are "long-term participants"; not rotational staff |
| **High-priority packs** | atlassian, figma (credential lifecycle); governance-extras, user-guide-diataxis (governance maintenance) |

### Solo engineer

| Dimension | Characterisation |
|---|---|
| **Binding constraint** | Time budget: 60–80% dropout before activation; 68% cite "too much setup time"; sub-15-min TTFHW target |
| **First-value shape** | Working result within 15 min on a real problem; for client-facing: result the client can evaluate |
| **Vocabulary bridge/barrier** | Bridge: peer vocabulary; coding-assistant vocabulary. Barrier: agent/pack vocabulary; required config steps |
| **Trust mechanism** | Peer discovery (78% primary channel); 5+ doc pages = 340% conversion lift; tangible result on real problem |
| **Failure modes** | Motivation decay; vocabulary exploration and configuration consume the activation window before first value |
| **Sustainability driver** | Competitive advantage for client-facing engineers; peer community |
| **Lowest-friction entry** | product-strategy (write-prfaq) — no credential, no configuration, explicit starter prompt |

### Technical PM / product engineer

| Dimension | Characterisation |
|---|---|
| **Binding constraint** | Mental model shift: chat-assistant ("AI answers") → agent orchestration ("AI acts"). Gate-based review vs. per-sentence checking is the threshold |
| **First-value shape** | Structured brief that the engineering team can act on without a sync meeting — cross-team handoff, not individual productivity |
| **Vocabulary bridge/barrier** | Bridge: brief, initiative, spec, appetite, shaping (Shape Up/OKR native). Barrier: skill (as primitive), pack, workspace-as-context, invoke, orchestrate |
| **Trust mechanism** | Cross-team handoff quality: the brief that eliminates a sync meeting is proof-of-value; gate-based review teaches trust through doing |
| **Failure modes** | Workflow inertia: installs agent skills platform, continues drafting in ChatGPT; unclear which skills to invoke when |
| **Sustainability driver** | Stage-progression: 0.5 (chat user) → 0.7 (templated assistant) → 1.0 (gate-based orchestration); each stage is self-reinforcing once crossed |
| **Primary packs** | product-engineering, workspace.toml, shaping queue; product-strategy as low-friction first entry |

### AI-naive knowledge worker

| Dimension | Characterisation |
|---|---|
| **Binding constraint** | Verification burden (mental simulation of agent steps = doubled effort) + professional identity threat (deskilling fear for junior roles); 2-week activation window |
| **First-value shape** | Visible, shareable deliverable in session one — completed research summary, drafted brief, strategic document. Not a capability tour |
| **Vocabulary bridge/barrier** | Bridge: familiar output types (research summary, brief, analysis). Barrier: all agent/platform vocabulary (prompting, pipeline, schema, invoke, orchestrate) |
| **Trust mechanism** | (1) Empathy-grounded approach (start with worker's problem, not org's efficiency goal). (2) Meaningful consultation: consulted workers adopt; mandated workers resist (CHI 2025) |
| **Failure modes** | Reliability anxiety (44% cite hallucination) + identity threat cause early abandonment; cognitive load from prompting overhead exceeds manual speed |
| **Sustainability driver** | Session-one value + explicit reason to return for session two; peer champion in role-proximate position |
| **Primary packs** | product-strategy (write-prfaq — standalone, no dependencies, clear starter task); desk-research |

### Enterprise AI champion

| Dimension | Characterisation |
|---|---|
| **Binding constraint** | Career-risk management: 95% of GenAI pilots produce zero measurable return (MIT NANDA 2025, N=300+); four personal risk vectors (pilot failure, budget overrun, regulatory exposure, adoption stall) |
| **First-value shape** | Board-ready proof within one budget cycle (weeks, not quarters); 12+ months of production evidence required before selection; 4-week-to-production benchmark |
| **Vocabulary bridge/barrier** | Bridge: governance, compliance, ROI, TCO framing. Barrier: outcome-first framing without governance depth reads as immature product; vendor lock-in risk |
| **Trust mechanism** | Champions programme (peer-led, 1:15–25 ratio) delivers 2.1× higher sustained usage vs. top-down mandate; measurement infrastructure the champion can present upward |
| **Failure modes** | IBM Watson Health pattern: technology championed top-down without frontline validation; adoption stall at sub-20% active usage is a reputational write-off |
| **Sustainability driver** | Named internal owner at engagement close; documented workflow operating guide + prompt library + measurement log; internal champions network |
| **Role in pack adoption** | Cross-pack; drives all Level B pack adoption decisions; feeds enterprise rollout playbook directly |

### UX / experience designer

| Dimension | Characterisation |
|---|---|
| **Binding constraint** | Craft integrity: generic-output barrier (AI results "templatized," below professional standard); inconsistency barrier (identical prompts → incompatible designs); articulation barrier (can't describe a good journey map to AI) |
| **First-value shape** | Compressed research synthesis → structured journey map with emotion scores, tagged quotes, pain points; designer retains strategic authorship; AI removes collation work |
| **Vocabulary bridge/barrier** | Bridge: journey map, JTBD, screen brief, persona, affinity map, Figma, plugin, method, framework. Barrier: skill, pack, agent, pipeline, invoke, schema |
| **Trust mechanism** | (1) Source provenance disclosure. (2) Peer/social proof (Grippo practitioner case > product marketing). (3) "Digital prosthetic" framing: AI amplifies craft |
| **Failure modes** | Generic-output rejection at first use; verifiability-first adoption means journey maps (0.5% adoption rate) are the last thing attempted, not the first |
| **Sustainability driver** | Collation/synthesis removed while strategic authorship preserved; "anxious amplifier" posture becomes stable amplifier when first-value is confirmed |
| **Entry point** | Figma (familiar environment, plugin-shaped integration) as Trojan-horse; experience-design pack for core workflow |

---

## Cross-segment patterns

### Four binding-constraint zones (solving for one may harm another)

| Zone | Segments | Key tension |
|---|---|---|
| **External / engagement** | FDE client, champion | Governance depth and preview-confirm build trust here; same interventions add friction that abandons the time-constrained solo engineer |
| **Resource / time** | Solo engineer | Outcome-first vocabulary helps here and for AI-naive; champion reads it as product immaturity |
| **Cognitive / mental model** | Technical PM/PE | Gate-based review teaching requires sustained engagement; no 15-min equivalent |
| **Identity / epistemic** | AI-naive, UX designer | Peer champion + constrained first task is the primary intervention; efficiency framing actively harms |

### Nine cross-segment design requirements

**From round-1 (five — apply to all six segments):**
1. **Prerequisites at the decision point, not on failure** — "Do you have X?" before the attempt, not as an error message
2. **Outcome-first vocabulary at every entry point** — plain-language outcome label before internal pack terminology
3. **Explicit artifact status in every receipt** — chat-only OR exact path, stated, never implied
4. **Credential lifecycle documentation** — re-authentication steps (trigger, steps, storage location) as a named, findable section in atlassian and figma
5. **Mutation status stated, not implied** — "No Figma changes made" / "no Jira items modified" in every read receipt

**From round-2 (four — triangulated across ≥3 independent sources each):**
6. **Constrain first task to a domain the user can verify in minutes** — user must know enough to confirm the output is right; removes verification burden as adoption barrier
7. **Name human control points explicitly** — agent paradigm requires visible "you decide here" moments; loss-of-controllability anxiety requires remediation by design
8. **Peer-champion the demo and onboarding** — peer discovery primary for engineers (78%), peer champions 2.1× for enterprise; practitioner case > marketing claim for designers
9. **Frame value at the shareable artifact, not at the system capability** — each segment's first value is defined by who they share it with; the demo must end at that sharing moment

### Three-track requirement for the rollout playbook

| Track | Segments | Primary constraint addressed |
|---|---|---|
| **Technical** | Solo engineer + Technical PM/PE | Time budget → outcome-first framing; mental model shift → gate vocabulary |
| **Enterprise** | FDE client + Enterprise champion | Handoff quality → documentation completeness; career risk → governance depth + measurement infrastructure |
| **Non-technical** | AI-naive knowledge worker + UX designer | Verification burden → constrained first task; identity threat → peer champion + "digital prosthetic" framing |

---

## Mid-market enterprise — unresolved

Named in three independent sources as the highest structural churn risk. Sold
on FDE-level outcomes; given self-service documentation; achieves ~20%
automation vs. 60–80% for FDE-mediated. No viable self-serve path for
enterprise-complexity packs (atlassian, figma, governance-extras) has been
characterised. The rollout playbook must name this gap honestly rather than
promise a path that doesn't exist.

---

## Confidence summary

| Finding | GRADE | Source count | Note |
|---|---|---|---|
| FDE/solo as pathway dimension | High | 8 | Cross-validated across all source tiers |
| Six-segment role model | Moderate | 13 | Desk research only; no participant observation |
| Verification burden as universal churn mechanism | High | 5+ independent disciplines | Cross-segment pattern; strongest finding |
| Peer adoption > mandate | High | 4+ independent disciplines | Directionally consistent across all segments |
| Professional identity threat in 3 segments | Moderate | 4 | Inferred for PM/PE; observed for AI-naive and UX |
| Mid-market gap existence | High | 3 | Consistent across round-1 and round-2 sources |
| Mid-market characterisation | None | — | Not researched; highest remaining gap |
