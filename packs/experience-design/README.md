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
| `tone-of-voice` | Set the brand register — copy goals and arbitration rules |
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

  screens  docs/design/screen-flows/onboarding.md

  /onboarding/welcome  →  /onboarding/connect  →  /onboarding/done
  States per screen: default · loading · error · success · empty
```

```text
experience-reviewer [link to docs/design/screen-flows/onboarding.md]

  Blocker  Welcome screen: empty state not designed
  Concern  Connect screen: error text has no recovery action
  Nit      "Get started" → "Connect your first account" (five-second scan)
```

The reviewer runs forked — no authoring context. You act on its findings, then merge.

---

## What the pack ships

**Connective thread** — from outcome to screen inventory:
`journey-mapping` → `content-design` / `tone-of-voice` → `user-flow` → `service-blueprint` / `process-mapping`

**Craft sequence** — from structure to behavior:
`design-principles` → `creative-direction` → `design-system` → `information-architecture` / genre-direct skill → `interaction-design`

**Review** — quality floor, aesthetic fit, cross-brief coherence:
`design-review` (authoring-time) → `experience-reviewer` (independent cold review)

Every skill ships portable **method**, not your stack: no UI-framework code, no values tables, no fixed token set, no pixel comps.

---

## Cross-pack

**Upstream — `product-strategy`:** When `ux-strategy.md` and `content-strategy.md` exist, `journey-mapping` and `content-design` read them as strategic anchors. Absent means the skills degrade gracefully.

**Downstream — `product-engineering`:** Pass `user-flow`'s per-screen state matrix to `voice-and-microcopy` to write copy keyed to every screen × state cell.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, method architecture, invariants, and decision log.  
→ **Go deeper:** the [`experience-design` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/experience-design/).
