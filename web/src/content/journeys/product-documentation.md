---
pack: product-documentation
scope: repo
tagline: "Create or improve product documentation in five modes."
prerequisitePacks: []
contract:
  useItWhen: "You need to create, revise, retrofit, audit, or verify product documentation — a guide, pack README, journey page, or explanation page — and want the result to lead with what the reader can accomplish."
  youProvide: "A description of the documentation goal — what to create or improve and who the reader is."
  youReceive: "A documentation artifact matched to the reader's job: a task-first guide, an improved pack README, or an audit report — inspected against canonical source behavior before drafting."
  yourDecisions:
    - "Confirm the proposed mode (create, revise, retrofit, audit, verify)"
    - "Confirm the artifact type and page kind"
    - "Review the draft before it is written to disk"
whatChanges: "One or more documentation files are created or updated. For create/revise mode, a task-first artifact is written to the appropriate guides directory or pack README. For audit mode, a findings report is returned without editing. No directory scaffold is installed."
skills:
  - name: author-product-docs
    description: "Creates, revises, retrofits, audits, or verifies product documentation using Diátaxis as a page contract. Inspects canonical pack sources before drafting. Supports five modes inferred from the request."
    humanTouches: 1
humanGates:
  - id: G-contract
    globalGate: null
    label: "Confirm the documentation contract"
    trigger: "Before author-product-docs begins drafting — to confirm mode, audience, and artifact type"
    duration: "2–5 minutes"
    whatToCheck:
      - "Is the proposed mode right — create, revise, retrofit, audit, or verify?"
      - "Is the audience right — external user or internal maintainer?"
      - "Is the artifact type right — guide, README, journey, or explanation?"
      - "Is the page kind right — tutorial, how-to, reference, or explanation?"
    whatGoodLooksLike: "A contract where the mode, audience, and artifact type match what you had in mind — or a clear redirect if they don't."
    whatBadLooksLike: "A contract proposing four empty quadrant directories or placing catalogue-facing content in docs/guides/."
    consequence: "Confirming the contract locks in the minimum artifact set. Redirecting here is cheaper than revising after the draft is written."
  - id: G-review
    globalGate: "G4"
    label: "Review the draft"
    trigger: "After author-product-docs produces a draft"
    duration: "5–20 minutes"
    whatToCheck:
      - "Does the artifact lead with what the reader can accomplish, not with a skill or command inventory?"
      - "Does the first copyable example appear within the first 120 words?"
      - "Is the read/write boundary explicit?"
      - "Are all cross-links pointing to pages that exist?"
    whatGoodLooksLike: "A task-first artifact that a reader can pick up cold and use without knowing any skill names."
    whatBadLooksLike: "An artifact that opens with a list of skills, creates empty quadrant directories, or links to pages that do not exist."
    consequence: "A poorly structured guide ships quietly and frustrates readers. Review before merge."
typicalSession:
  agentTurns: "5–10"
  humanTouches: 1
  wallClockMinutes: "15–45"
docsUrl: /guides/product-documentation/
packUrl: /packs/product-documentation/
relatedJourneys:
  - core
  - governance-extras
---

### 1. Describe the documentation goal

- **You provide:** what to create or improve and who the reader is.
- **Agent does:** activates `author-product-docs`; reads canonical pack sources (`pack.toml`, skill files); proposes a documentation contract naming mode, audience, artifact type, and page kind.
- **You decide:** confirm the documentation contract.
- **Output:** a confirmed contract ready to draft from.

---

### 2. Draft the artifact

- **Agent does:** drafts the artifact starting from canonical behavior — not from imagination. For a guide or README, puts the first copyable example within 120 words. For an audit, produces findings without editing. For a verify, confirms documentation matches current shipped behavior.
- **You do:** watch the draft take shape; for task-oriented pages, check that the reader could pick it up cold and complete a task without knowing any skill names.
- **Output:** a draft artifact or findings report.

---

### 3. Review and finalize

- **You do:** read the draft as a first-time reader. If the first thing you see is a list of skills or commands, flag it — the inventory belongs after the first task completes.
- **You decide:** review the draft — gate passes when the artifact leads with outcomes and links only to pages that exist.
- **Output:** a reviewed artifact ready for merge.
