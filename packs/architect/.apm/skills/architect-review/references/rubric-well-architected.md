# Well-architected rubric — review a design through pillars + lenses

The quality bar for `architect-review`'s **well-architected (WA) mode**. This
rubric is *orthogonal to artifact type*: where the other rubrics route by *what
the artifact is* (design doc, C4, sequence…), this one inspects a design for
*how well-architected it is*, through the pillar spine and one or more selected
lenses. Walk it, tag every finding, and emit the output shape in
`assets/risk-register.md`.

## Select the lenses first

A WA review applies the pillar spine through whichever lenses the design and the
user's intent call for. Two orthogonal axes:

- **Concern-lens** — security · cost/FinOps · reliability/SRE · DR · data/privacy
  · compliance · sustainability/green.
- **Workload-class lens** — ML · **GenAI/agentic** · SaaS · **serverless**. For
  GenAI/agentic, load `lens-genai-agentic.md`; for serverless, load
  `lens-serverless.md`. ML and SaaS are named here but not yet backed by a lens
  file.

A full review is the union of the relevant passes — usually one or two lenses,
not all of them. Load `well-architected-pillars.md` for the spine,
`quality-attribute-scenarios.md` to anchor measurable claims,
`tradeoffs-and-sensitivity.md` for the tradeoff/sensitivity checks, and
`cross-cutting-questions.md` for the alignment / lock-in / assessability bank.

## The pillar checks (per selected lens)

- [ ] **Reliability** — blast radius, SPOF, recovery (RTO/RPO), graceful
      degradation named, with a measure where one is claimed.
- [ ] **Security** — trust boundaries labeled, identity/least-privilege,
      data classification + egress, attack surface. (Control-level verification
      routes downstream to `security-reviewer` / `security-checklists` — this
      rubric stays at design altitude.)
- [ ] **Cost** — unit economics, scaling shape (linear vs sublinear), the levers
      the provider class actually offers.
- [ ] **Performance** — workload-to-resource fit, scaling model, latency budget
      (p50/p99) as a scenario. For a **synchronous** request path, treat the
      latency budget as a **binding-constraint viability check**: is the
      worst-case sum across every hop compared to the binding front-door timeout?
      An **unbudgeted synchronous long-operation path is a finding** — 🟥 blocker
      when it makes the design structurally impossible (the work cannot fit the
      ceiling), not merely slow.
- [ ] **Operational excellence** — observability (metrics/logs/traces),
      deploy/rollback, "debuggable at 3am."
- [ ] **Sustainability** — utilization, region/placement levers (when material).
- [ ] **Provider fit** — for a primitives provider, are the **capability gaps**
      (`cloud-primitives.md`) the design must build itself named? For a
      hyperscaler, is each pillar tied to the managed service that carries it?
- [ ] **Platform-contract grounding** — is every **load-bearing managed-service
      claim** (a binding limit, scaling floor, cold-start cost, or network /
      identity requirement the design depends on) backed by **visible
      grounding** — a cited source with confidence — rather than asserted from
      memory? **Re-derive or flag the claim; do not trust the design's own
      assertion.** A load-bearing managed-service claim with no visible grounding
      is a finding. 🔧 mechanical when the pillar spine determines the missing
      fact must be established (one correct resolution: ground it); 🧭 judgment
      when grounding it needs a business / risk call.
- [ ] **Tradeoffs & sensitivity** — is at least one tradeoff point named, and any
      sensitivity point? Flag *undocumented* tradeoffs.

## Tag every finding — the decidable mechanical-vs-judgment test

Every WA-mode finding carries the existing **severity** tag *and* a
**mechanical / judgment** tag. This is the signal `architect-design`'s
convergence loop consumes — so the test must be *decidable on a novel finding*,
not just recognizable on the planted examples below.

**The test.** Ask: *is the fix fully determined?*

- **🔧 Mechanical** — the fix is **fully determined by the pillar spine or a
  stated constraint**, with **no** business-value or risk-acceptance choice left
  open. There is one correct resolution and applying it needs no human decision.
- **🧭 Judgment** — resolving it **requires choosing between defensible options**:
  a **tradeoff** (two pillars pull opposite ways), a **risk acceptance** (a best
  practice deliberately not adopted, business sign-off), **or an assumption
  resting on low-confidence / leading-edge evidence**. More than one answer is
  defensible; a human must pick.

Apply it to the finding in front of you, not a catalogue. If you can write the
fix without making a business or risk call, it's mechanical; if writing the fix
forces you to choose a side, it's judgment.

**Worked discriminations:**

| Finding | Tag | Why |
|---|---|---|
| An unlabeled trust boundary on a cross-tenant arrow | 🔧 mechanical | the spine determines it must be labeled; no choice |
| A reliability claim with no response-measure, but a stated SLO exists | 🔧 mechanical | the constraint (the SLO) determines the measure |
| A reliability claim with no SLO and no agreed target | 🧭 judgment | how much availability is worth is a business call |
| Self-host inference vs. external LLM API | 🧭 judgment | a tradeoff (control/residency vs. burden/capability) |
| A best practice the design skips for cost reasons | 🧭 judgment | a risk acceptance needing sign-off |
| A design assumption resting on a grey-lit / leading-edge claim | 🧭 judgment | low-confidence evidence; a human must accept the risk |

A mechanical finding that **cannot be determinately fixed** (the rubric can't
resolve it) is judgment in disguise — tag it judgment and let the loop's stasis
escape surface it.

## Scenario-anchor measurable findings

Where a finding turns on a measurable claim, frame it as the
quality-attribute scenario the design fails to meet
(source/stimulus/artifact/environment/response/response-measure) so the fix
target is unambiguous. See `quality-attribute-scenarios.md`.

## Reuse the existing verdict + severity vocabulary

WA mode does not invent a new verdict scale. Reuse `architect-review`'s verdict
(SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT) and severity tags
(🟥 blocker / 🟧 major / 🟨 minor / ⚪ nit). The mechanical/judgment tag is *added
to* each finding, not a replacement.

## Severity mapping (typical, WA mode)

- 🟥 **Blocker** — an unmet pillar that makes the design unsafe to build as-is
  (no recovery story for a stated availability goal; an unlabeled trust boundary
  on sensitive egress).
- 🟧 **Major** — a material pillar gap (no observability for an operability goal;
  a primitives capability-gap the design never names).
- 🟨 **Minor** — a partial pillar treatment; a sensitivity point left un-named.
- ⚪ **Nit** — phrasing, ordering, a label that's present but imprecise.
