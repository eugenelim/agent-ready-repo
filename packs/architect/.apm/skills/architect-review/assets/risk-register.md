<!-- Inline output shape for `architect-review`'s well-architected (WA) mode.
     Not written to disk by default — reviews are throwaway. Use this as the
     order and section shape of the inline reply. Reuses the verdict + severity
     vocabulary from `critique.md`; adds the mechanical/judgment tag and the
     WAR-shaped risk register + improvement plan + risk-acceptance + non-risks. -->

## Verdict

<SHIP IT | SHIP WITH CHANGES | MAJOR REWRITE | WRONG ARTIFACT>

## Summary

<Three sentences or fewer. The workload + provider class, the lenses applied
(e.g. security + GenAI/agentic), and the dominant risk.>

> Lenses applied: <concern-lens(es)> · <workload-class lens(es)>. Pillar spine
> per `rubric-well-architected.md`.

## Risk register

> Findings ordered by severity. Each finding carries a **severity** tag *and* a
> **🔧 mechanical / 🧭 judgment** tag (the signal `architect-design`'s convergence
> loop consumes). Mechanical = fix fully determined by the spine or a stated
> constraint; judgment = a tradeoff / risk-acceptance / low-confidence call.

### 🟥 Blockers

**1. <Short title.>** `🔧 mechanical | 🧭 judgment`
- *Pillar / lens:* <Reliability · Security · … / which lens surfaced it>
- *Where:* "<quoted verbatim>" — or section + paragraph.
- *What's wrong:* <One sentence naming the failed pillar check.>
- *Scenario (if measurable):* <source/stimulus/artifact/environment/response/measure>
- *Fix / decision:* <mechanical → the determinate fix; judgment → the decision
  the human must make and the options.>

### 🟧 Majors

**2. <…>** `🔧 | 🧭`
- *Pillar / lens:* …
- *Where:* …
- *What's wrong:* …
- *Fix / decision:* …

### 🟨 Minors / ⚪ Nits

- <One-line finding + tag.>

## Prioritized improvement plan

> Remediation roadmap, ranked by business-importance × architectural-risk
> (not finding order). Status vocabulary mirrors a real WAR.

| # | Finding | Pillar / lens | Tag | Priority | Status |
|---|---|---|---|---|---|
| 1 | <title> | <pillar> | 🔧 / 🧭 | High / Med / Low | None / Not started / In progress / Complete / Risk acknowledged |

## Documented risk-acceptance

> Best practices the design **deliberately** does not adopt — recorded, not
> hidden. Each is a 🧭 judgment call with a rationale and (where relevant) who
> signed off.

- **<Accepted risk>.** <Why it's accepted given the drivers; who owns the
  acceptance.>

## Documented non-risks

> Decisions that are **sound given the drivers** — more rigorous than praise,
> and the WA analogue of "what's working." Name *why* each is not a risk here.

- **<Decision>.** <Why it's the right call for this workload / provider class.>
