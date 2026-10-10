---
journey_id: product-documentation
pack: product-documentation
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: "Create, revise, retrofit, audit, and verify documentation for any software product."
prerequisitePacks: []
contract:
  useItWhen: "You need to write, improve, or audit the user-facing docs of a library, CLI, API, app, service, framework, plugin, or agent-context pack — whether you're starting from scratch, reworking legacy docs, finding which stages of the reader journey are missing, or checking that pages match what ships."
  youType: "Audit this project's docs and tell me which stages of the reader journey are missing."
  youProvide: "A description of what you want to document, improve, or check, and optionally the mode (create / revise / retrofit / audit / verify)."
  youReceive: "A draft, revision, retrofit plan, journey gap report, or verification result — whichever fits the request — with the product surface, journey stage, page kind, and write destination reported so you can redirect any of them. Audits and verification results change nothing unless you also ask for fixes."
  yourDecisions:
    - "Redirect the agent if the reported surface, journey stage, page kind, or destination is wrong"
    - "Review the drafted or revised output before it is merged"
  decisionGateIds:
    - confirm-documentation-page-kind
    - review-product-documentation
whatChanges: "After installing product-documentation, your project has the `author-product-docs` skill — one entry point for five documentation modes. The skill infers the mode from your request, discovers what your product is (library, CLI, API, app, service, framework, plugin, or agent-context pack) and where your repository keeps user-facing and maintainer docs, and treats Diátaxis as a page contract rather than a mandatory directory structure. Audits start with a journey gap report: one row per reader stage, from discovering the product to contributing to it."
skills:
  - name: author-product-docs
    description: "Creates, revises, retrofits, audits, or verifies user-facing documentation for any software product, mapping the doc set to the reader journey and using Diátaxis as a page contract — one skill, five modes, no forced directory skeleton."
    humanTouches: 2
humanGates:
  - id: confirm-documentation-page-kind
    globalGate: null
    label: "Check what the agent chose"
    trigger: "When the agent reports its choices with the draft or report — before you commit, redirect it if any is wrong"
    duration: "2–4 minutes"
    whatToCheck:
      - "Is the surface right: library, CLI, API, app, service, framework, plugin, or agent-context pack?"
      - "Is the journey stage right: discover and evaluate, install, first success, daily tasks, look up, understand, troubleshoot, upgrade, or contribute?"
      - "Is the artifact or page kind right: README, docs landing page, installation guide, tutorial, how-to, reference, explanation, troubleshooting, changelog, migration guide, contributing guide, or journey page? For the four Diátaxis kinds, does the reader's posture match: learning (tutorial), a named task (how-to), a fast lookup (reference), or understanding why (explanation)?"
      - "Is the destination where your repository keeps docs of that kind and audience — user docs apart from maintainer docs?"
      - "For an audit or verify request without a request for fixes, does the agent write nothing?"
    whatGoodLooksLike: "A page kind you could justify in one sentence — 'This is a how-to because the reader already knows they want to install X and just needs the steps.'"
    whatBadLooksLike: "An explanation that buries the reader in background before revealing what they can do, or a how-to that opens with three paragraphs about why the tool exists."
    consequence: "A doc written against the wrong page contract misleads the reader from the first sentence. Asking for a revision before you commit is cheap; fixing the page after it is live is not."
  - id: review-product-documentation
    globalGate: "G4"
    label: "Review the product documentation"
    trigger: "After author-product-docs produces an output — before it is committed or merged"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the page stay within its Diátaxis kind — no background narrative in a how-to, no step-by-step instructions in an explanation?"
      - "For a README: does it lead with what the reader can do and show a first runnable example (not an inventory of commands, flags, or skills)?"
      - "For a how-to: is every step an action the reader can take, not a sentence about the system's behavior?"
      - "For an audit: does the journey gap report mark every stage covered, partial, missing, or not applicable with evidence, and does each page-level finding include the violated contract and a concrete fix?"
      - "Are all cross-links pointing to artifacts that actually exist in the repo?"
    whatGoodLooksLike: "A page a reader can pick up cold, act on or learn from, and close — with a first runnable action in its first 120 words and a clear next step."
    whatBadLooksLike: "A how-to that ends with 'now you understand how X works' (that's an explanation), or a reference page with a narrative introduction that restates what the tool does before listing anything."
    consequence: "A badly structured doc ships quietly. Catching contract violations at the review gate is the cheapest point — after a page is live, users accumulate expectations of stability."
typicalSession:
  agentTurns: "4–8"
  humanTouches: 2
  wallClockMinutes: "15–40"
docsUrl: /docs/guides/product-documentation/
packUrl: /packs/product-documentation/
relatedJourneys:
  - core
  - governance-extras
---

### 1. Describe what you need

- **You provide:** what you want to document, improve, or check. The mode is optional — the skill infers it from your request. If you say "write a quickstart for this CLI", it activates create mode. If you say "this doc feels wrong", it activates revise or audit mode.
- **Agent does:** activates `author-product-docs`; discovers the product surface from the repository (library, CLI, API, app, service, framework, plugin, or agent-context pack); places your request on the reader journey; reads the canonical sources for ground-truth behavior; picks the page kind, artifact, and destination. It records these choices and continues; it stops to ask only when uncertainty would change the audience, the behavior described, the artifact, a destructive claim, or the canonical source.
- **You do:** answer the agent's question if it asks one; otherwise nothing yet.
- **Output:** nothing written yet — the agent's choices are working notes until it reports them with the result.
- **State:** read-only

---

### 2. Draft, revise, or audit

- **Agent does:**
  - **create / revise / retrofit** — writes or updates the artifact, leads with a first runnable action, stays within the page contract, cross-links only existing pages. Retrofit starts from the journey gap report and changes the smallest set of pages that fixes the worst rows.
  - **audit** — reads the README, docs index, and every page they link to, then produces a journey gap report (one row per stage, marked covered, partial, missing, or not applicable) followed by page-level findings that each name the violated contract.
  - **verify** — checks each documentation claim against the canonical sources and lists verified, unverified, and contradicted claims.
- **You do:** for create/revise/retrofit, read the draft as a first-time reader; if you find yourself re-reading a sentence to extract the action it asks for, flag it. For audit, check that you agree with the status given to each stage and the contract cited for each finding.
- **You decide:** redirect the agent if the surface, journey stage, page kind, or destination it reports is wrong.
- **Output:** a draft, revision, retrofit plan, audit report, or verification result, followed by a report of the mode, surface, journey stage, artifact, destination, files changed, and checks run.
- **State:** draft

---

### 3. Review and merge

- **You do:** read the output as the intended reader. For create/revise: does the page have a clear entry state, a clear exit, and no sentence that serves a different Diátaxis kind? For audit: is every finding actionable without needing to re-read the original doc?
- **You decide:** review the output — gate passes when page kind, voice, and structure are consistent.
- **Output:** a reviewed page that you commit or merge. Audit and verify end read-only unless you also asked for fixes: they produce a report, so there is nothing to merge.
- **State:** confirmed-write
