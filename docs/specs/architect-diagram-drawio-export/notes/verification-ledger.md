# Verification ledger: architect-diagram draw.io export

Execution observations for the approved plan. This file is not hash-pinned; it
records how tasks were verified, not new obligations.

## Fixture provenance (T1, 2026-10-15)

- CLI: draw.io Desktop 32.4.1 (macOS arm64), run from the official release
  `.dmg` mounted read-only; the `.dmg` SHA-256 matched the release's
  `Files-SHA256-Hashes.txt`.
- Command, per fixture:
  `draw.io --disable-update -x -f xml -u -o testdata/<stem>.drawio testdata/<stem>.mmd`
- Results: `flowchart-tb` exit 0, `sequence` exit 0, `architecture-beta` exit 0.
- Label check: every Mermaid node and participant label in each `.mmd` appears
  as a cell value in its `.drawio` (sequence aliases appear as their display
  text, not their ids).

## Mutation run (AC-0005, 2026-10-15)

Command: `python3 -m pytest packs/architect/tests/skills/architect-diagram/test_drawio_fixtures.py -v`
(19 passed). Each mutation is applied to a copy of `flowchart-tb.drawio` and the
checker must reject it; each control must pass.

| Case | Expected | Observed |
| --- | --- | --- |
| missing `.mmd` sibling | rejected | rejected |
| compressed diagram | rejected | rejected |
| no vertex | rejected | rejected |
| duplicate id | rejected | rejected |
| dangling edge | rejected | rejected |
| `link` attribute | rejected | rejected |
| `<a href` in a label | rejected | rejected |
| style `image=` of `java` + TAB + `script:alert(1)` | rejected | rejected |
| skeleton edge without `source` | rejected | rejected |
| control label `Metadata: store` | passes | passes |
| control label `a < b` | passes | passes |
| control label `x <and y` | passes | passes |

## Edge endpoints in CLI output (AC-0003, 2026-10-15)

`sequence.drawio` from the CLI has 5 of its 10 message edges with one end
floating (no `source` or no `target` attribute; the end is a point on a
lifeline). The suite checks that every endpoint present names an existing
cell, and demands both endpoints only for the agent-written fallback and the
reference skeleton.

## Owner decision: contract amendment (2026-10-15)

The owner (eugenelim) chose a formal amendment for two corrections the work
proved necessary: AC-0003's edge rule must allow a floating endpoint in CLI
output, and the plan's old-CLI upgrade offer is replaced by a manual-upgrade
link plus the fallback, because the allowlisted install commands do not
upgrade an existing copy.

## Skeleton endpoint check can fail (T7, 2026-10-15)

Replacing the `require_endpoints` branch in `check_model` with `if False:` made
`test_skeleton_edge_without_source_rejected` fail (1 failed, 18 passed);
restoring it made the suite pass (19 passed).
