# Eval results

Evals 13 and 14 in `packs/architect/.apm/skills/architect-assess/evals/evals.json`
were run on 2026-10-30. Each run used a fresh cold session. The session read only a
copy of the skill with every `evals/` directory removed (checked: zero
remain) and a seven-file fixture repository; it saw the task text and nothing
else. Each output was graded by a separate session that saw only the output file and
the assertions, never the prompt.

| Eval | Run | Result | Notes |
| --- | --- | --- | --- |
| 13 cannot-pause run | 1 | PASS, 6 of 6 | Charter line, both checkpoint lines, the three tables, and no file written. |
| 14 no deployment evidence | 1 | FAIL, 3 of 4 | The subsection began `not assessed. The repository has no ...` on one line; the assertion wants the line to be exactly `not assessed`. |
| 14 no deployment evidence | 2, after the template and reference said `not assessed` stands on its own line | PASS, 4 of 4 | First line is `not assessed`, the reason follows, and the subsection ends with its table. |

The first run of eval 14 showed the template wording was ambiguous, and the
wording was tightened before the second run. Eval 13's prompt was also changed
before its only run, from "save the assessment" to "show me the full assessment",
because a headless run cannot approve a write.

Limits: one run per case, one fixture, and graders are model sessions.
Assertion 6 of eval 13 (writes no file) rests on the run's own statement plus a
file count of the fixture before and after (7 files each).
