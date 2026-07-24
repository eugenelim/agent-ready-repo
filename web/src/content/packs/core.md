---
name: Core
scope: repo
tagline: "The build loop. Spec → shipped code. Supervised."
skills:
  - work-loop
  - new-spec
  - bug-fix
  - frontend-engineering
  - contract-acquisition
  - receive-brief
  - init-project
  - adapt-to-project
installCommand: "agentbundle install --pack core"
docsUrl: /docs/guides/core/
journeyUrl: /journeys/core/
---

Core is the engine of the build loop. After installing it, every coding task runs through `work-loop`: plan → execute → verify → adversarial review. You get mechanical gates (lint, typecheck, tests) and three specialist reviewers who read every diff cold. The loop cannot self-certify — it always surfaces to you at plan approval and PR merge.

The `frontend-engineering` skill operates in four modes: **create** (new surface), **retrofit** (improving an existing surface), **audit** (reviewing without writing code), and **verify** (running the full gate suite and generating an evidence manifest). Create mode requires a page/screen contract before significant UI code; verify mode produces a structured evidence record covering CWV performance, accessibility, and browser coverage.
