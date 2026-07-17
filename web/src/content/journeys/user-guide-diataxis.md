---
pack: user-guide-diataxis
scope: repo
tagline: "Diátaxis-shaped documentation skeleton."
prerequisitePacks: []
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

## Stage 1 — Identify the documentation need and classify it

You identified a gap in the project's documentation — something users needed to know that wasn't written down, or was written in the wrong form. The agent activated `new-guide`, asked what the guide needed to cover, and helped classify it into the correct Diátaxis category.

**You did:** Made the classification decision at the G-classify gate. This is the most consequential decision in the documentation session — the wrong category means the wrong structure, the wrong voice, and the wrong reader. If you were unsure between how-to and tutorial, asked: is this reader learning, or is this reader doing? Learning → tutorial. Doing → how-to.

---

## Stage 2 — Draft the guide

With the category confirmed, the agent scaffolded the guide in the correct `guides/` subdirectory and drafted the content — entry conditions, steps or information organized by category structure, and exit conditions.

**You did:** Watched the draft take shape. For how-tos: checked that every step was an action, not a paragraph of explanation. Explanation belongs in a linked explanation document. For tutorials: confirmed the reader could follow the steps sequentially and arrive at a working outcome, not just a theoretical understanding.

---

## Stage 3 — Review and merge

After the draft completed, you reviewed at the G-review gate for structure consistency and category fidelity, then the agent opened a PR.

**You did:** Read the guide as a first-time reader — not as the author who knows what it means. If you had to re-read a sentence twice to understand what action it was asking for, it needed rewriting. If a paragraph of background explanation appeared in the middle of a how-to, flagged it for extraction into a linked explanation document. Merged after the review gate passed.
