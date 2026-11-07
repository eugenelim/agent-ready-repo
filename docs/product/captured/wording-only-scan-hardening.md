# Wording-only scan hardening

- **Status:** Open
- **Kind:** defect

The work-loop supervisor's `wording-only` review tier ships disabled (`wording_only_enabled: false` in `packs/core/.apm/skills/work-loop/review-rules.json`), because code review kept finding Markdown inputs the scan misreads as plain prose. A change to a line inside any of these classifies `wording-only` when the tier is on:
- a code fence or raw HTML block that follows a list marker;
- indented code reached through mixed tab-space indentation, or five or more spaces after a list marker;
- a code span or inline HTML that opens on an unchanged line and encloses a changed one;
- continuation lines of a reference link definition.
Also decide whether GFM inline math counts as non-prose. Turning the tier on needs the owner's approval once these are closed. Source: spec `docs/specs/review-obligation-policy/spec.md` Follow-ons; ADR-0158 Errata.
