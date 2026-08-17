# Implementation review — round 1

## Blockers

**1. Behavior eval execution is not recorded.** `docs/specs/project-knowledge-authoring-integrations/notes/manual-qa.md:52`

Fix: run the repository's behavior/judge eval surface for all six changed
skills or record an explicit environment-bound deferral with structural eval
evidence.

**2. Producer request and confinement tests are incomplete.** `packs/core/tests/skills/work-loop/test_project_knowledge_handoff.py:84`

Fix: pin every required top-level and nested request field plus lexical
traversal, link/junction/reparse escape, non-file, I/O, and uncertainty refusal.

**3. Terminal knowledge diffs can bypass the review return.** `packs/governance-extras/.apm/skills/new-rfc/SKILL.md:351`

Fix: route journal, topic, or map diffs through the producer's applicable
verification and review barrier before its final completion receipt.

**4. The ADR abandoned-path eval expects a non-gate lookup.** `packs/governance-extras/.apm/skills/new-adr/evals/evals.json:76`

Fix: require no provider lookup, unavailable skip, capture, distillation, or
fallback before `adr-accepted`.

**5. Living docs contradict current writer and integration behavior.** `docs/knowledge/README.md:88`

Fix: retire legacy append guidance and update the architecture component map
and spec index.

## Concerns

**6. Producer root discovery does not clear Git relocation variables.** `packs/core/.apm/skills/receive-brief/SKILL.md:187`

Fix: align each producer with the shipped writer root-resolution contract
before real-path containment or committed-blob lookup.

**7. Author-brief activation coverage is below the pack convention.** `packs/core/.apm/skills/author-brief/evals/eval_queries.json:1`

Fix: add realistic positives and adjacent near misses.

**8. Common handoff prose is repeated across five producers.** `packs/core/.apm/skills/receive-brief/SKILL.md:175`

Disposition proposed: decline extraction because the approved design keeps
executable gate behavior local, crosses two independently versioned packs, and
adds no shared helper/reference surface; retain synchronized construction
assertions and evals instead.

**9. Manual QA and lifecycle closeout are incomplete.** `docs/specs/project-knowledge-authoring-integrations/notes/manual-qa.md:68`

Fix: after all findings and gates are clean, record final reviews and named
environment limitations, mark every AC, and finalize spec/plan/index status.
