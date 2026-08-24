# product-engineering

From raw idea to build-ready decision brief.

---

## Start here

Type `frame-intent` and describe a product problem — any altitude, any level of clarity.

```text
frame-intent

  Level    feature
  Problem  New users don't understand the product's value in the first session.
  User     First-time user arriving after sign-up with no prior context.
  Outcome  Activation rate rises; first-session drop-off decreases.
```

On any session return, type `discovery-loop [initiative-name]` to resume where you left off.

```text
discovery-loop self-serve-onboarding

  Initiative  self-serve-onboarding

  Slot               Status
  intent             ratified
  explore-options    done — 4 candidates
  domain-framing     done
  assumption-test    in progress ← current
  decision-brief     pending G2

  Proceed to assumption-test? ›
```

---

## Entry points

| Say this | What happens |
|----------|-------------|
| `discovery-loop` | Start or resume a supervised end-to-end discovery |
| `frame-intent` | Frame a product problem at any altitude |
| `de-risk-intent` | Surface the riskiest assumption and design a prototype approach |
| `decompose-intent` | Break the intent into delivery briefs and specs |
| `ux-writing` | Characterize the product voice and write per-state UI copy |
| `lean-canvas` | Elicit an initiative brief through an adapted Lean Canvas |
| `diverge-solutions` | Generate structured comparable solution options |
| `place-bet` | Commit to a direction with a structured betting table |
| `map-capabilities` | Translate a committed bet into a Capability Map |

---

## How a session runs

```text
frame-intent [describe your product problem]

  Level    feature
  Problem  New users don't understand the product's value in the first session.
  User     First-time user arriving after sign-up with no prior context.
  Outcome  Activation rate rises; first-session drop-off decreases.
```

```text
de-risk-intent

  Assumption   Users who finish the wizard go on to activate the core feature.
  Kill cond.   < 4 of 6 target users reach core-feature first-use in prototype.
  Approach     validate-first — predeclare the line, then run prototype sessions.
  Hook         Conduct 6 moderated prototype sessions with target user profile.
```

```text
decompose-intent

  onboarding-activation
  ├─ onboarding/step-1-welcome      (app — spec ready to draft)
  ├─ onboarding/step-2-connect      (app — spec ready to draft)
  └─ onboarding/step-3-first-action (app — spec ready to draft)
```

After you confirm the handoff, the agent sends each independently shippable leaf
to Core intake as a delivery contract. It sends a coordinating delivery brief
only when the result spans multiple specs or repositories. If the current Core
invocation advertises the handoff capability, the bounded context is
machine-readable; otherwise you receive the same portable rendered handoff.

---

## Where artifacts land

```text
docs/
├── product/
│   ├── intents/          ← frame-intent, de-risk-intent, decompose-intent
│   │   └── <slug>.md
│   ├── rollups/          ← align-value-stream (business-unit scale)
│   │   └── <slug>.md
│   └── voice/            ← ux-writing
│       └── <slug>.md
└── discovery/            ← discovery-loop (sidecar + initiative tree)
    └── <initiative-slug>/
        └── _state/
```

The base paths are configurable — `[product] output_dir` and `[discovery] output_dir` in your repo's `agentbundle-layout.toml`. Defaults to `docs/product/` and `docs/discovery/`.

---

## Cross-pack

**Upstream — `product-strategy`:** OKR gaps and opportunity assessments from `product-strategy` feed `frame-situation` and `frame-intent` as strategic anchors. Absent means both skills degrade gracefully.

**Downstream — `core`:** One independently shippable result from
`decompose-intent` becomes a delivery contract; a multi-spec or
cross-repository result becomes a delivery brief. A compatible Core invocation
admits the bounded handoff through `work-intake`, then preserves the existing
`new-spec` or `receive-brief` approval path. Core is optional.

**Downstream — `experience-design`:** The per-screen state matrix from `user-flow` feeds `ux-writing`. Pass it to write per-state copy for every screen × state cell.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.  
→ **Go deeper:** the [`product-engineering` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/product-engineering/).
