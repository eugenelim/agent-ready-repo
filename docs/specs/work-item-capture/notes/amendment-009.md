# Amendment 009 — the close can obtain a correlation key

**Authorised by:** eugenelim, 2026-09-21
**Tier:** contract — adds one criterion and one CLI mode.
**Against:** approved_spec_hash 2c590916

## The defect this closes

**No reachable procedure can write a `work-item`.** The CLI requires
`--reasoning-verdict` and `--reasoning-correlation-key` together for a
`work-item`, and the correlation key is a SHA-256 over the canonical dispatch
payload including `declined_ordinal`. Grepping every `.md` in the repository
for `reasoning-verdict`, `reasoning-correlation-key` or `correlation_key`
returns nothing: both `packs/core/.apm/skills/work-loop/references/work-item-capture.md`
and `docs/guides/reference/work-item-capture.md` describe the branch in prose
and name neither the flags nor how to compute the key.

So an agent following the shipped reference submits without a verdict and
every capture refuses. The feature ships with a verified refusal path and no
verified admission path outside the test suite.

Computing the key by hand is not a workaround. It is a SHA-256 over
`_canonical_json_bytes` of a payload whose field set is closed by
`reasoning_dispatch_parameter_bins` and whose serialisation the agent cannot
reproduce reliably. The key exists to bind a verdict to an item; a key the
caller cannot obtain binds nothing because no caller can get that far.

## What changes

One new read-only CLI mode, `--reasoning-payload`, and one criterion.

`--reasoning-payload` reads a capture request on stdin exactly as `--capture`
does, and for a `work-item`:

1. runs `enforce_declined_set_cap` against `--declined-ordinal`,
2. validates the request, so a malformed item is refused here rather than
   after a wasted dispatch,
3. runs `refuse_instruction_shaped_work_item`, so instruction-shaped content
   never reaches the cold context — this is the ordering § D3 requires,
4. builds the payload, and
5. prints the rendered dispatch message and its correlation key.

It **writes nothing**. It is the only way a caller obtains a correlation key,
and obtaining one is not a verdict: the caller still has to run the cold check
and still has to hand the writer a verdict that matches.

## What does not change

**The residual `AC-0069` records.** The verdict still reaches the writer
through the party that produced it. `--reasoning-payload` hands the caller the
key for an item, which the caller could already have computed in principle;
it does not establish that the caller then consulted the tier. The write-time
floor is unchanged and the security gap list needs no new entry, because this
mode makes an existing disclosed residual *reachable* rather than wider.

**The close remains agent-driven.** The spec's Testing Strategy pins
`AC-0001`, `AC-0002` and `AC-0014` to *Visual / manual QA, the real close*.
This amendment does not add a `--close` mode that would drive the whole
declined set, because that needs a dispatch subprocess — a trust boundary this
spec has not specified — and would contradict that row.

## What stays unreachable, and why that is now disclosed rather than hidden

Four surfaces still have no production caller after this amendment:
`dispatch_reasoning_check`, `CloseLedger`, `render_close_output` and
`refuse_instruction_shaped_work_item`. The first three are the agent-side
half of the close: the agent runs the dispatch and accounts for its own
declined set, and a Python callable cannot be driven by skill prose, so
these are library surface for a close driver this delivery does not ship.

The fourth is different and worth stating plainly. Building this mode
surfaced that `refuse_instruction_shaped_work_item` is **fully subsumed** by
`_deterministic_privacy_scan`: measured across all three shapes and all six
`WORK_ITEM_SCANNED_FREE_TEXT_FIELDS`, the general scan already refuses every
input the dedicated gate refuses. `AC-0035`'s outcome holds — nothing
instruction-shaped reaches the cold context, and a test drives all
shape-field pairs through the CLI to show it — but it holds by the general
scan, not by the dedicated function. This mode therefore does **not** call
that function: doing so would ship a control that cannot fail.

Both gaps go in the spec's Durable Outputs security row, rather than being
left to be rediscovered by the next reviewer.

## New criterion

`AC-0070` — a caller can obtain the correlation key for a declined item
without computing it, and doing so writes nothing.
