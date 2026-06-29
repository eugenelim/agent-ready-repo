# ADR-0038: Rename the `design-craft` pack to `experience` — live surface renamed, frozen governance bridged, no install-time alias

- **Status:** Accepted
- **Date:** 2026-06-25
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0048 Decision 3 (adopted the rename at the foundation level), RFC-0050 (the `experience`-pack child RFC that models it), RFC-0033 + ADR-0024 (created the `design-craft` pack and its posture — **frozen, bridged here**), RFC-0047 § Errata 2026-06-25 (the `infra-contract-acquisition → contract-acquisition` skill rename — the precedent this follows), `docs/specs/design-craft-pack/` (Shipped — **frozen, bridged here**)

## Decision summary

- **Decision:** We will rename the `design-craft` pack to `experience` — renaming the live surface and bridging frozen governance, with no install-time alias.
- **Because:** "experience" names the whole seat (flow + service + screen + taste + words) better than "design-craft", and the pre-stable, user-scope window makes the rename cheap now.
- **Applies to:** the pack *identity* (name + the live surfaces that carry it); the pack's posture (ADR-0024 agnosticism + all-skills-zero-agents) is unchanged.
- **Tradeoff accepted:** adopters with an installed `design-craft` must uninstall and reinstall as `experience` (no alias), and the name appears in two forms across the repo (frozen-historical vs. live).
- **Revisit if:** a pack-alias mechanism is ever designed (deferred, RFC-0048 OQ) — a future rename could then smooth the install tail (this rename does not wait for it).

## Context

The `design-craft` pack (RFC-0033, ADR-0024) ships four framework-agnostic
design-craft skills at version `0.1.1`, user-scope by default. RFC-0048
(Decision 3) decided to grow this seat into the catalogue's full design/UX
column — adding the connective UX layer (journey / service blueprint / screen
inventory) and grounding taste — and, in the same decision, to **rename the
pack `design-craft → experience`**, because "experience" names the whole seat
(flow + service + screen + taste + words) better than "design-craft" (which
reads as visual polish).

Two facts constrain *how* the rename can happen:

- **No pack-level rename/alias field exists** in the manifest or installer
  (grep-confirmed in RFC-0048). Inventing one is a distribution-mechanism RFC,
  not in scope here.
- The pack is **pre-stable (`0.1.1`) and user-scope-default**. Version is a
  recency signal, not an install-count one, so the migration window is cheap
  now and gets more expensive as the pack stabilizes.

The catalogue already has a proven rename mechanism for exactly this shape:
the **`infra-contract-acquisition → contract-acquisition`** skill rename
(RFC-0047 § Errata, 2026-06-25) renamed the live surface, kept frozen
governance naming the old skill as historical record bridged by an erratum,
and shipped **no install-time alias**.

## Decision

> We will rename the `design-craft` pack to `experience`, renaming the live
> surface and bridging frozen governance, with no install-time alias —
> following the `contract-acquisition` precedent.

Specifically:

