# Docs site print rendering is tuned for paper

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/docs-site-design-refresh Assumptions](../../specs/docs-site-design-refresh/spec.md)

## Outcome

The docs site has paper-specific aesthetic tuning beyond correct printable content.

## Opportunity

Print rendering remains at Starlight defaults, leaving accent colors and hairlines untuned for paper. Print-chrome suppression shipped, but `docs/specs/site-browser-quality-gate/notes/print-audit.md:305` explicitly leaves `workspace.toml [backlog].open` slug `docs-site-print-styles` open.

## What this absorbs

### docs-site-print-styles

The `docs-site-design-refresh` deferral remains open for paper aesthetics. The SCA half, `docs-site-npm-sca-gap`, was discharged by `spec/npm-sca-gate` and ADR-0083: `tools/audit-npm.py` now runs as a `make sast` leg. The `spec/site-browser-quality-gate` print audit on 2026-08-18 closed `close-stale` after measuring content integrity on six representative routes listed in its Measured axes section. It added no print CSS because its decision rule bars preference-based proposals. This item is distinct: print correctness is settled, while paper aesthetic tuning remains open. A reader must not treat the audit as settling the tuning work.

## Assumptions

- The 2026-08-18 audit established print content integrity only; it did not evaluate paper aesthetics.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
