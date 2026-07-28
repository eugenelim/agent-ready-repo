---
pack: user-guide-diataxis
scope: repo
tagline: "Superseded by product-documentation — see the updated journey."
prerequisitePacks: []
contract:
  useItWhen: "Install product-documentation instead. This journey is preserved for existing installations only."
  youProvide: "See the product-documentation journey."
  youReceive: "See the product-documentation journey."
  yourDecisions:
    - "See the product-documentation journey"
whatChanges: "Superseded. Install product-documentation — it provides the same guide-authoring flow plus four additional modes (revise, retrofit, audit, verify) and removes the mandatory four-subdirectory skeleton. Existing user-guide-diataxis installations continue to work; new-guide routes to author-product-docs automatically."
skills:
  - name: new-guide
    description: "Routes to author-product-docs (product-documentation pack). See the product-documentation journey for the full workflow."
    humanTouches: 2
humanGates:
  - id: G-classify
    globalGate: null
    label: "Confirm the Diátaxis category"
    trigger: "Before new-guide begins drafting"
    duration: "3–5 minutes"
    whatToCheck:
      - "See the product-documentation journey — it reflects current behaviour."
    whatGoodLooksLike: "See the product-documentation journey."
    whatBadLooksLike: "See the product-documentation journey."
    consequence: "See the product-documentation journey."
  - id: G-review
    globalGate: "G4"
    label: "Review the drafted guide"
    trigger: "After new-guide produces a draft"
    duration: "10–20 minutes"
    whatToCheck:
      - "See the product-documentation journey — it reflects current behaviour."
    whatGoodLooksLike: "See the product-documentation journey."
    whatBadLooksLike: "See the product-documentation journey."
    consequence: "See the product-documentation journey."
typicalSession:
  agentTurns: "4–7"
  humanTouches: 2
  wallClockMinutes: "15–35"
docsUrl: /guides/product-documentation/
packUrl: /packs/product-documentation/
relatedJourneys:
  - core
  - governance-extras
---

> **Deprecated.** This journey is preserved so existing `/journeys/user-guide-diataxis/` links continue to resolve. The canonical journey is [product-documentation](../../journeys/product-documentation/).

Install `product-documentation` for new projects. The `new-guide` skill in existing installations routes to `author-product-docs` automatically — the workflow is unchanged.
