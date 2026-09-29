# ADR-0129: Intent filename retirement uses a tombstone file at the vacated name, not a global retired list

- **Status:** Accepted
- **Date:** 2026-09-28
- **Areas:** governance, product-engineering
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0108 (identity for loop-contract items — D3's non-reuse rule and its rejection of a repository-global retired list are what this decision extends to intent filenames as a second artifact class)

## Decision summary

- **Decision:** When a rename operation retires an intent filename, it leaves a tombstone file at the vacated name. The tombstone's name is the retired name, preserving the `<TYPE>-NNNN-<slug>.md` structure and `.md` extension. ADR-0108 D3's non-reuse rule — previously scoped to loop-contract items — is extended here to intent filenames.
- **Because:** a global retired list is uncoordinatable across concurrent worktrees — the same reason ADR-0108's Context rejected one for criteria — and a tombstone file at the vacated name is self-enforcing: the allocator that scans the directory already sees it.
- **Applies to:** every intent filename retired through a rename operation in `docs/product/intents/`.
- **Tradeoff accepted:** a tombstone deleted by hand frees its ordinal with no detection — the same gap that exists for a live intent file deleted by hand.
- **Revisit if:** the directory-scanning allocator is replaced by a registry that can enforce the non-reuse constraint independently of the filesystem.

## Context

ADR-0108 D3 states that an identifier is never reused after removal, and that every removal is recorded in the artifact's retired list. That ADR scoped D3 to loop-contract items — acceptance criteria and verification items held in spec directories. Its Context rejected a repository-global identifier counter on the grounds that this repository has demonstrated it cannot coordinate a shared mutable resource across concurrent worktrees.

Intent filenames are a second artifact class with the same non-reuse requirement. A rename operation changes a filename's `<TYPE>-NNNN` prefix. The vacated ordinal must not be reissued to a later intent, or a citation written before the rename silently resolves to the wrong artifact.

The same worktree-coordination argument applies. A global list of retired intent filenames is a shared mutable resource; two concurrent sessions can write conflicting updates and neither sees the other's change. A file placed at the vacated name requires no coordination — it sits in the directory the allocator already scans.

ADR-0108's Context also rejects a per-directory retired list in a separate data file for the same reason, preferring instead that each retired item be recorded in the artifact that owns it. For intent filenames, the artifact at the vacated name is that record: a tombstone file whose presence is the reservation.

Six candidate tombstone-name shapes were measured on 2026-09-21 (recorded at `docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md` § "what the tombstone decision inherits from this slice"), each placed beside a live `CAP-0001` in a fixture directory and run through both `--dir/--token` and `--check`:

| Candidate name | `--dir/--token` | `--check` | Outcome |
| --- | --- | --- | --- |
| `CAP-0003-old-slug.md` | `CAP-0004`, exit 0 | exit 0 | correct — counted, ordinal reserved |
| `CAP-0003-old-slug.tombstone.md` | `CAP-0004`, exit 0 | exit 0 | correct — infix absorbed by `[^/]+` in the shape grammar |
| `tombstone-CAP-0003-old-slug.md` | `CAP-0002`, exit 0 | exit 0 | **silently reuses `CAP-0003`** |
| `CAP-0003-old-slug.tombstone` | `unparsed-name`, exit 1 | exit 1 | refuses the whole directory |
| `CAP-0003.tombstone.md` | `unparsed-name`, exit 1 | exit 1 | refuses the whole directory |
| `CAP-0003-old-slug.md.tombstone` | `unparsed-name`, exit 1 | exit 1 | refuses the whole directory |

Two shapes allocate correctly. One shape — a `tombstone-` prefix that moves the name outside the `<TYPE>-NNNN-<slug>` namespace — allocated `CAP-0002` with exit 0, leaving `CAP-0003` silently reissuable. Three shapes kept the `<TYPE>-NNNN` prefix but were invalid (no `.md` extension, or a structural alteration): each produced an `unparsed-name` scan failure that refused every subsequent admission in the directory.

The silent failure is the worse of the two: the refusing shapes fail at the moment of first use and draw attention; the prefixed shape succeeds, reports the wrong number, and violates ADR-0108 D3 with no diagnostic anywhere.

## Decision

A rename operation retires an intent filename by placing a tombstone file at the vacated name.

- **D1:** The tombstone file's name is the retired intent filename, unchanged: the `<TYPE>-NNNN-<slug>` structure and `.md` extension are preserved. The allocator's existing scan counts the file alongside live intents, and the ordinal stays out of circulation for as long as the tombstone stands.
- **D2:** The tombstone's preamble carries exactly three fields: `Slug:` (the same slug the retired artifact carried), `Tombstone:` (the UTC calendar date of the rename, written as one ISO 8601 calendar date `YYYY-MM-DD`), and exactly one of `Reissued as:` (a repository-relative path to the successor under `docs/product/intents/`) or `Retired:` (a single non-empty line describing the reason).
- **D3:** A file in `docs/product/intents/` is a tombstone if and only if its preamble carries a `Tombstone:` field. This partition rule routes every file in the directory to the live-intent contract or the tombstone contract; a corpus check enforces it.
- **D4:** No global list of retired intent filenames is maintained. The tombstone file at the vacated name is the entire reservation record — standing in for ADR-0108's per-directory retired list on this artifact class — and deleting it by hand frees the ordinal. That is corpus corruption of the same kind as deleting a live intent, and nothing in this convention detects either.

## Decision drivers

- **Worktree coordination.** ADR-0108's Context established that a repository-global shared resource cannot be coordinated across concurrent sessions. A file at the vacated name requires no coordination: its existence is the reservation.
- **Self-enforcing reservation.** The allocator scans `docs/product/intents/` for `<TYPE>-NNNN-<slug>.md` filenames. A tombstone at the retired name is picked up by the same scan with no extra case.
- **Visible-by-default failure mode.** A name that is in-namespace but structurally invalid causes a scan failure that refuses every subsequent admission. That is loud; the one shape that fails silently — a prefix outside the namespace — is why the tombstone must keep the original name rather than a transformed one.

## Consequences

**Positive:**

- The retired ordinal is reserved by the tombstone file's presence alone, with no auxiliary ledger or registry.
- The allocator's existing scan picks up tombstones without any code change; the reservation is enforced by the same logic that makes admission work.
- A corpus check that reads the directory can validate the partition rule directly.

**Negative:**

- Deleting a tombstone by hand frees its ordinal, and nothing in this convention detects that. The guarantee is "no ordinal is reused while its tombstone stands"; hand-deleting one is out-of-contract corpus corruption.
- The tombstone file is the sole reservation record. There is no defence-in-depth; if the file is lost, the reservation is lost with it.

**Residual:** a tombstone deleted by hand frees its ordinal again, and nothing detects that. `Agent Rules` in `docs/specs/intent-renumber-and-reissue/spec.md` forbids the reuse as a rule an agent follows, not a control that fails closed.

**Revisit if:** the directory-scanning allocator is replaced by a registry that can enforce the non-reuse constraint independently of the filesystem.

## Confirmation

- **Mode:** goal-based.
- **Signal:** `docs/specs/intent-renumber-and-reissue/spec.md` cites this ADR in its `Constrained by:` field, and this ADR's Status is `Accepted`. Checked by reading the files.
- **Owner:** eugenelim.

## Alternatives considered

- **A name outside the `<TYPE>-NNNN-<slug>` namespace (e.g., a `tombstone-` prefix).** Rejected first, because this is the worse failure: measured to allocate the wrong next ordinal with exit 0, silently freeing the retired ordinal. The violation of ADR-0108 D3's non-reuse rule produces no error and no diagnostic. One shape from the measurement, `tombstone-CAP-0003-old-slug.md`, produced `CAP-0002` as the next allocation while `CAP-0003` was left silently reissuable.
- **A name that keeps the `<TYPE>-NNNN` prefix but is invalid (e.g., drops `.md` or adds a suffix).** Rejected: measured to cause an `unparsed-name` scan failure for every subsequent admission in the directory. Three of the six tested shapes fell into this category: `CAP-0003-old-slug.tombstone`, `CAP-0003.tombstone.md`, and `CAP-0003-old-slug.md.tombstone`. One badly-named tombstone switches the feature off for every intent admitted after it in that directory. The failure is visible, but it makes the directory unusable until the bad name is removed.

## References

- `docs/specs/typed-intent-ordinal-allocator/notes/verification-ledger.md` § "what the tombstone decision inherits from this slice" — the six-candidate measurement this decision rests on.
- `docs/specs/intent-renumber-and-reissue/spec.md` — the delivery contract that implements D1 through D4.
