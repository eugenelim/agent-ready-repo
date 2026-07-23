---
pack: desk-research
scope: user
tagline: "Evidence-grounded desk research — portable across every repo."
prerequisitePacks: []
contract:
  useItWhen: "You have a question that needs evidence grounded in primary sources — single-session query or a sustained multi-week investigation."
  youProvide: "A research question, a chosen depth mode, and any known sources or prior corpus."
  youReceive: "A confidence-graded synthesis brief citing primary sources, with an explicit gap map."
  yourDecisions:
    - "Set scope and depth"
    - "Review the synthesized brief"
whatChanges: "After installing research, every question your agent takes on is grounded before it answers. `/desk-research` runs scoping, source curation, and synthesis in one session across four depth modes. For sustained investigations, the four `desk-research-project-*` skills run a multi-week lifecycle that accumulates a corpus and ends in a brief you can hand to a decision."
skills:
  - name: desk-research
    description: "The primary desk-research skill. Runs scoping, source curation, and synthesis in a single session, selecting depth from four modes — shallow through exhaustive."
    humanTouches: 1
  - name: source-map
    description: "Maps the canonical sources for a topic before evidence retrieval begins — prevents wasting citations on secondary sources that restate a primary."
    humanTouches: 0
  - name: build-outline
    description: "Builds a research outline from the source map, structuring the question before the agent fetches anything."
    humanTouches: 1
  - name: identify-perspectives
    description: "Identifies the stakeholder perspectives and intellectual traditions bearing on a question before synthesis."
    humanTouches: 0
  - name: compare-hypotheses
    description: "Runs the competing-hypotheses pipeline against a set of candidate answers, producing a scored matrix."
    humanTouches: 0
  - name: devils-advocate
    description: "Steelmans the opposing case for a position — used after compare-hypotheses to stress-test the top candidate."
    humanTouches: 0
  - name: decision-archaeology
    description: "Reconstructs why a prior decision was made from artifacts, commit history, and design docs — used when the answer is historical rather than open."
    humanTouches: 0
  - name: desk-research-project-start
    description: "Initializes a research project folder with a scoped question, source list, and corpus skeleton."
    humanTouches: 1
  - name: desk-research-project-status
    description: "Orients to the current desk-research project at a glance — reads overview.md and surfaces phase, working hypothesis, stop-signal verdict, and what to do next."
    humanTouches: 0
  - name: desk-research-project-check
    description: "Snapshots progress: which sources are captured, what the corpus covers, and what remains."
    humanTouches: 0
  - name: desk-research-project-digest
    description: "Summarizes the accumulated corpus into a digest artifact — the input to the final synthesis."
    humanTouches: 0
  - name: desk-research-project-synthesize
    description: "Synthesizes the corpus digest into a brief graded by confidence, ready to hand to a decision."
    humanTouches: 1
humanGates:
  - id: G-scope
    globalGate: null
    label: "Set scope and depth"
    trigger: "Before /research or desk-research-project-start runs"
    duration: "3–5 minutes"
    whatToCheck:
      - "Is the question specific enough to return a useful answer? (Vague questions return vague syntheses.)"
      - "Is the correct depth mode selected — shallow for orientation, deep or exhaustive for a decision-quality brief?"
      - "Is there a prior corpus this question should extend, or is this a fresh start?"
      - "Is there a success criterion — how will you know when the research is complete?"
    whatGoodLooksLike: "A specific, answerable question with a chosen depth mode and a clear success criterion — something a colleague could pick up and continue."
    whatBadLooksLike: "A question that can't be falsified or finished — 'what is the best approach to X?' with no scope boundary or success criterion."
    consequence: "The scope gate sets the direction for everything that follows. A bad scope means the agent searches the wrong space and returns a synthesis that looks complete but answers the wrong question."
  - id: G-synthesis
    globalGate: null
    label: "Review the synthesized brief"
    trigger: "After the synthesis step completes"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the synthesis cite primary sources, not just secondary summaries?"
      - "Is the confidence grade honest? (A GRADE-C answer dressed as GRADE-A is worse than an honest gap.)"
      - "Does the brief directly answer the original question — or an easier adjacent question?"
      - "Are the gaps named explicitly, with a note on what would be needed to fill them?"
    whatGoodLooksLike: "A synthesis that names its sources, grades its confidence honestly, and directly answers the scoped question — including an explicit gap map where confidence is low."
    whatBadLooksLike: "A synthesis that sounds authoritative but can't be traced to primary sources. Or one that confidently answers a different question than the one you asked."
    consequence: "The synthesis is the final output. A confident but wrong synthesis is actively harmful. If the confidence grade is low, the right response is to narrow the question or run another retrieval pass — not to ship the draft."
typicalSession:
  agentTurns: "4–8"
  humanTouches: 2
  wallClockMinutes: "15–40"
docsUrl: /docs/guides/desk-research/
packUrl: /packs/desk-research/
relatedJourneys:
  - architect
  - core
---

## 1. Scope the question

- **You provide:** the question and chosen depth mode (shallow through exhaustive).
- **Agent does:** activates `desk-research` or `desk-research-project-start`; identifies the question type and maps the source space; emits a scope statement.
- **You do:** read the scope statement before retrieval begins; if the agent's framing misses the real question, redirect with one sentence — a bad scope leads to a confident answer to the wrong question.
- **You decide:** set scope and depth — the direction for everything that follows.
- **Output:** a scoped question with chosen depth mode confirmed.

---

## 2. Curate sources

- **Agent does:** runs `source-map` to identify the canonical sources for the question domain; dispatches retrieval subagents to fetch and synthesize source material.
- **You do:** watch the source list take shape; if a key source is missing — a specific industry report, a primary author's paper, an internal standard you know exists — name it explicitly; the agent doesn't know your domain.
- **Output:** a curated source set with fetched material ready for synthesis.

---

## 3. Synthesize and grade

- **Agent does:** synthesizes a brief graded by confidence (GRADE A–D), citing each claim to its source; marks unsupported claims as explicit gaps.
- **You do:** read the confidence grades first — a GRADE-C synthesis needs a different follow-on (narrow the question, run another retrieval pass) than a GRADE-A; check that each claim has a source citation and is not an unsupported assertion.
- **You decide:** review the synthesized brief — act on it, narrow the question, or run another retrieval pass.
- **Output:** a confidence-graded synthesis brief with cited sources and explicit gap map.
