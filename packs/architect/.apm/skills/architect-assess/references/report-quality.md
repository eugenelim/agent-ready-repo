# Assessment report quality self-check

Before closing, pressure-test the report:

- The report has five parts, each opening with a line that starts "Read this part
  to" and says what the reader can do after it. A section sits in the part that
  serves that outcome: do not move findings into Part 3 or recommendations into
  Part 4.
- A sponsor who reads only the Bottom line, Key themes, and Prioritized
  recommendations can state the verdict, the first action, and the decision
  needed. The Bottom line opens with its five fixed fields.
- Each theme is a full-sentence claim, not a topic label, and names the findings
  that support it.
- Recommendations are ranked P1 to P3 with a reason, an effort size, and the
  finding IDs they answer. Every P1 and P2 finding has one, and no recommendation
  lacks a finding.
- The "How to read this report" terms table is kept verbatim.
- The Bottom line carries a "Working well" field next to the verdict, so a
  sponsor sees what to protect as well as what to fix.
- Findings by area has one row for every one of the six areas. Each finding names
  its area, and the index agrees with the findings. A row says `none found` only
  when the area was assessed, and `not assessed` when no evidence was read.
- Technology and dependencies states `not assessed` for the dependency inventory
  when no lock file or dependency graph was analysed.
- A wave's indicative horizon, if given, is an estimate or an objective and does
  not reorder the waves.
- Scope matches the accepted charter and names exclusions.
- The conceptual model distinguishes repositories, deployables, runtimes, data,
  and external systems; folders are not treated as components by default.
- Every required evidence surface has a status and missing evidence remains
  visible.
- Target evidence, enterprise context, and pack knowledge are separately
  attributed.
- Heat shows raw dimensions and is used only to select drill-downs.
- Each finding traces observation → mechanism → consequence/scenario and carries
  counter-evidence, confidence, validation gap, and smallest safe response.
- Triggered lenses have explicit coverage; a readiness statement does not skip
  material agentic or knowledge-platform contracts.
- Strengths, non-risks, alternative explanations, and unknowns survive editing.
- Every action wave traces to finding IDs and includes prerequisites,
  completion proof, containment/rollback, owner class, and non-goals.
- The next decision is human-readable and the report does not imply that a
  survey completed investigation.

If any item fails, repair the report or narrow its conclusion. This self-check
does not certify the report; independent review uses its own assessment rubric.
