# Agent skill engineering has a dedicated guide route

- **Slug:** `agent-skill-engineering-guide-slice`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **De-risked:** 2026-11-05
- **Governed by:** [spec/agent-skill-engineering-foundation AC21](../../specs/agent-skill-engineering-foundation/spec.md)

## Outcome

An adopter of the agent-skill-engineering pack finds a dedicated guide from the guides index and from the pack's site page, and the guide gate no longer exempts the pack.

## Opportunity

`agent-skill-engineering` is the only pack in `GUIDE_OPTIONAL_PACKS`, its site record sets `docsUrl: /docs/guides/`, and the planned documentation slice has not yet supplied the dedicated guide.

## What this absorbs

### agent-skill-engineering-guide-and-docsurl

- The owner decision is dated 2026-08-27.
- Add `guides/agent-skill-engineering/`.
- Link it from `guides/README.md`.
- Drop the `GUIDE_OPTIONAL_PACKS` exemption.
- Repoint the site `docsUrl` from the guides index to the dedicated guide.
- The `GUIDE_OPTIONAL_PACKS` comment in `tools/check-guide-index.py` records that the M1 slice shipped the portable pack and left the guide to a later planned documentation slice.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Readiness

Route: direct-light, one session. Checked 2026-11-05: `guides/agent-skill-engineering/` does not exist, `tools/check-guide-index.py` still lists the pack in `GUIDE_OPTIONAL_PACKS`, and `web/src/content/packs/agent-skill-engineering.md` still has `docsUrl: /docs/guides/`. Change: add the guide, link it from `guides/README.md`, remove the exemption, repoint `docsUrl`. Agent-only proof: `tools/check-guide-index.py` passes with the exemption removed, and the web content schema test passes.

## Non-goals

- Other packs' guides, and any change to the guide-index gate beyond removing this pack's exemption.
- New agent-skill-engineering skills or behavior.

**Riskiest assumption:** the guide-index gate and the web content schema accept the new guide and repointed `docsUrl` without other edits. Tested agent-only by running `tools/check-guide-index.py` with the exemption removed and the web content schema test.

## De-risk result

2026-11-05. Ran a copy of `tools/check-guide-index.py` in a scratch tree with the `GUIDE_OPTIONAL_PACKS` exemption removed. With no guide-home link the gate fails and names `agent-skill-engineering` (1 of 22 packs); after adding the single link `agent-skill-engineering/` to a copy of `guides/README.md` it passes (22 of 22). The web content schema types `docsUrl` as a plain string, and the only tool that reads it is the pack-journey lint, so repointing it needs no other gate change. Verdict: supported. The web build was not run; that stays in the work-loop session.
