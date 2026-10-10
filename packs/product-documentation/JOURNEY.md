---
journey_id: product-documentation
pack: product-documentation
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: "Create, revise, retrofit, audit, and verify documentation for any software product."
prerequisitePacks: []
contract:
  useItWhen: "You need to write, improve, or audit the user-facing docs of a library, CLI, API, app, service, plugin, or agent-context pack — whether you're starting from scratch, reworking legacy docs, finding which stages of the reader journey are missing, or checking that pages match what ships."
  youType: "Audit this project's docs and tell me which stages of the reader journey are missing."
  youProvide: "A description of what you want to document, improve, or check, and optionally the mode (create / revise / retrofit / audit / verify)."
  youReceive: "A draft, revision, retrofit plan, journey gap report, or verification result — whichever fits the request — with the product surface named, the page kind confirmed, and the write destination resolved from your repository's own layout."
  yourDecisions:
    - "Confirm the Diátaxis page kind (tutorial / how-to / reference / explanation)"
    - "Review the drafted or revised output before it is merged"
  decisionGateIds:
    - confirm-documentation-page-kind
    - review-product-documentation
whatChanges: "After installing product-documentation, your project has the `author-product-docs` skill — one entry point for five documentation modes. The skill infers the mode from your request, discovers what your product is (library, CLI, API, app, service, plugin, or agent-context pack) and where your repository keeps user-facing and maintainer docs, and treats Diátaxis as a page contract rather than a mandatory directory structure. Audits start with a journey gap report: one row per reader stage, from discovering the product to contributing to it."
skills:
  - name: author-product-docs
    description: "Creates, revises, retrofits, audits, or verifies user-facing documentation for any software product, mapping the doc set to the reader journey and using Diátaxis as a page contract — one skill, five modes, no forced directory skeleton."
    humanTouches: 2
humanGates:
  - id: confirm-documentation-page-kind
    globalGate: null
    label: "Confirm the documentation page kind"
    trigger: "Before author-product-docs begins drafting — to confirm the page kind inferred from your request"
    duration: "2–4 minutes"
    whatToCheck:
      - "Is this a tutorial (learning-oriented — the reader is doing to learn), a how-to (task-oriented — the reader knows what they want and needs the steps), a reference (information-oriented — structured facts, no narrative), or an explanation (understanding-oriented — why, context, background)?"
      - "Does the mode make sense for the request? Create/revise/retrofit = active authoring; audit = journey gap report and findings, no edits; verify = each claim checked against the shipped behavior."
      - "Is the audience the product's users (people who install, call, run, or extend it) or the repository's maintainers? User-facing docs and maintainer docs live apart in your repository."
    whatGoodLooksLike: "A confirmed page kind that you could justify in one sentence — 'This is a how-to because the reader already knows they want to install X and just needs the steps.'"
    whatBadLooksLike: "An explanation that buries the reader in background before revealing what they can do, or a how-to that opens with three paragraphs about why the tool exists."
    consequence: "A doc written against the wrong page contract misleads the reader from the first sentence. The classification gate catches this before the first paragraph is drafted — cheap here, expensive after it's live."
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
- **Agent does:** activates `author-product-docs`; discovers the product surface from the repository (library, CLI, API, app, service, plugin, or agent-context pack); places your request on the reader journey; reads the canonical sources for ground-truth behavior; proposes the page kind and target artifact.
- **You do:** check that the inferred page kind fits your intent.
- **You decide:** confirm the Diátaxis page kind.
- **Output:** a confirmed surface, journey stage, page kind, mode, and destination path.
- **State:** read-only

---

### 2. Draft, revise, or audit

- **Agent does:**
  - **create / revise / retrofit** — writes or updates the artifact, leads with a first runnable action, stays within the page contract, cross-links only existing pages. Retrofit starts from the journey gap report and changes the smallest set of pages that fixes the worst rows.
  - **audit** — reads the README, docs index, and every page they link to, then produces a journey gap report (one row per stage, marked covered, partial, missing, or not applicable) followed by page-level findings that each name the violated contract.
  - **verify** — checks each documentation claim against the canonical sources and lists verified, unverified, and contradicted claims.
- **You do:** for create/revise/retrofit, read the draft as a first-time reader; if you find yourself re-reading a sentence to extract the action it asks for, flag it. For audit, check that you agree with the status given to each stage and the contract cited for each finding.
- **Output:** a draft, revision, retrofit plan, audit report, or verification result.
- **State:** draft

---

### 3. Review and merge

- **You do:** read the output as the intended reader. For create/revise: does the page have a clear entry state, a clear exit, and no sentence that serves a different Diátaxis kind? For audit: is every finding actionable without needing to re-read the original doc?
- **You decide:** review the output — gate passes when page kind, voice, and structure are consistent.
- **Output:** a review-gate-passed artifact; the agent opens a PR after approval.
- **State:** confirmed-write
