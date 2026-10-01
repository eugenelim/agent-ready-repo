---
generated: true
journey_id: code-intelligence
pack: code-intelligence
start_state: read-only
end_state: read-only
scope: repo
tagline: "Find out what is actually true about a codebase before you change it"
prerequisitePacks: []
contract:
  useItWhen: "You need to know what calls something, what a change would break, how an unfamiliar system is organised, or where a behaviour is implemented — and you want the answer from a resolved call graph rather than a text search."
  youType: "What breaks if I change the request handler?"
  youProvide: "A repository indexed with `wicked-estate index .`, and the symbol, module, or behaviour you are asking about. Nothing else — the pack never writes to the graph without asking."
  youReceive: "An answer grounded in the index, carrying the index's own limits: how many references it could not resolve, whether output was truncated, and which revision it describes. Where the graph cannot answer, you are told that rather than given a guess."
  yourDecisions:
    - "Confirm which symbol was meant when a name resolves to more than one"
    - "Approve building or refreshing the index, which writes into the working tree"
    - "Decide what to do with the evidence — the pack reports, it does not recommend changes"
  decisionGateIds:
    - confirm-ambiguous-symbol
    - approve-index-build
humanGates:
  - id: confirm-ambiguous-symbol
    globalGate: null
    label: "Confirm which symbol you meant"
    trigger: "When a name resolves to more than one symbol, before any analysis runs on it"
    duration: "under a minute"
    whatToCheck:
      - "Does the file path of the chosen match point at the code you had in mind?"
      - "If two matches look plausible, is one of them a vendored or generated copy?"
      - "Did the agent pick for a stated reason, or silently take the first hit?"
    whatGoodLooksLike: "Every match listed with its file and line, and either a question to you or a named reason for the choice."
    whatBadLooksLike: "One symbol analysed with no mention that the name was ambiguous."
    consequence: "Impact analysis on the wrong overload is worse than none — it reads as evidence while describing different code."
  - id: approve-index-build
    globalGate: null
    label: "Approve building the index"
    trigger: "Before the agent runs `wicked-estate index`, which writes into your working tree"
    duration: "under a minute, then several minutes unattended"
    whatToCheck:
      - "Is `.wicked-estate/` ignored by version control? The database is a few hundred megabytes."
      - "Are you indexing the repository you meant, and not a parent directory?"
      - "If an index already exists, is rebuilding it what you want, or is the existing one fine?"
    whatGoodLooksLike: "The target path stated, the write disclosed, and the gitignore checked before the command runs."
    whatBadLooksLike: "A large database appearing in your working tree, or committed, because nobody mentioned it."
    consequence: "An un-ignored index dirties every status check and can be committed by accident; a stale one silently answers questions about an older revision."
whatChanges: "Before, an agent answering \"what depends on this?\" grepped for a name and produced a list it could not vouch for — no way to tell a real call from a coincidence, and no way to say what it missed. After installing this pack, the same question is answered from resolved call and import edges, and the answer states what the indexer could not bind. The habit matters more than the tool: resolve the symbol before reading it, read the source before concluding, stop when the question is answered, and never present a text search as a blast radius."
skills:
  - name: code-intelligence
    description: "Query an indexed code graph through five reusable investigation patterns — understand an entity, analyze change impact, investigate behavior, analyze architecture, assemble task context — preserving the provenance, confidence and completeness the index reports. Read-only; degrades to labelled repository search when no index is present."
    humanTouches: 1
agents:
  - name: code-investigator
    description: "Forked-context, read-only subsystem and behaviour investigation. Returns findings labelled observed, verified, or unestablished."
  - name: impact-analyst
    description: "Forked-context, read-only change-impact analysis. Leads with its own completeness limits rather than burying them."
---

# Code intelligence

Point an agent at a question about your codebase and get an answer it can show
its working for.

The pack drives the [Wicked Estate](https://github.com/mikeparcewski/wicked-estate)
command-line tool against an index you build. It is read-only by default: the
commands that write to the graph are named, and each one asks first.

What it will not do is guess. If the index cannot answer — and the pack ships a
fourteen-point assessment of exactly what it cannot — you are told so, with what
it can tell you instead.
