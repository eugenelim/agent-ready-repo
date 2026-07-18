---
pack: research
scope: user
tagline: "Evidence-grounded research — portable across every repo."
prerequisitePacks: []
whatChanges: "After installing research, every question your agent takes on is grounded before it answers. `/research` runs scoping, source curation, and synthesis in one session across four depth modes. For sustained investigations, the four `research-project-*` skills run a multi-week lifecycle that accumulates a corpus and ends in a brief you can hand to a decision."
skills:
  - name: research
    description: "The primary research skill. Runs scoping, source curation, and synthesis in a single session, selecting depth from four modes — shallow through exhaustive."
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
  - name: research-project-start
    description: "Initializes a research project folder with a scoped question, source list, and corpus skeleton."
    humanTouches: 1
  - name: research-project-check
    description: "Snapshots progress: which sources are captured, what the corpus covers, and what remains."
    humanTouches: 0
  - name: research-project-digest
    description: "Summarizes the accumulated corpus into a digest artifact — the input to the final synthesis."
    humanTouches: 0
  - name: research-project-synthesize
    description: "Synthesizes the corpus digest into a brief graded by confidence, ready to hand to a decision."
    humanTouches: 1
humanGates:
  - id: G-scope
    globalGate: null
    label: "Set scope and depth"
    trigger: "Before /research or research-project-start runs"
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
docsUrl: /docs/guides/research/
packUrl: /packs/research/
relatedJourneys:
  - architect
  - core
---

## Stage 1 — Scope the question

You give the agent a question and select a depth mode. For a single-session query, the agent activates `/research` and runs a scoping pass — identifying what kind of question this is (factual, comparative, historical, open-ended) and which sources to consult. For a project-mode investigation, it runs `research-project-start` to create a corpus folder and an initial source list.

**You:** Read the scope statement the agent produces before it begins fetching. A bad scope leads to a confident answer to the wrong question — the cheapest fix is here, not after the synthesis returns. If the agent's framing misses the real question, redirect with one sentence before the retrieval subagents run.

---

## Stage 2 — Source curation

The agent runs `source-map` or its equivalent, identifying the canonical sources for the question domain. Two retrieval subagents — `evidence-retriever` and `source-extractor` — fetch and synthesize source material without polluting the main session context.

**You:** Watch the source list take shape. If a key source is missing — a specific industry report, a primary author's original paper, an internal standard you know exists — name it explicitly. The agent doesn't know what you know about your domain. A one-sentence nudge here is faster than a post-synthesis correction.

---

## Stage 3 — Synthesis and grading

After sources are captured, the agent synthesizes a brief graded by confidence (GRADE A–D). Each claim cites its source. Unsupported claims are marked explicitly as gaps, not silently omitted.

**You:** Review the synthesis at the G-synthesis gate. The confidence grades are the first thing to read — a GRADE-C synthesis needs a different follow-on action (narrow the question, run another retrieval pass, seek a domain expert) than a GRADE-A synthesis (act on it). If a claim lacks a source citation, check whether it's an inference the agent labeled correctly or an assertion it presented as fact.
