# Brief: an adopter can see what a skill update changes and what they consented to

- **Slug:** `direct-skill-lifecycle-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as committed in `a96a878c4`, which an independent delivery-brief review returned `Clean` with no open Ready gap. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** [`direct-skill-lifecycle`](../intents/direct-skill-lifecycle.md) and the follow-ons recorded in [`docs/specs/direct-skill-lifecycle/spec.md`](../../specs/direct-skill-lifecycle/spec.md)
- **Parent intent:** intent:direct-skill-lifecycle

## Outcome

An adopter of a directly installed skill can inspect the capability surface they consented to, and can see the old-to-new capability difference before accepting an update.

## Success metrics

- One command shows `allowed-tools`, `boundaries`, and credentialed status for an installed direct skill, where `show` and `list-installed` show none of them today.
- `upgrade --skill` prints the capability difference and refuses a widening update unless the adopter passes an explicit acceptance flag.
- `upgrade --all` never accepts a widening silently. Its behaviour without a terminal is left to D2's spec, which reconciles the shipped spec's all-or-nothing re-consent wording with RFC-0098 D6's no-picker rule.

## Scope / Non-goals

In scope: the inspection surface, difference rendering, the acceptance flag, and bulk re-consent.

Out of scope: `--scope local` upgrade, persisted receipts, and any change to what install asks for.

## Constraints / Appetite

Two slices, two sessions. `upgrade --skill` exists ([spec](../../specs/direct-skill-lifecycle/spec.md)) and refuses a widening update; `agentbundle upgrade --help` shows `--skill`, `--source`, and `--yes`, and no acceptance flag. A consent decision is a safety posture, so D2's Gating cell requires a security review. Protected `packages/agentbundle/**` needs an `Engine-Change-RFC:` trailer naming RFC-0098.

## Proposed slices

| # | Slice | Primary owning surface | Verification | Gating |
| --- | --- | --- | --- | --- |
| D1 | Per-skill inspection of the declared capability surface, read back from the projected `SKILL.md` | `agentbundle` CLI, `parse_bounded_metadata` | Fixture skill installed on temp roots; output names all three axes; no state-schema change | None |
| D2 | Capability difference rendering, the acceptance flag, and `upgrade --all` re-consent | `commands/upgrade.py`, `direct_install.py` | Fixtures: narrowing, equal, widening; widening refused without the flag and accepted with it; unknown history counts as widening | A clean security review by the repository owner. D2 does not depend on D1 |

## Assumptions / Risks

- **Riskiest assumption:** old capability values can be recovered from the installed projection. The parent intent's De-risk result (2026-11-05) confirmed the `boundaries` and credentialed axes, and `_read_projected_capability_axes` in `direct_install.py` already reads old values; D1's fixture re-proves it on installed temp roots.

## Ready gaps (Draft only)

None open.

## Decisions

- **2026-11-05, eugenelim:** adding the upgrade acceptance flag needs no RFC-0098 amendment. D2's spec names the flag and records it against D6.

## Rabbit holes

- Do not let an update consent to less than install does.

## Manual residue (named, non-blocking)

None.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

Follow-ons `direct-lifecycle-capability-inspection` and `direct-lifecycle-capability-reconsent` named in the shipped spec.
