# Pre existing ruff sim102 closure index

- **Status:** Open
- **Kind:** defect

`make lint-ruff` reports one `collapsible-if` (SIM102) error at `packs/core/.apm/skills/close-work/scripts/closure_index.py:1375` with ruff 0.17.4, the newest release the unpinned local and CI install picks up. The file is unchanged since core 4.0.2 and the error appears on a clean `origin/main`, so it was not fixed during the supervisor self-describing output delivery, which never touches close-work. Fix: collapse the nested `if` in `closure_index.py`, or pin ruff in the lint install step. It unblocks when someone picks up lint health. First captured 2026-11-05.
