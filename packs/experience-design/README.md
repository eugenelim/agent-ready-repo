# experience-design

Walkable design method from outcome to realization — journey, screens, aesthetic, craft, review.

---

## Start here

Type `journey-mapping` first — describe the user, the outcome, and where the current experience breaks down.

```text
journey-mapping

  journey  docs/design/journeys/onboarding.md

  Stage 1  Aware          finds product, expectations vague
  Stage 2  First-session  blank state, no direction, high drop-off
  Stage 3  Value          first export, relief, converts
```

On any session return, type `experience-status` to see where the thread is.

```text
experience-status

Design thread — docs/design

Journey maps (journeys/): 1 found
  onboarding.md — Onboarding

Screen flows (screens/): 0 found

Steel-thread check:
  Journey map:   ✓ exists
  Screen flow:   ✗ missing — run user-flow
  Briefs:        ✗ missing — run user-flow

What to run next: user-flow
```

---

## Entry points

| Say this | What happens |
|----------|--------------|
| `experience-status` | Orient — where the design thread is, what's next |
| `journey-mapping` | Map the user's outcome: stages, emotions, pains, opportunities |
| `content-design` | Set surface intent — what this screen says and for whom |
| `copy-direction` | Name the per-surface copy goals for a marketing or acquisition surface |
| `tone-of-voice` | Set the brand-level copy register — cross-surface voice personality |
| `user-flow` | Build the screen inventory — transitions and per-screen state briefs |
| `creative-direction` | Anchor the aesthetic — grounded in persona and precedent |
| `design-system` | Derive the token taxonomy from the aesthetic direction |
| `information-architecture` | Structure a screen — hierarchy, reading flow, wayfinding |
| `interaction-design` | Design the behavioral layer — states, feedback, animation |
| `design-review` | Authoring-time critique — quality floor + coherence |
| `experience-reviewer` | Independent cold review — forked context, read-only |

Genre-direct alternatives to `information-architecture` for known surface types: `analytical-design`, `conversion-design`, `documentation-design`, `informational-design`, `marketplace-design`, `workspace-design`.

---

## How a thread runs

```text
journey-mapping [paste the user's outcome and context]

  journey  docs/design/journeys/onboarding.md

  Stage 1  Aware          finds product, expectations vague
  Stage 2  First-session  blank state, no direction, high drop-off
  Stage 3  Value          first export, relief, converts
```

```text
user-flow [link to docs/design/journeys/onboarding.md]

  screens  docs/design/screens/onboarding-flow.md

  /onboarding/welcome  →  /onboarding/connect  →  /onboarding/done
  States per screen: default · loading · error · success · empty
```

```text
experience-reviewer [link to docs/design/screens/onboarding-flow.md]

  Blocker  Welcome screen: empty state not designed
  Concern  Connect screen: error text has no recovery action
  Nit      "Get started" → "Connect your first account" (five-second scan)
```

The reviewer runs forked — no authoring context. You act on its findings, then merge.

---

## What the pack ships

**Connective thread** — from outcome to screen inventory:
`journey-mapping` → `content-design` → `tone-of-voice` (optional, brand register) → `copy-direction` (acquisition surfaces) → `user-flow` → `service-blueprint` / `process-mapping`

**Craft sequence** — from structure to behavior:
`design-principles` → `creative-direction` → `design-system` → `information-architecture` / genre-direct skill → `interaction-design`

**Review** — quality floor, aesthetic fit, cross-brief coherence:
`design-review` (authoring-time) → `experience-reviewer` (independent cold review)

Every skill ships portable **method**, not your stack: no UI-framework code, no values tables, no fixed token set, no pixel comps.

---

## Where these methods come from

Framework names are the procedure; the following is provenance only — who published what, and where this pack's version differs.

- **`journey-mapping`** — draws on Nielsen Norman Group's journey-mapping model (the canonical definition and the five components), Jeff Patton's user-story mapping (stages map roughly to Patton's user activities), and Teresa Torres's opportunity-solution tree (the journey's pains and opportunities feed the tree). See `references/journey-mapping.md` for the full grounding and links. Step 6's peak/dip/end marking follows Daniel Kahneman's peak-end rule: the overall judgment of an experience is disproportionately shaped by its most intense moment (positive or negative) and its end, not its average.
- **`design-principles`** — steps 1–4 of the procedure map to NNGroup's 4-step design-principles model; step 5 (writing the principles doc) is this pack's own addition, not part of that model.
- **`process-mapping`** — the method borrows vocabulary from APQC's Process Classification Framework (PCF) and BPMN 2.0 (OMG / ISO 19510); the source stays authoritative, and the skill's anti-pattern forbids reprinting PCF tables or BPMN element XML.
- **`service-blueprint`** — informed by Nielsen Norman Group's service-blueprinting model, whose rows are customer actions, frontstage actions, backstage actions and support processes, plus physical evidence, separated by three dividers: the line of interaction, the line of visibility, and the line of internal interaction. In NN/g's model the line of visibility is a divider, not a row. **Unresolved discrepancy, recorded rather than papered over:** `SKILL.md` declares five rows and counts line-of-visibility among them, while this skill's own `references/service-blueprint.md` — the file step 3 loads — is titled "the four-row method" and states that the line of visibility "is not a row to fill in." The reference agrees with NN/g; the skill body does not. Which structure the artifact should have is an open design question, not settled here. See [NN/g: Service Blueprints](https://www.nngroup.com/articles/service-blueprints-definition/) and `references/service-blueprint.md`.

---

## Cross-pack

**Upstream — `product-strategy`:** When `ux-strategy.md` and `content-strategy.md` exist, `journey-mapping` and `content-design` read them as strategic anchors. Absent means the skills degrade gracefully.

**Downstream — `product-engineering`:** Pass `user-flow`'s per-screen state matrix to `ux-writing` to write copy keyed to every screen × state cell.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, method architecture, invariants, and decision log.  
→ **Go deeper:** the [`experience-design` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/experience-design/).
