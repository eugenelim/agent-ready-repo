# Plan Evolution Experiments Methodology

This research record is standalone by design. It freezes the pilot method before any model worker launches and does not depend on the delivery spec directory.

The pilot tests H1 through H13 from the frozen workbench design. The durable design fixture names each hypothesis, its comparison, primary measure, evidence class, and verdict rule. The study records direct pilot evidence separately from retrospective, proxy, and source evidence.

Quality is the gate. Speed, token savings, and reviewer-churn reductions count only when the quality guardrail holds: hidden oracle success, no sustained critical or high defect, no critical semantic drift, and no prohibited file change.

The staged process ceiling is 240 total model processes: 8 instrument calibration, 160 core experiment, 36 independent review, 12 blind adjudication, and 24 adaptive reserve. The first fixed release permits ordinals 1 through 80. Later fixed and reserve ordinals require gate memos and are refused by the workbench until released.

The exact source URL inventory is frozen in
`tools/plan_evolution_workbench/fixtures/valid-design.json`. It includes the
Hacker News threads, the source article, Nuanced posts, Plannotator, Stencil,
Claude permission documentation, Superpowers, clops, Whiteboard, the Assumption
Problem, the three cited studies, the comment-linked example projects, the
context-window social post, TeamKit, and both Breadcrumb pages. Each record
stores the ordinary HTTPS URL, its exact `pure.md` recovery form, and retrieval
status. This file is the readable method summary; the JSON inventory is the
machine-checked authority.

The workbench performs no HTTP, DNS, webhook, or arbitrary URL retrieval. Unsupported or unlisted links are recorded as unavailable evidence unless a supported first-party retrieval tool or owner-supplied content provides them outside the workbench.

T1 implements dry-run command construction only. It records redacted argv arrays, sandbox policy, environment allowlist, prompt digest, and limits without starting Codex.
