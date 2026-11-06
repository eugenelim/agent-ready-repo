# Fix seed upgrades

- **Status:** Open
- **Kind:** defect

## Summary

`agentbundle upgrade` neither refreshes nor adds seeded files, while the published guides say it does. Owner: `eugenelim`.

## Observed

- `agentbundle install` writes a pack's seed files once. `agentbundle upgrade` leaves an unedited seed at its old version, writes no `.upstream` companion for an edited seed, and adds no seed the pack gained later. Skill files get all three behaviors.
- `agentbundle upgrade --seed <path>` fails with `primitive '<path>' not in pack`, because the primitive filter reads the rendered projection, which holds no seeds.
- State keeps the seed at the install version after an upgrade.
- The upgrade output counts edited seeds in its "local edits" line and then does nothing for them.
- `guides/_shared/explanation/file-safety-contract.md` says seeds are replaced on upgrade when the on-disk content matches what the catalogue last wrote. `guides/_shared/reference/agentbundle.md` documents `--seed <path>` as a selective upgrade.
- Code: `deliver_seeds` in `packages/agentbundle/agentbundle/commands/_common.py` is called only by `install` and `scaffold`. `commands/upgrade.py` never reads the seed checksums that `install.py` records.
- Workaround today: `agentbundle scaffold` adds absent seeds. It writes a companion for every differing file and does not update state.

## Intended

- `upgrade` applies the skill rule to seeds: overwrite an unedited seed, write a companion for an edited one, add a seed never recorded in state.
- A seed the adopter deleted on purpose (recorded in state, missing on disk) stays deleted.
- A self-hosting repository's own seed paths, which the drift check already skips, are skipped by upgrade too.
- `--seed <path>` works, and the upgrade output lists the companions it wrote.
- The change ships with an `agentbundle` version bump, a changelog fragment and a test for each case above. Until then, release notes for packs that add seeds say they reach new installs only.
