# The mechanical reading of "must not load its contents"

RFC-0096 §7 binds Wave 6: "Cooling stays outside ordinary orientation and is
retrieved only for explicit history, regression investigation, or retirement
review; status and default orientation must not load its contents."

A projection that reads every record to count the due ones has loaded
something. This note fixes *what* it may not load, before any acceptance
criterion is written, because every exclusion criterion in the spec depends on
the answer.

## The record is not the contents

"Its contents" means the body of the **cooled delivery artifact** — the
`spec.md` and `plan.md` at the record's `locator` and `aliases`. It does not
mean the lifecycle record.

Three pieces of authority decide this, and they agree:

1. **RFC §6 designs the record to be read.** It enumerates the record's fields
   and states that the record "excludes requirements, personal identities, and
   rationale". A structure whose defining property is that it carries no
   requirements and no rationale is metadata about content, not content. A rule
   forbidding status from loading it would make §6's field list unreachable by
   the only surface RFC §7 names as its reader.
2. **RFC §7 names status as the signal.** §6 says "Status or an external system
   signals due state". Status cannot signal due state without resolving
   dueness, and `review_on` lives in the record. The two sentences are only
   consistent if the record is readable and the artifact is not.
3. **Wave 4 said which thing is visible.** Wave 4's AC18
   (`docs/specs/close-work-extraction-and-immediate-disposition/spec.md:470`)
   reads "Cooling context remains visible to current readers because Wave 6
   context exclusion is absent." At Wave 4 there were no lifecycle records at
   all — `docs/lifecycle/` holds only `README.md`. The thing visible to current
   readers was the cooled spec, surfaced by the ordinary spec scan. That is the
   visibility Wave 6 removes.

## What the engine may and may not touch

| Surface | Ordinary orientation | Why |
| --- | --- | --- |
| `docs/lifecycle/<delivery_id>.json` | **May read**, through Wave 5's bounded reader | The pointer layer. `cooling.load_record` already caps it at `MAX_RECORD_BYTES` (64 KiB) and `MAX_RECORD_DEPTH` (8). |
| `docs/specs/<slug>/spec.md` at a cooled locator | **Must not open** | The contents. |
| `docs/specs/<slug>/plan.md` at a cooled locator | **Must not open** | The contents. |

The bound on the permitted read is not new work: Wave 5 already owns it, so
"bounded read" is a reuse, not a mechanism this wave invents.

## Why not filenames, and why not an index

A filename-only count was rejected on evidence, not taste. Records are named
`<delivery_id>.json` (`docs/lifecycle/README.md:4`); the name carries no date,
so dueness is not derivable from it. Counting due reviews from filenames would
require encoding `review_on` into the filename — a second persistent
representation of a field the schema already pins, and a change to the record
destination Wave 5 owns.

A cached index was rejected for the same reason plus one more: it is a new
store, which the accepted cut list forbids and which would need its own
invalidation rule.

## The observable this produces

Two independent observables, both falsifiable, neither asserting a property of
the code's character:

1. **Byte.** A sentinel string that exists only inside a cooled artifact's body
   never appears in the emitted JSON.
2. **Count.** `scan.global_scan_spec_files_read` and
   `scan.declared_spec_files_read` each fall by exactly one per excluded
   artifact, measured against the identical fixture with the record removed.

The counter is not new instrumentation. `workspace_status_engine.py:488-489`
already exposes `files_read` over `declared_spec_files_read +
global_scan_files_read`, and `_run_type1_scan` increments it at `:3465`
immediately before `extract_spec_status(spec_file)` — the exact read being
suppressed.

## Retrieval stays explicit — by doing nothing

RFC §7 permits retrieval "for explicit history, regression investigation, or
retirement review". `close-work` already owns all three: Wave 5 shipped
`cooling.load_record` and `cooling.review`. Wave 6 adds no retrieval verb, no
`--show-cooling` flag, and no detail subcommand. Explicitness is preserved by
the default path not loading the artifact, and the existing explicit path
continuing to work unchanged.
