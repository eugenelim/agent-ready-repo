---
generated: true
journey_id: frontend-engineering
pack: frontend-engineering
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Build a web surface, then prove it holds up."
prerequisitePacks: []
contract:
  useItWhen: "You need to create, retrofit, audit, or verify an HTML/CSS/JS surface with a page/screen contract, accessible states, Core Web Vitals targets, and completion evidence."
  youType: "Build this screen against its page contract."
  youProvide: "A surface brief, existing page, or completed implementation, plus any product constraints, routes, viewports, design references, and available performance data."
  youReceive: "A proportional page/screen contract, implementation or audit path, gate results, evidence manifest, and independent frontend review focused on regressions that ordinary tests miss."
  yourDecisions:
    - "Choose create, retrofit, audit, or verify"
    - "Approve the page/screen contract before significant UI code"
    - "Accept or fix known exceptions before completion"
  decisionGateIds:
    - choose-frontend-operating-mode
    - approve-frontend-surface-contract
    - accept-frontend-evidence
    - review-frontend-implementation
whatChanges: "After installing frontend-engineering, the main skill gives one operating path for web surfaces: create starts from a contract, retrofit starts from brownfield inspection, audit reports findings without code changes, and verify runs gates against a completed surface. Supporting skills cover tokens, accessibility, performance, rendering, component contracts, responsive layout, CSS architecture, and status. The frontend-reviewer agent provides an independent read: the diff for token drift, ARIA mutation completeness, state coverage, WCAG 2.2 manual checks and Core Web Vitals regression signals, and the rendered captures for reader-visible layout failure a diff cannot show."
skills:
  - name: frontend-engineering
    description: "Selects create, retrofit, audit, or verify mode; runs the shared pre-flight; and requires evidence before completion."
    humanTouches: 4
  - name: token-architecture
    description: "Shapes the design-token system used by the surface."
    humanTouches: 1
  - name: a11y-engineering
    description: "Handles dedicated accessibility audits, retrofits, and complex interaction accessibility."
    humanTouches: 1
  - name: fe-performance
    description: "Measures, diagnoses, and remediates Core Web Vitals and asset-budget violations."
    humanTouches: 1
  - name: rendering-strategy
    description: "Chooses CSR, SSR, SSG, ISR, or RSC route strategy from data, SEO, and hydration constraints."
    humanTouches: 1
  - name: component-contract
    description: "Defines public interfaces for reusable components."
    humanTouches: 1
  - name: responsive-layout
    description: "Plans responsive layout behavior across containers and breakpoints."
    humanTouches: 1
  - name: css-architecture
    description: "Keeps cascade layers, scoping, specificity, and token compliance coherent."
    humanTouches: 1
  - name: fe-status
    description: "Reads the evidence manifest and reports current frontend quality state."
    humanTouches: 0
