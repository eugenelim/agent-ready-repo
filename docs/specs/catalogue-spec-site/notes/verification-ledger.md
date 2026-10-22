# Verification ledger — catalogue-spec-site

- 2026-10-22, T4: local build of both sites (`build-site.py`, web and docs-site builds) passed `check-rendered-site-links.py` (36,892 links across 640 pages, clean) and the web rendered-output suite (240 tests). The docs site built 303 pages, inside the 330 budget, so the budget and heap are unchanged.
- 2026-10-22, T4: `pages.yml` build job passed on this branch at `81ce1dd39` through the pull request's own run: https://github.com/eugenelim/agent-ready-repo/actions/runs/39779726682. The branch targets `main` after S1 and S2 merged, so the `pull_request` trigger ran it and no `workflow_dispatch` was needed.