- **Renamed (the live surface):** the pack directory `packs/design-craft/` →
  `packs/experience/`; `pack.toml` `name`/`display_name`/`description`;
  `.claude-plugin/plugin.json`; the `.claude-plugin/marketplace.json`
  aggregated entry; the guides directory `docs/guides/design-craft/` →
  `docs/guides/experience/` and the `[pack.links].documentation` URL; the
  README; cross-links in the pack's skills; **the framework-agnosticism CI lint
  `tools/lint-design-craft-agnostic.py` (scan root hardcoded to
  `packs/design-craft/`), its self-test `tools/test-lint-design-craft-agnostic.py`,
  and the two CI steps that run them** (`build-check.yml`,
  `build-check-windows.yml`) — renamed to `lint-experience-agnostic.py` /
  `test-lint-experience-agnostic.py`, scan root retargeted to `packs/experience/`,
  the `DESIGN_CRAFT_ROOT` override env var renamed `EXPERIENCE_ROOT`, and the CI
  step descriptors updated. **Two provenance pointers stay pinned to their frozen
  sources** — the RFC-0033 citation in the lint docstring and the
  `(design-craft-pack AC8)` tag in the CI step name both reference frozen
  governance (RFC-0033, the Shipped `design-craft-pack` spec); there is no
  `experience` spec/AC to repoint them to, so only the tool filename, scan root,
  env var, and leading descriptor change. And RFC-0050's implementing spec /
  changelog / backlog. The version moves `0.1.1 → 0.2.0` (the rename rides the same minor
  bump as RFC-0050's three new skills + enhancements).
- **Kept as historical record (frozen governance — NOT edited):** **RFC-0033**
  (created the pack), **ADR-0024** (its agnosticism + all-skills-zero-agents
  posture), the Shipped **`docs/specs/design-craft-pack/`** spec, and the
  `docs/rfc` / `docs/specs` README index rows that name `design-craft`. Each
  names `design-craft`; **that is the same pack, now `experience`.** Per the
  immutability convention no frozen body is edited; this ADR (and the
  `docs/product/changelog.md` entry the implementing spec adds) is the old→new
  bridge.
- **No install-time alias.** An installed `design-craft` is uninstalled and
  reinstalled as `experience` by the adopter; no alias field is added.

The decision is scoped to the pack *identity* (name + the surfaces that carry
it). The pack's **posture is unchanged** — ADR-0024's framework-agnosticism and
all-skills-zero-agents commitments carry forward to `experience` verbatim.

## Decision drivers

- **Name legibility** — the seat is the whole *experience*, not just craft; the
  name should say so.
- **Migration cost now vs. later** — pre-stable + user-scope makes the rename
  cheap today; deferring raises the cost monotonically.
- **Precedent reuse** — a proven, alias-free rename mechanism already exists
  (`contract-acquisition`); not inventing a second one.
- **Governance immutability** — frozen ADRs/RFCs/specs are bridged, never
  edited.

## Consequences

**Positive:**
- The pack name matches the seat it now fills (RFC-0050's connective layer +
  grounded taste).
- The migration is a known, bounded move (the `contract-acquisition` shape) —
  no new alias mechanism, no central registry edit.
- Frozen governance stays immutable; the bridge is recorded once, here.

**Negative:**
- Adopters with an installed `design-craft` must reinstall as `experience` —
  there is no alias to smooth it. (Mitigated by the pre-stable, user-scope,
  low-install-depth window.)
- `design-craft` now appears in two namings across the repo (frozen-historical
  vs. live), a small ongoing legibility cost the bridge note carries.

**Revisit if:** a pack-alias mechanism is ever designed (deferred, RFC-0048 OQ) — a future rename could then smooth the install tail (this rename does not wait for it).

## Confirmation

- **Mode:** lint/CI.
- **Signal:** the implementing spec (`docs/specs/experience-pack/`) and the CI manifest/lint gates confirm the live surface carries `experience` consistently (pack dir, manifests, marketplace aggregation, guides, cross-links) and that no live surface still names `design-craft`; a `docs/product/changelog.md` entry records the user-visible rename.
- **Owner:** RFC-0050's implementing-spec owner (the `experience-pack` spec + its CI gates).

## Alternatives considered

- **Grow `design-craft` in place, keep the name** — rejected against *name
  legibility*: the seat outgrows the name, and the cheap-rename window
  (pre-stable) is forfeited (RFC-0050 Option B).
- **Ship an install-time pack alias** — rejected against *precedent reuse* and
  *scope*: no alias field exists; adding one is a distribution-mechanism RFC,
  and the `contract-acquisition` precedent shipped no alias.
- **Edit frozen RFC-0033 / ADR-0024 to the new name** — rejected against
  *governance immutability*: frozen bodies are bridged, not edited.

## References

- RFC-0048 Decision 3 (`docs/rfc/0048-autonomous-product-team-operating-model.md`).
- RFC-0050, the `experience`-pack child RFC (`docs/rfc/0050-the-experience-pack.md`).
- RFC-0047 § Errata 2026-06-25 (the `contract-acquisition` rename precedent).
- RFC-0033, ADR-0024, `docs/specs/design-craft-pack/` (the frozen governance bridged here).