humanGates:
  - id: choose-frontend-operating-mode
    globalGate: null
    label: "Choose the frontend operating mode"
    trigger: "Before planning starts, after you describe the surface or review target"
    duration: "2-5 minutes"
    whatToCheck:
      - "Create is for a new surface or significant component."
      - "Retrofit is for improving an existing surface and starts with brownfield inspection."
      - "Audit reads and reports only."
      - "Verify runs gates and records evidence for completed work."
    whatGoodLooksLike: "The mode matches the job and the expected output is named before work begins."
    whatBadLooksLike: "A small component tweak gets treated like a full new route, or a review-only request silently turns into code edits."
    consequence: "The wrong mode either overburdens a small change or skips evidence a larger surface needs."
  - id: approve-frontend-surface-contract
    globalGate: null
    label: "Approve the frontend surface contract"
    trigger: "Before significant UI code in create mode, or before a retrofit becomes a substantial rebuild"
    duration: "10-15 minutes"
    whatToCheck:
      - "The target user, primary job, expected result, first-screen content, and next action are specific."
      - "The read/write consequence is clear."
      - "The critical states, responsive behavior, a11y requirements, and measurement event are testable."
    whatGoodLooksLike: "A reader can tell what the first screen must accomplish and what evidence will prove it."
    whatBadLooksLike: "The contract repeats vague product goals or omits error, empty, keyboard-only, high-zoom, or reduced-motion states that apply."
    consequence: "A weak contract lets the implementation drift into a polished happy path with missing states."
  - id: accept-frontend-evidence
    globalGate: null
    label: "Accept the frontend implementation evidence"
    trigger: "After implementation, audit, or verify mode produces gate results"
    duration: "10-20 minutes"
    whatToCheck:
      - "Routes, viewports, browsers, states, screenshots, inspection observations, a11y result, perf result, console/network result, analytics events, known exceptions, and unverified items are present."
      - "Inspection observations say what was seen in the captures and name the result state AND the verdict; a list of screenshot filenames does not satisfy the field, and a skipped or failed inspection is not a completed one."
      - "The inspection verdict is `pass`. A `fail` verdict means the run looked at the page and found a blocking reader-visible failure: accept it as a known exception with a named owner, or send it back. A completed run is not a passing one."
      - "Core Web Vitals use p75 targets, with mobile and desktop separated where field data exists."
      - "Known exceptions are explicit decisions, not hidden missing work."
    whatGoodLooksLike: "The manifest names what was tested, what passed, what could not be tested, and what remains accepted risk."
    whatBadLooksLike: "Completion is claimed from source inspection alone, or field performance, manual WCAG 2.2 checks, and screenshots are left implicit."
    consequence: "Without evidence, the surface may look complete while still failing in browser, accessibility, or performance review."
  - id: review-frontend-implementation
    globalGate: null
    label: "Review the frontend implementation"
    trigger: "After gates and manifest are ready, before merge or handoff"
    duration: "10-20 minutes"
    whatToCheck:
      - "Token drift, ARIA mutation completeness, state coverage regression, WCAG 2.2 Focus Appearance, WCAG 2.2 Target Size Minimum, Core Web Vitals regression signals, and reader-visible layout failure read from the rendered captures were reviewed."
      - "Security, reliability, or product-design concerns were routed to the appropriate reviewer instead of claimed as covered here."
    whatGoodLooksLike: "The reviewer finds no blocking frontend regressions, or the findings are fixed and rerun."
    whatBadLooksLike: "The same author judges their own UI diff complete without an independent read."
    consequence: "The independent read catches frontend-specific regressions that schema checks and unit tests rarely see."
typicalSession:
  agentTurns: "6-14"
  humanTouches: 4
  wallClockMinutes: "45-120"
docsUrl: /docs/guides/frontend-engineering/
packUrl: /packs/frontend-engineering/
relatedJourneys:
  - experience-design
  - product-documentation
---

Common requests:

- **Create:** “Build this dashboard screen from the brief.” The agent writes a proportional contract, implements the surface, runs gates, and produces evidence. You approve the contract and accept or fix exceptions.
- **Retrofit:** “Improve this existing checkout page without changing its flow.” The agent starts with brownfield inspection, then produces a preservation list, implementation path, and evidence manifest. You decide which existing debts are in scope.
- **Audit:** “Audit this landing page for frontend quality.” The agent writes a prioritized report without changing code. You decide which findings become work.
- **Verify:** “Verify this completed page before release.” The agent runs the gate suite and produces an evidence manifest. You accept the release evidence or send it back.

## The journey

### 1. Choose the frontend job

- **You provide:** the surface or request: create a new page, retrofit an existing one, audit without edits, or verify completed work.
- **Agent does:** loads `frontend-engineering`, selects create, retrofit, audit, or verify, and names the expected output before touching code or gates.
- **You do:** confirm that the mode matches the job you actually want done.
- **You decide:** choose the operating mode.
- **Output:** a mode decision with the work boundary: contract, brownfield inspection, audit report, or verification manifest.
- **State:** decision-required

---

### 2. Write or confirm the page/screen contract

