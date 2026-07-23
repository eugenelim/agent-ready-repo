---
pack: user-guide-diataxis
scope: repo
tagline: "Diátaxis-shaped documentation skeleton."
prerequisitePacks: []
contract:
  useItWhen: "You need to add a new document to your project's documentation and want it structured correctly in the right Diátaxis category from the start."
  youProvide: "A description of the documentation gap — what the guide needs to cover and who the reader is."
  youReceive: "A Diátaxis-categorized, correctly structured guide draft — scaffolded in the right quadrant, with entry and exit conditions, ready for review and merge."
  yourDecisions:
    - "Confirm the Diátaxis category"
    - "Review the drafted guide"
whatChanges: "After installing user-guide-diataxis, your repo has a `guides/` directory shaped to the Diátaxis framework — separate directories for tutorials, how-to guides, reference, and explanation. The `new-guide` skill scaffolds each new document in the correct category, preventing the most common documentation failure: mixing instruction and reference in the same document."
skills:
  - name: new-guide
    description: "Scaffolds a new guide document in the correct Diátaxis category — tutorial, how-to, reference, or explanation — with the right structure and tone for that category."
    humanTouches: 2
humanGates:
  - id: G-classify
    globalGate: null
    label: "Confirm the Diátaxis category"
    trigger: "Before new-guide begins drafting — to select the correct document type"
    duration: "3–5 minutes"
    whatToCheck:
      - "Is this a tutorial (learning-oriented — 'do this to understand that'), a how-to (task-oriented — 'do this to achieve that'), a reference (information-oriented — 'what is this'), or an explanation (understanding-oriented — 'why is this')?"
      - "Is the reader a newcomer who needs to be led through a learning experience (tutorial) — or someone who knows what they need and just wants the steps (how-to)?"
      - "Does this document answer 'how do I do X' (how-to) or 'what is X and how does it work' (explanation)? These are different readers with different needs."
      - "Is there already a document in the wrong category covering this topic — that should be replaced or split, not extended?"
    whatGoodLooksLike: "A clear category choice that you could explain in one sentence: 'This is a how-to because the reader already knows what they want to do and just needs the steps.'"
    whatBadLooksLike: "An 'explanation' that includes step-by-step instructions, or a 'how-to' that spends the first half explaining why the tool exists. These are the two most common Diátaxis violations — each mixes a different reader need into the same document."
    consequence: "A document in the wrong Diátaxis category doesn't fail loudly — it just fails its readers silently. Tutorials that are secretly how-tos frustrate experienced readers. Explanations that embed instructions confuse newcomers who needed a tutorial. The classification gate catches this before the first paragraph is written."
  - id: G-review
    globalGate: "G4"
    label: "Review the drafted guide"
    trigger: "After new-guide produces a draft — before it is merged into the docs"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the document stay within its Diátaxis category — no instruction in reference, no background in how-to?"
      - "Is the voice consistent throughout — second person, active voice, present tense for how-tos and tutorials; neutral, descriptive for reference and explanation?"
      - "Does the document have a clear entry point — what state does the reader need to be in before they start?"
      - "Does the document have a clear exit — what state is the reader in when they're done?"
    whatGoodLooksLike: "A document that a reader could pick up cold, complete, and close — knowing exactly what they learned or accomplished. The entry and exit states are explicit."
    whatBadLooksLike: "A document that assumes the reader knows something that wasn't stated in the entry conditions. Or a how-to that ends with 'now you know how X works' — which is the exit state of an explanation, not a how-to."
    consequence: "A badly structured guide ships quietly and gets read by users who then file support requests or give up. Catching structure problems at the review gate is the cheapest point in the lifecycle — after a document is live, it accumulates readers who expect stability."
typicalSession:
  agentTurns: "4–7"
  humanTouches: 2
  wallClockMinutes: "15–35"
docsUrl: /docs/guides/user-guide-diataxis/
packUrl: /packs/user-guide-diataxis/
relatedJourneys:
  - core
  - governance-extras
---

## 1. Identify and classify the documentation need

- **You provide:** a description of the documentation gap — what the guide needs to cover and who the reader is.
- **Agent does:** activates new-guide; asks clarifying questions; proposes the correct Diátaxis category based on the reader need (tutorial for learning, how-to for doing, reference for information, explanation for understanding).
- **You do:** consider the classification — is this reader learning or doing? If unsure between how-to and tutorial: learning → tutorial, doing → how-to; check whether an existing document in the wrong category should be replaced or split rather than extended.
- **You decide:** confirm the Diátaxis category.
- **Output:** a confirmed document category and a clear statement of the reader's need and entry state.

---

## 2. Draft the guide

- **Agent does:** scaffolds the guide in the correct guides/ subdirectory and drafts the content — entry conditions, steps or information organized by category structure, and exit conditions.
- **You do:** watch the draft take shape; for how-tos, check that every step is an action, not a paragraph of explanation (explanation belongs in a linked document); for tutorials, confirm the reader can follow the steps sequentially and arrive at a working outcome, not just a theoretical understanding.
- **Output:** a category-consistent guide draft.

---

## 3. Review and merge

- **You do:** read the guide as a first-time reader — if you have to re-read a sentence to understand what action it asks for, it needs rewriting; if a paragraph of background explanation appears in a how-to, flag it for extraction into a linked explanation document.
- **You decide:** review the drafted guide — gate passes when category, voice, entry state, and exit state are consistent.
- **Output:** a review-gate-passed guide; the agent opens a PR after approval.
