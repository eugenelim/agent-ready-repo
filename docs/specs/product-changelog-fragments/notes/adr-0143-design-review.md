# ADR-0143 design review

ADR-0143 passed a four-round design review on 2026-10-03, before any code.
In the final round:

- the security review returned `Clean — ready to commit.`;
- the architecture review returned `SHIP IT`;
- the adversarial review's last three points were folded in.

Three independent, read-only reviewers checked the drafts against ADR-0123,
`docs/architecture/changelog-fragment-source.md`, this spec and plan,
`tools/changelog.py` and pass 5 of the build-cost report:

- an adversarial reviewer;
- an architecture reviewer;
- a security reviewer, in spec-stage secure-design mode.

Each later round re-read the revised drafts against its own earlier findings.

## What changed the design

These findings changed the decision itself, not only its wording.

| Round | Lens | Finding | Resolution |
| --- | --- | --- | --- |
| 1 | All three | The draft dismissed reader optimization, yet the file-safety helper reloads once per fragment, and T16's profile had measured removing it | Spike 3 measured a 3.07 s paired saving. Loading the helper once moved into T16 (AC-B1), and bundles are recorded as the owner's headroom choice |
| 1 | Security, adversarial | Path-based merge-base checks miss deletions, rename pairings and empty directories | Identity is compared by `id` over both forms, from merge-base tree listings, without rename pairing (D6) |
| 1 | Security | A compaction diff is too large to review, so a moved record could carry hidden edits | Bundled records must equal their merge-base bytes, read as raw bytes (D6, AC-B5) |
| 1 | Adversarial | ADR-0123 D2, D4 and D6, the spec's never-track rule, and the § 2, § 6, § 7 and § 8 rows all change | Supersedes ADR-0123 D2, D4 and D6 in part, with one sentence per clause. The spec and architecture rows are amended |
| 2 | Architecture | The bar is a ratio, and the monolith grows too, so the helper fix alone tends toward 8.6–10.2% rather than growing without bound | Context states the arithmetic and records bundles as a judgement, not a § 7 requirement |
| 2 | Architecture | Append-only parts remove month rewrites and cross-part order checks | Parts are append-only (D5) |
| 2 | Architecture | A part-writing change could drop a record | A part-adding change may not drop an unbundled merge-base fragment (D6) |
| 2 | Adversarial | The release gate ran nowhere, and byte immutability left no way to remove a leaked secret | The ceiling moved into `tools/build-site.py` (D9). A listed retraction path was added (D7) |
| 3 | Adversarial | T18's arm at 2,115 loose would exceed the 2,000 ceiling the build enforces | Spike 4 measured cost by loose count. The ceiling is 1,000, and T18 measures exactly 1,000 loose |
| 3 | Architecture | Nothing measured the mixed state the policy produces | Spike 4: 2.79 s at 1,000 loose and 1.46 s at 300, against 5.42 s fully loose |
| 3 | Security | The retraction list could be edited to re-publish, its free text could leak or inject, and rollback could lose records | The list is append-only, with fixed categories and no free text. Parts are never rolled back once deletion starts, and a rerun completes the move (D7, D8) |
| 4 | Adversarial | Pending fragments sit outside the ceiling | The § 7 arm is the worst case for released records only, and pending fragments get a 250 warning |

## Container and bounds hardening

These rounds also fixed rules at parser depth:

- the exact separator line, matched as a whole line on raw bytes;
- LF-only, LF-terminated UTF-8 with no byte-order mark;
- the separator banned in front matter as well as the body;
- part names that fullmatch `YYYY-MM-NN.bundle`, checked before any Git path
  parsing;
- each record's month matching its part's;
- a 65,536-record cap across both forms;
- a size check before any read of a merge-base blob or the retraction list;
- "changed" decided by object id over loaded bytes, never by the Git index;
- the single reader, which no consumer may call with a substitute enumerator,
  helper handle or Git runner;
- exclusive-create and atomic-replace writes for `compact` and `retract`.

## Left for implementation review

The final round named these as outside a design review:

- whether an interrupted compaction's rerun recovers cleanly, though its
  intermediate state already fails closed as a duplicate `id`;
- how the reader computes object ids in a SHA-256 repository, where a mismatch
  costs only extra reads;
- whether the repository's security workflow covers credential rotation and
  history purge after a retraction;
- free-form Markdown reaching HTML, which today's fragment path already allows
  and this design leaves unchanged.
