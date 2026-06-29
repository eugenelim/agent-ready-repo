---
type: customer-journey
slug: <slug>
persona: <persona-name-or-role>
outcome: <the outcome the customer is trying to reach>
surface: <responsive-web | iOS | Android | cross-platform>
---

# Journey: <title>

**Persona:** <who the customer is and the relevant context>
**Outcome:** <what done looks like for the customer>
**Surface:** <the platform/surface this journey is designed for>
**Trigger:** <what initiates the journey — the first action or event>
**End state:** <what the customer has achieved when the journey is complete>

---

## Stage 1: <stage name>

| Row | Content |
|-----|---------|
| **Actions** | <what the customer does — frontstage, in the customer's words> |
| **Emotions** | <how the customer feels; mark valence: positive / neutral / negative> |
| **Pains** | <friction, confusion, or gaps — in the customer's words> |
| **Opportunities** | <what would change if the pain were addressed — solution-independent> |

## Stage 2: <stage name>

| Row | Content |
|-----|---------|
| **Actions** | |
| **Emotions** | |
| **Pains** | |
| **Opportunities** | |

## Stage 3: <stage name>

| Row | Content |
|-----|---------|
| **Actions** | |
| **Emotions** | |
| **Pains** | |
| **Opportunities** | |

<!-- Add stages 4–6 as needed. Three to six stages is the right grain. -->

---

## Emotional arc

<!-- Summarize the emotional trajectory across stages — where is the lowest
     point (deepest negative)? That dip is usually the highest-opportunity
     problem. Name the dip stage and the opportunity it implies. -->

Lowest point: Stage <N> — <emotion word> — because <why>.
Highest-opportunity pain: <pain in the customer's words>.

---

## Handoff notes

**For `map-screen-flow`:** the stages with the highest-opportunity pains
are <list stages>. The actions within each stage are the screen-level
inputs for sequencing.

**For `blueprint-service`:** the backstage services implied by the
customer's actions include <list any named services or system capabilities
the customer's actions depend on — textual if `architect`/`contracts` are
not installed, by-reference if they are>.
