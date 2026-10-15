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
