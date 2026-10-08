# navigate-intents test fixtures

## Schema for expected-outstanding.json

Every corpus directory carries an `expected-outstanding.json` file:

```json
{"outstanding": ["<node-id>", ...]}
```

- **`outstanding`**: sorted list of node ids for every non-terminal artifact in
  the corpus. Node ids follow AC-0004 and AC-0062:
  - Intents: `capability:<slug>`, `outcome:<slug>`, `opportunity:<slug>`, or `intent:<slug>`
  - Briefs: `brief:<slug>`
  - Specs: `spec:<dir>`

Terminal statuses by kind (AC-0058, AC-0067):
- **Intents**: Fulfilled, Withdrawn, Cancelled, Superseded (leading word)
- **Briefs**: Shipped, Cancelled (leading word)
- **Specs**: Shipped, Archived (leading word)

Tombstones are never nodes and never appear in the outstanding list.
The seeded brief template (`_template.md`) is never a node.

For corpora where AC-0009 (malformed_record, duplicate_identity) or AC-0042
would cause the whole operation to fail, `expected-outstanding.json` still exists
but contains `{"outstanding": []}`. The outstanding test skips comparison for
those corpora (AC-0058).

## Corpus layout

```
fixtures/
├── README.md              (this file)
├── mixed/                 (positive corpus covering all admitted preamble shapes)
│   ├── docs/product/intents/
│   ├── docs/product/briefs/
│   ├── docs/specs/
│   └── expected-outstanding.json
└── negative/              (one corpus per refused-edge state and integrity code)
    ├── dangling/          AC-0007: Parent intent: names no live intent
    ├── retired_target/    AC-0007: Parent intent: names a tombstone
    ├── kind_mismatch/     AC-0007: typed ref slug names intent with different node id
    ├── out_of_type/       AC-0007: path/ref names wrong artifact type
    ├── multiple_values/   AC-0007: same pointer field appears twice with different values
    ├── cycle/             AC-0007: cycle (self-parent + 2-member cycle)
    ├── unparseable/       AC-0007: absolute path, .. segment, backslash
    ├── malformed_record_utf8/     AC-0009: invalid UTF-8 (whole op fails)
    ├── malformed_record_bad_slug/ AC-0009: missing/bad Slug (whole op fails)
    ├── duplicate_identity/        AC-0009: two nodes share an identity (whole op fails)
    ├── brief_parent_malformed/    AC-0064: brief Parent intent: malformed (no kind: prefix)
    ├── brief_parent_unsafe/       AC-0064: brief Parent intent: unsafe (absolute path)
    ├── brief_parent_ambiguous/    AC-0064: brief Parent intent: two distinct slugs → multiple_values
    ├── brief_parent_repair/       AC-0064: one accepted + malformed values → repair case
    ├── brief_parent_unrecognized/ AC-0071: value matching no recognized shape
    ├── no_decomposed/     AC-0064 no-relation: feature intent with no Decomposed:
    ├── spec_route/        AC-0064 no-relation: feature intent with spec route
    └── two_briefs/        AC-0064 no-relation: feature intent named by two briefs
```

Non-committed cases (built at test time in tmp_path by `navigate_intents_fixture_builders.py`):
- AC-0042: symlinked file, file under symlinked directory, FIFO, file with two hard links,
  file swapped between validation and open
- AC-0009: intent over 1,000,000 bytes (input_too_large), unsafe_input
