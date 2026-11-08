# work-intake describes captured-item headers in a form dispatch.py rejects

- **Status:** Open
- **Kind:** defect

## Summary

The `work-intake` skill describes a captured item's preamble as `Status:` and `Kind:` lines, and `dispatch.py` accepts only the bullet form `- **Status:** Open`, so an item written to the skill's contract fails validation.

## Observed

On 2026-11-07, in a scratch repository with `core` 4.0.21 installed, a headless agent run of `work-intake` ("remember the configurable retry backoff follow-on ... stop without implementation") wrote `docs/product/captured/configurable-retry-backoff.md` with bare `Status: Open` and `Kind: design` lines. `dispatch.py --root . --captured` then reported `invalid_captured_item` with field `Status`. The parser is `_HEADER_FIELD_RE` in `packs/core/.apm/skills/work-loop/scripts/_header_readiness.py`; the contract text is in `packs/core/.apm/skills/work-intake/SKILL.md`, the captured-item section. Rewriting the two lines in bullet form made the item list as valid.

## Intended

The skill's contract and the dispatch parser agree on one header form, and a test writes a captured item through the contract and passes it to `dispatch.py`.
