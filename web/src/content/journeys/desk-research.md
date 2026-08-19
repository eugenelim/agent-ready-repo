---
generated: true
journey_id: desk-research
pack: desk-research
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Evidence-grounded desk research — portable across every repo."
prerequisitePacks: []
contract:
  useItWhen: "You have a question that needs evidence grounded in primary sources — single-session query or a sustained multi-week investigation."
  youProvide: "A research question, a chosen depth mode, and any known sources or prior corpus."
  youReceive: "A confidence-graded synthesis brief citing primary sources, with an explicit gap map."
  decisionGateIds:
    - set-research-scope-and-depth
    - review-research-synthesis
whatChanges: "After installing desk-research, every question your agent takes on is evidence-grounded before it answers. `desk-research` runs scoping, source curation, and synthesis in one session across four depth modes. For sustained investigations, the four `desk-research-project-*` skills run a lifecycle that accumulates a corpus and ends in a confidence-graded brief. Gaps are named explicitly — honest gaps are better than false confidence."
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
  - id: set-research-scope-and-depth
    globalGate: null
    label: "Set the research scope and depth"
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
  - id: review-research-synthesis
    globalGate: null
    label: "Review the research synthesis"
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

| Say this | What happens |
|----------|--------------|
| `desk-research` | Single-session research — scoping, retrieval, synthesis in one pass |
| `source-map` | Map canonical sources before retrieval begins |
| `build-outline` | Build a research outline from the source map |
| `identify-perspectives` | Map stakeholder perspectives before synthesis |
| `compare-hypotheses` | Competing-hypotheses pipeline — scored matrix |
| `devils-advocate` | Steelman the opposing case |
| `decision-archaeology` | Reconstruct why a prior decision was made |
| `desk-research-project-start` | Initialize a sustained multi-week research project |
| `desk-research-project-status` | Orient to an active project — phase, hypothesis, what's next |
| `desk-research-project-check` | Snapshot progress — sources captured, coverage, gaps |
| `desk-research-project-digest` | Summarize corpus into a synthesis matrix |
| `desk-research-project-synthesize` | Synthesize digest into a confidence-graded brief |

---

### Optional knowledge boundary

Project knowledge is not part of the research pipeline. Research retains
authority over its source corpus and every survey, citation, claim, confidence
assessment, counterpoint, verdict, and governance brief. Quick and non-survey
session work, project scaffolding, digest, check, status, and any incomplete or
abandoned path perform no knowledge handoff.

Only a completed repository-contained standard, applied, or deep survey, or a
completed project synthesis, may optionally hand independently reusable
practice or sanitized evidence residue to `project-knowledge`. Personal and
external output roots remain capture-ineligible. A `devils-advocate` review may
instead ask one bounded `CQ-REVIEW` question for candidate counter-checks, but
must verify every research claim from independent direct sources and never
capture or distil the retrieved result.

---

### 1. Scope the question

Type `desk-research` and describe what you want to find out — the agent maps the source space and surfaces its scoping assumptions before retrieving anything.

```text
desk-research "What drives deployment frequency in platform engineering teams?"

  Mode:     standard
  Sources:  DORA reports, Google Cloud DevOps research, academic CS
  Scope:    peer-reviewed + grey literature, 2019–2024

  Approve scope? ›
```

- **You decide:** approve scope and depth before retrieval begins — a bad scope returns a synthesis that answers the wrong question.
- **Output:** a confirmed scope statement with chosen depth mode.
- **State:** read-only

---

### 2. Curate sources

The agent runs `source-map` to identify the canonical sources for the domain, then dispatches retrieval subagents to fetch and extract material.

```text
  ● evidence-retriever   running  DORA 2023 State of DevOps
  ✓ source-extractor     done     accelerate.io — 3 findings extracted
  ● evidence-retriever   running  Google Cloud DevOps metrics guide
  ○ synthesis            idle
```

- **Output:** a curated source set with fetched material ready for synthesis.
- **State:** read-only

---

### 3. Synthesize and grade

The agent synthesizes findings into a brief — every claim carries a GRADE confidence tag and a source citation; gaps are named in a `## Known unknowns` section.

```text
  brief  deployment-frequency-brief.md

  Bottom line:  Trunk-based development and automated testing pipelines
                are the strongest predictors of deployment frequency.

    Claim                                              Grade      Sources
    Trunk-based development → 4× deployment rate     [high]      4 independent
    Test automation → 2× deployment rate              [high]      3 independent
    Platform team structure → moderate effect         [moderate]  3; downgrade: org-confound

  Known unknowns
    Known-unknown: effect isolated to platform eng. Would close by: segmented DORA data.
```

- **You decide:** review the synthesized brief — if confidence is low, narrow the question or run another retrieval pass before acting on findings.
- **Output:** a confidence-graded brief with cited sources and explicit gap map.
- **State:** confirmed-write
