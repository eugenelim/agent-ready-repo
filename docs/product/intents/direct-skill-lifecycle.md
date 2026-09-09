# Keeping a directly installed skill current

- **Status:** Draft
- **Level:** feature
- **Scale:** app

## Outcome

An adopter who installed a skill straight from someone else's repository can bring it to a known-current state, and see what changed, without remembering the source string or hand-editing state.

**Steerable input:** the share of directly installed skills reachable by an update path that names what changed. Today it is zero: `upgrade` requires `--pack` or `--all` and exits 2 on a bare `--skill`, and an install naming a different revision is refused as a different source (`CAT-D009`), so an installed skill has no route to a later revision at all.

**Lagging outcome:** adopters keep third-party skills current rather than install-and-forget, so a defect the publisher fixed actually reaches the agent that runs it.

**Guardrail:** an update never consents to less than an install does. Install already prints the full declared capability surface and refuses without confirmation; an update that widened `allowed-tools` behind a quieter prompt would be a regression in the safety posture, not a feature.

## Opportunity

**Functional job.** Keep a skill I took from another repository up to date, and know what I am getting before it lands in my agent's instructions.

**Emotional job.** Not to feel that installing third-party instructions took on an unbounded liability I have no way to re-inspect.

**Social job.** To be able to tell a teammate what is installed, where it came from, and that nothing widened since we agreed to it.

**Struggling moment.** The publisher fixes something. My only route is to remember the original source string, re-run install, and re-read a full capability summary hunting for the line that differs — so I do not, and the skill silently ages.

## Assumptions

- The audience is the adopters the shipped direct-install feature already serves, across all eight adapters — confirmed by the scope owner, 2026-09-01.
- Install already carries the consent surface an update needs, so the update path is that surface plus a delta rather than a second route — probed against the built CLI: install without `--yes` prints `allowed-tools`, `boundaries`, `credentialed`, and digests, then refuses.
- Old capability values are recoverable from the installed projection, so no state-schema change is required — probed: `parse_bounded_metadata` reads `allowed-tools` back out of the projected `SKILL.md`.
- Knowledge surface consulted: in-repo doc set (`docs/product/intents/`, `docs/product/journeys/`, `docs/specs/`). No in-flight intent or brief frames direct lifecycle, so this is not a duplicate bet.
- No adopter journey covers direct install today; the nearest current-state inputs are `engineer-adopts-coordination.md` and `engineer-provisions-infrastructure.md`, neither of which reaches a third-party skill source. Offered as a brownfield input and not taken, so the struggling moment above is reasoned from the CLI's observed behaviour rather than from a mapped journey.
- Per-skill inspection **does** need its own surface. This was first assumed redundant with `list-installed --format json` and the assumption was tested and refuted: `show` returns a pack's contents while `list-installed` returns its installation record, and neither renders the declared capability surface. Probed on an installed direct skill — `show`, `list-installed --format json`, and `.agentbundle-state.toml` each carry zero of `allowed-tools`, `boundaries`, `credentialed`. An adopter who consented at install has no route back to what they agreed to.
- An update **is** a verb. RFC-0098 D4 mandates `upgrade --skill <name>` without `--pack`: it re-resolves the recorded source and path, re-runs admissibility, previews the file plan, and replaces it; D6 gives it repository, user, and local scope, and no erratum retires either. An earlier draft of this intent claimed the opposite, reasoning from the parent spec's AC22 rather than from the RFC decision that governs it; that reasoning also proved too much, since it would have forbidden remote install as well.

## Source

- Mode: repo-origin
- Locator: docs/specs/direct-skill-repository-installation/spec.md
- Revision: c794be99c