- **You provide:** the surface brief, target user, primary job, first-screen requirements, existing design constraints, and any measurement event already known.
- **Agent does:** for create mode, drafts the proportional page/screen contract before significant UI code. For retrofit mode, runs brownfield inspection first and then narrows or expands the contract only if the surface is being substantially rebuilt.
- **You do:** read the contract as the product owner: can you tell what the surface must show, what action it supports, what state coverage applies, and whether the primary action reads or writes data?
- **You decide:** approve the contract or send it back with the missing product, state, responsive, a11y, or measurement detail.
- **Output:** an approved contract or brownfield inspection that constrains implementation.
- **State:** proposed-write

---

### 3. Implement or audit the surface

- **You provide:** repository access, the route or component location, design-system constraints, and any existing token, a11y, performance, or rendering requirements.
- **Agent does:** follows the implementation sequence for create or retrofit: named aesthetic reference, optional genre routing through the co-installed design pack, seed token block, state matrix, semantic HTML, CSS token discipline, responsive behavior, and public-surface checks where applicable. In audit mode, it reads the surface and reports findings without writing code.
- **You do:** answer any product decision that changes the contract, such as what to preserve in a retrofit or which known debt is allowed as a ride-along.
- **You decide:** accept scoped implementation decisions or keep them out of this change.
- **Output:** implemented frontend work for create/retrofit, or an audit report for audit mode.
- **State:** confirmed-write

---

### 4. Run verification gates

- **You provide:** a runnable local route, static file, or completed surface, plus any browser or environment constraints, and the routes you want inspected.
- **Agent does:** runs the verification gates in order: structural HTML validation, accessibility audit, CSS token enforcement when configured, and visual QA against applicable states. It then runs the **rendered-page inspection**: it opens each route you named at two viewport heights, at rest and scrolled, and judges what the page actually looks like — content covering other content, text running out of its container, a control too small to hit. It records Core Web Vitals targets at p75 and separates mobile and desktop where field data exists.
- **You do:** provide access or manual evidence for any browser-only check the agent cannot run, and decide whether any signed-in or sensitive view should be captured at all.
- **Output:** gate results with pass, fail, or unverified status for each required check, plus the inspection's **observations** — what was seen in the captures, the result state, and the verdict (`pass`, or `fail` when a blocking reader-visible failure is unresolved) — which carry into the evidence manifest. A filename is not an observation. When no browser is reachable the inspection takes its named skip, recording `skipped-no-browser` and naming the missing capability; a skip stays visibly different from a completed inspection everywhere the result is read, so it reaches you as a decision rather than passing as a pass.
- **State:** read-only

---

### 5. Produce the evidence manifest

- **You provide:** screenshots, field data, analytics-event proof, or known-exception decisions that are not available from local gates.
- **Agent does:** assembles the evidence manifest with routes, viewports, browsers, states, screenshots, inspection observations (what was seen in the captures, the result state, and the verdict), a11y result, perf result, console/network result, analytics events, known exceptions, and unverified items. For a production surface it also records security/privacy review status and reliability/recovery status — the state of those reviews and who they were routed to, not a verdict of its own.
- **You do:** inspect the unverified items and known exceptions instead of treating them as noise.
- **You decide:** accept the known exceptions, require fixes, or defer the surface.
- **Output:** a completion-ready evidence manifest for create, retrofit, or verify mode.
- **State:** decision-required

---

### 6. Get an independent frontend review

- **You provide:** the diff and evidence manifest.
- **Reviewer does:** reads the HTML/CSS/JS diff for token drift, ARIA mutation completeness, state coverage regression, WCAG 2.2 manual-verification items, and Core Web Vitals regression signals, and reads the rendered-page captures for what a diff cannot show — something covering something else, text out of its container, a control too small to hit — taking its own captures where the set it was given does not cover what the diff makes it suspicious of. Security, reliability, and broader product-design findings route to their own reviewers instead of being claimed here.
- **You do:** review findings and decide whether each one blocks the handoff.
- **You decide:** merge after clean review, or send the work back through implementation and gates.
- **Output:** reviewed frontend work with the contract, gates, manifest, and reviewer disposition connected.
- **State:** confirmed-write
