# Spec: Intent renumber, reissue, and the tombstone

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Constrained by:** ADR-0108

## Objective

Make an ordinal safe to change. A renumber is not free: `workspace.toml` holds the registry `path` entries and a stale one raises `missing_artifact`, which `tests/roster/test_workspace_status_projection.py` treats as fail-closed. The owner accepted the renumber cost, so the constraint is on completeness of the sweep rather than its frequency.

A post-admission altitude change reissues at the new prefix and leaves a tombstone, which keeps `max + 1` correct without a shared retired list, per ADR-0108 D3's non-reuse rule.

## The tombstone contract

**Owner decision, 2026-09-21. Owner: eugenelim.** This discharges the decision
this spec owed. It settles the five parts of that question: how a tombstone is
identified, how it is excluded from intent-shape validation, whether resolution
follows it, what happens when its target is missing, and what happens when two
tombstones point at each other.

**T1 — A tombstone keeps the retired artifact's exact filename, with no marker
in the name.** The retired name is already `<TYPE>-NNNN-<slug>.md`, which
`classify()` reads as `valid`
(`packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py:145`), so the
allocator counts the retired ordinal exactly as it did before the rename and
`max + 1` never returns it. Six candidate names were measured on 2026-09-21 and
only two are safe
(`docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md`,
`## 2026-09-21 — what the tombstone decision inherits from this slice`). This
decision takes the one that also preserves inbound links: a tombstone standing
at the original path turns a citation the sweep could not reach into a working
forwarding pointer instead of a broken link.

**T2 — A tombstone is identified by a `Tombstone:` preamble field, and by
nothing else.** Presence of the field is the whole test. It is a new field
rather than a `Status:` value because the `Status` vocabulary is an owed
decision of `docs/specs/intent-metadata-shape-contract/spec.md`, and because a
tombstone must be identifiable without first parsing as a well-formed intent.

A tombstone carries exactly three things and no others:

- `Slug:` — the retired artifact's canonical slug, unchanged, so identity still
  binds to the field rather than to the filename.
- `Tombstone:` — the ISO date the artifact was retired.
- Exactly one of `Reissued as:` — a repository-relative path to the live
  successor — or `Retired:` — a reason, for a retirement with no successor.
  Both fields present, or neither, is a failure.

**T3 — Exclusion routes to a second contract; it never skips validation.** The
corpus lint partitions the directory on the presence of `Tombstone:`. A file
carrying it is validated against the three-field contract above. A file without
it is validated against the intent contract. No file in the directory is left
unvalidated, so the field cannot be used to escape a shape a file would
otherwise fail.

**T4 — A tombstone forwards a reader and refuses a resolver.** A person
following a stale link lands on it and reads the pointer. No mechanical
consumer dereferences it: the allocator counts the name and never opens the
file, and a live pointer found at a tombstone — a `Parent intent:` target, a
registry `path` — is reported as a stale citation rather than silently resolved
to the successor. Resolving through it would hide the staleness the first
acceptance criterion requires be zero.

**T5 — A `Reissued as:` target must be a live intent.** It must exist and must
not itself carry `Tombstone:`. That makes a chain unrepresentable rather than
detectable: one check refuses a self-pointer, a mutual pair, and a chain of any
length, with no traversal and no visited set. Renumbering an artifact a second
time therefore re-points its existing inbound tombstones at the final target
inside the same transaction instead of stacking a second tombstone behind the
first.

**T6 — A dangling tombstone is fail-closed.** A `Reissued as:` target that does
not exist exits non-zero and names both the tombstone and the missing path. A
half-landed rename is the failure the lockstep criterion exists to prevent, and
this is the posture `workspace.toml`'s `missing_artifact` already takes in
`tests/roster/test_workspace_status_projection.py`. A `Retired:` tombstone has
no target and is never dangling.

**Where T3 lands.** The corpus lint is `intent-metadata-shape-contract`'s to
build and that spec is Draft, so this slice either follows it or ships the
partition as part of its own sweep check. The sequencing is a plan question,
not a contract question: the partition rule above holds wherever it is
implemented.

## Testing Strategy

- Renumber one real intent end to end; assert zero stale path-shaped citations and unchanged pointer values.
- Assert the allocator counts a tombstone at the retired name and never returns that ordinal, and assert the four unsafe candidate names stay unsafe.
- Walk the two-contract partition over a corpus holding a conforming intent, a conforming tombstone, and a file carrying `Tombstone:` plus fields the tombstone contract forbids; assert each is validated against exactly one contract and none is skipped.
- Assert a `Reissued as:` target that is absent, and one that is itself a tombstone, each fail and name both paths.
- Assert a live pointer resolving to a tombstone is reported as a stale citation rather than followed.

## Acceptance Criteria

- [ ] A renumber leaves zero stale path-shaped citations — registry `path` entries and Markdown link targets — and changes no canonical pointer value, because identity binds to each artifact's `Slug:` field.
- [ ] A renumber edits `workspace.toml` in lockstep with the rename, and the sweep is complete rather than best-effort.
- [ ] A retirement or altitude change leaves a tombstone at the retired filename that the allocator counts, so an ordinal is never reused.
- [ ] Every file in the intent directory is validated against exactly one of two contracts, selected on the presence of `Tombstone:`, and a file carrying that field is refused for any content the tombstone contract does not admit.
- [ ] A `Reissued as:` target that is absent, or that is itself a tombstone, fails and names both the tombstone and the target.
- [ ] A live pointer whose target is a tombstone is reported as a stale citation and is never resolved through it.
- [ ] A renumber re-points every inbound tombstone at the final target in the same transaction, so no tombstone ever points at another.
