# Pre-existing defect: current ruff flags closure_index.py's nested ifs

- **Kind:** defect
- **Status:** Open
- **Discovered:** 2026-11-05, during the promotion-drain-hardening gates
- **File:** `packs/core/.apm/skills/close-work/scripts/closure_index.py:1375`

## What fails

`ruff check .` under ruff 0.17.4 reports one `collapsible-if` (SIM102)
violation at
`packs/core/.apm/skills/close-work/scripts/closure_index.py:1375`, inside
`close-work`'s brief-route refusal handling. The same tree passes every
check under ruff 0.14.0, 0.16.10, and 0.17.2 — each verified by a run on
this tree; the flagging change landed between 0.17.2 and 0.17.4, so an
unpinned install that resolves 0.17.4 reds on a clean post-merge tree.
(Coverage of the first round's range claim "0.15+": the 0.17.2 pass
contradicted it, which this correction records.)

CI runs the ruff version pinned in `tools/requirements.txt` (`0.16.10`,
green on this tree): the workflow's bare `pip install ruff mypy` runs
after the "Install tools requirements" step and leaves that pin in place.
The promotion-drain-hardening delivery's own gate evidence ran under
ruff 0.14.0 — also green on this tree. Un-pin or re-pin
`tools/requirements.txt` only with a run verifying the new version on a
clean tree, and lift past 0.17.2 only after the nested-`if` fix below
lands.

## Why it is pre-existing

The failing file is byte-identical to `origin/main` at `74f4b7248` (merged
in PR #1665); the promotion-drain-hardening branch never touches it. At
discovery time the delivery's local gates ran ruff 0.14.0 while an
unpinned resolution fetched 0.17.4, which re-flagged code that was green
when it merged; the parity record above is the correction.

## Known-skip treatment

Gate runs on this branch treat the violation as a known skip and pin ruff
0.14.0 — the version the file was green under — for the local gate
evidence. Fixing the nested-`if` is a one-line `and` merge owned by the
`close-work` skill, out of this delivery's scope.
