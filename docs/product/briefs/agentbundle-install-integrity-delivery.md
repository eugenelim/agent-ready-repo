# Brief: install, uninstall, and upgrade keep installed-pack state intact

- **Slug:** `agentbundle-install-integrity-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as committed in `a96a878c4`, which an independent delivery-brief review returned `Clean` with no open Ready gap. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** [`agentbundle-install-integrity`](../intents/agentbundle-install-integrity.md)
- **Parent intent:** intent:agentbundle-install-integrity

## Outcome

`agentbundle install` refuses a pack that fails lint before it renders anything. Uninstall and upgrade never lose a concurrent state update. A required dependency is satisfied only by the catalogue it was installed from.

## Success metrics

- An install of a pack that `lint_pack` rejects writes nothing and exits non-zero.
- A multi-process test that runs install, uninstall, and upgrade together loses no state row, and no command writes state outside `persist_state_locked`, including the legacy dist-tree paths: the detection path in `commands/install.py` (`write_text(dump_state(...))`) and `commands/init_state.py` (`dump_state` then `write_jailed`).
- A dependency installed from catalogue A does not satisfy a requirement resolved against catalogue B.

## Scope / Non-goals

In scope: the three integrity gaps and the state migration the third needs.

Out of scope: the dependency scope qualifier (dropped 2026-11-05 for lack of a recorded adopter need; reopen when one is recorded), and any change to uninstall or upgrade behaviour beyond serialising the state write.

## Constraints / Appetite

Three small slices. Ship order: I2 first (it prevents data loss), then I1, then I3 (which needs I2). Baseline checked 2026-11-05 in `packages/agentbundle/agentbundle`: `statelock.persist_state_locked` is called only from `commands/install.py` and `direct_install.py`; the uninstall command's state-write function and `_apply_single_row` in `commands/upgrade.py` serialise with `dump_state` directly; `commands/install.py` has no `lint_pack` call before `render_pack(`; `validate_dependencies_required` builds a `dict[str, str]` of name to version. Each change is protected and its commit needs an `Engine-Change-RFC:` trailer naming the RFC that governs that command (earlier engine commits cite RFC-0008, RFC-0098, or RFC-0040, or `n/a` for behaviour-neutral work).

## Proposed slices

| # | Slice | Primary owning surface | Verification | Gating |
| --- | --- | --- | --- | --- |
| I1 | Gate install-path `render_pack` with `lint_pack`; refuse before any write | `commands/install.py` | Fixture packs with a symlink and a poisonous name: nothing written, exit non-zero | None |
| I2 | Fresh-state mutate closures for uninstall and upgrade, and the two legacy dist-tree state writes (in install and in `init_state`), through `persist_state_locked` | `commands/uninstall.py`, `commands/upgrade.py`, `commands/install.py`, `commands/init_state.py` | Multi-process test: concurrent install, uninstall, upgrade keep every row | None |
| I3 | Persist catalogue identity per installed pack, migrate old state, require identity plus name plus range | `commands/install.py`, state schema | State migration fixture; two-catalogue fixture refused | After I2, because both write state |

## Assumptions / Risks

- **Riskiest assumption:** old state files carry no catalogue identity. Owner decision, 2026-11-05: strict. A row with no catalogue identity does not satisfy a catalogue-qualified dependency, and the install stops, naming the dependency and telling the adopter to reinstall that pack, which writes the catalogue record. A pre-migration state file still loads, and the migration fixture proves both.

## Ready gaps (Draft only)

None.

## Rabbit holes

- Do not widen I2 into a state-format redesign.

## Manual residue (named, non-blocking)

None.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

Four items absorbed by the intent: dependency provenance, scope qualifier, state-lock gap, and the pre-render lint gate.
