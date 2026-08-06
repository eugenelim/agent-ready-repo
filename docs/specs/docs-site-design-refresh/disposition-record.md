# Resolve-vs-surface disposition record: docs-site-design-refresh

Opened at PLAN (2026-08-05); closed at DECIDE. Records what was resolved by
the loop vs. surfaced to the human, per the work-loop self-coverage gate.

## Resolved by the loop (with authority source)

- **Palette values (cobalt-family, cool grounds)** — user delegated
  explicitly ("pick a good color theme that lends engineering capability
  and enterprise professionalism and polish"); values derived in plan LLD
  and numerically verified.
- **Display serif choice (Source Serif 4 Variable over the reference's
  serif)** — within the delegated enterprise register; rationale in
  creative-direction.md (crisper cut, same optical-sizing capability).
- **Mermaid bundling (AC9)** — user asked what the reference does and the
  reference's bundled-pinned pattern was adopted in conversation
  (2026-08-05); resolves the security reviewer's CDN concern.
- **Per-site AGENTS.md split** — user directed in-session ("you can move
  the web/CLAUDE.md into separate folders per site").
- **No reference-site name in-tree** — user directed in-session ("leave out
  the site name"); extended to anonymizing all vendor precedents per the
  repo privacy rule (round-1 adversarial Blocker).
- **Theme default stays `auto`** — decision recorded in AC5.
- **State-token carve-out** — hue-distinct semantic colors preserved
  (round-3 adversarial Blocker), measured pairs recorded in plan LLD.
- **Spec/plan approval gates** — the G-plan approvals were exercised on the
  strength of the user's explicit in-session scope direction (see Brief);
  the PR review is the human merge gate (CODE-HUMAN-GATE). If this
  delegation is wrong, reject at PR review and the loop re-enters via
  `blocker-applied`.

## Surfaced to the human (open at PR)

- **Marketing-site palette divergence** — `web/` keeps amber/dark-hero
  while docs go cobalt. Re-skinning `web/` to match is a named follow-on
  decision in the PR description; not executed.
- **Deferrals** — `docs-site-npm-sca-gap` (no SCA scanner repo-wide; docs
  now vendor mermaid's transitive tree) and `docs-site-print-styles`;
  recorded in `workspace.toml [backlog].open`.

## REVIEW findings ledger

- Round 1 (adversarial 4B/6C/5N + security 4C): all resolved in spec
  revision (plan changelog, round-2 entry).
- Round 2 (adversarial 1B/2C/2N + security 1C): all resolved (round-3
  changelog entry).
- Round 3 (adversarial 1B/2C/1N): all resolved (round-3 changelog entry).
- Round 4: adversarial Clean; security Clean (round-3 confirmation).
- Post-EXECUTE findings: recorded below when the implementation review
  runs. <!-- updated at DECIDE -->
