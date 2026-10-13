# Owner decisions — 2026-10-13

The owner asked to build Slice 3 and took three decisions during the code-mode
amendment of this spec and plan. None of them approves the amended pair; both
human gates run again after pre-execute review.

## Build the slice

The owner asked for T1-T4 to be built. Terminal Intent moves from `spec-plan`
to `code` through the controlled amendment path, with fresh review and fresh
approval of both artifacts, as Slice 1 did.

## Changelog destination

Main now authors the product changelog as fragments created with
`tools/changelog.py new` under `docs/product/changelog.d/`. Asked whether to
amend only Terminal Intent or also the destination, the owner chose "Also amend
the destination". The Release history durable output and T4 name a changelog
fragment instead of `docs/product/changelog.md`.

## Read-only quarantine and the store-wide write stop

Round 3 of review showed that AC-0005 let all of distillation exclude invalid
records, while promotion, terminal disposition, map rebuild, writer admission,
and migration must keep refusing so that no write runs against a reduced view.
The owner chose "Approve both":

- AC-0005 limits per-record exclusion to the read-only paths, enquiry through
  `--enquire` and the distillation pending page through `--distill --pending`,
  and requires every write, disposition, promotion, map-rebuild,
  writer-admission, and migration path to refuse the whole operation and
  change no byte when any record it reads is invalid.
- The spec's Accepted Risk gains the store-wide write stop that this keeps.

The risk text shown to the owner said an invalid observation record blocks
captures into its partition. The recorded text adds that an invalid committed
topic or topic-map entry blocks every capture through writer admission
(`_assert_v1_writer_allowed`), which is today's behavior. The owner confirms
that wording at re-approval.

The rejected option was making writers tolerate invalid records, which would
change storage and admission behavior that the spec puts under Ask first.
