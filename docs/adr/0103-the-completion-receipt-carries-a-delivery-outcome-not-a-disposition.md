# ADR-0103: The completion receipt carries a delivery outcome, not an artifact disposition, and rides on the citing dependency edge

- **Status:** Accepted
- **Date:** 2026-09-02
- **Decision-makers:** eugenelim
- **Related:** [RFC-0096](../rfc/0096-portable-delivery-artifact-lifecycle.md) §6 and §7 (the receipt's four fields and its per-citation lifetime); [`close-work-extraction-and-immediate-disposition`](../specs/close-work-extraction-and-immediate-disposition/spec.md) AC17 (which shipped the producer this decision constrains); [`dependency-scoped-completion-receipts`](../specs/dependency-scoped-completion-receipts/spec.md) (the contract this decision governs)

## Decision summary

- **Decision:** the completion receipt's `outcome` is the closed vocabulary `completed`, `abandoned`, `superseded` — the *delivery's* result. It is not `post_closeout_result`, which is the *artifact's* disposition, and it is not free prose. The receipt's other three fields use the grammars `delivery-lifecycle-record.schema.json` already publishes, compared to that file at test time rather than restated. The receipt rides as an optional object on the citing local dependency edge in `workspace.toml`.
- **Because:** three distinct concepts are spelled with the word *outcome* in this codebase, and picking the wrong one silently converts "my dependency shipped" into "my dependency went away, and the tooling could not tell".
- **Applies to:** every completion receipt written by `close-work` and read by `workspace-status`.
- **Tradeoff accepted:** the receipt is a self-assertion. Once the artifact is pruned there is nothing left to verify it against, so its trust rests on `workspace.toml` being a reviewed, committed file — the same trust the workspace entry it replaces already carried.
- **Revisit if:** (1) a delivery result appears that none of the three values describes; (2) the lifecycle record gains an `outcome` field, making the receipt's value derivable rather than asserted; or (3) a receipt is found to have outlived every dependant that justified it.

## Context

RFC-0096 §7 states the mechanism: "Closeout removes the live entry and keeps
`{delivery_id, outcome, completion_event, evidence_ref}` only while a live
dependency cites it." Wave 6 deferred building it, recording that the receipt
"needs a schema answer this wave does not have" because the lifecycle record
carries no `outcome` field.

Measured on 2026-09-02, the gap is one field rather than a schema. Three of the
four are already published as `required` in
[`delivery-lifecycle-record.schema.json`](../../contracts/jsonschema/delivery-lifecycle-record.schema.json):
`delivery_id` (line 13), `completion_event` (line 19), and
`completion_evidence_ref` (line 20), which is RFC-0096's `evidence_ref`. The
producer is also already shipped: `plan_completion_receipt`
(`packs/core/.apm/skills/close-work/scripts/close_work.py:688`) builds the exact
four fields and refuses without a resolved surface.

## The three things called "outcome"

The word carries three different meanings in this codebase, each with its own
source and its own question:

| Spelling | Where | Values | The question it answers |
| --- | --- | --- | --- |
| `post_closeout_result` | `delivery-lifecycle-record.schema.json:18` | `Cooling`, `Retained`, `Retired`, `ExternalAdvisory` | What happened to the *artifact* after closeout? |
| `lifecycle_outcome` | `close_work.py:78`, gated at `:1025` | `completed`, `abandoned`, `superseded` | Did the *delivery* achieve its accepted outcome? |
| `outcome` (parameter) | `close_work.py:969`, gated at `:986` and `:1014` | `completed`, `abandoned`, `superseded` | Did the *delivery* achieve its accepted outcome? |
| `outcome` | `CompletionReceipt.outcome`, `close_work.py:348` | previously bounded text of at most 512 characters | undecided before this record |

The fourth row is the sharpest evidence for this record's existence:
`project_lifecycle` already takes a parameter *spelled* `outcome` that carries
the *delivery* meaning and the closed vocabulary — the same spelling as row 3
and the same semantics as row 2. The collision is already in the module.

A dependant reading a receipt is asking the delivery question. It needs to know
whether the thing it depends on landed. `post_closeout_result` cannot answer it:
a delivery that shipped and one that was abandoned can both be parked as
`Retained`, and both would read identically to every dependant.

## Decision detail

### `outcome` reuses the vocabulary already in the module

`lifecycle_outcome`'s three values are already the repository's answer to "did
this delivery land", already validated in the same file, and already the value
the shipped Wave 4 receipt fixture passes verbatim
(`test_pause_receipts_and_initiative.py:227` passes `outcome="completed"`).
Inventing a second vocabulary for the same question would create two answers.

The reuse is a reason for the *choice*, not a live coupling. The receipt's
vocabulary is owned by its own contract and stated once, in that spec's AC2;
`close_work.py`'s copies are not pinned to it by an equality read the way the
other three grammars are pinned to the lifecycle record. That asymmetry is
deliberate: the lifecycle record is a published, versioned contract document, so
an equality read against it is meaningful, whereas `lifecycle_outcome` is an
internal literal with no published home to read from. If the two ever need to
move together, the fix is to publish the vocabulary, not to add a fourth copy.

The alternative was bounded free prose, which `close-work`'s instructions
described before this record as "a short outcome statement". It was rejected
because a consumer cannot act on it: the satisfaction rule would have to treat
`outcome` as opaque, and a receipt written for abandoned work would satisfy a
dependant exactly as a delivered one does. That is the single failure the
receipt exists to prevent. `close-work`'s instructions are corrected to match.

### The other three fields are pinned by comparison, not by copying

Two independently versioned contract documents cannot share a JSON Schema
`$ref` without coupling their `contract_version` lines, so the receipt restates
the three grammars and a test reads the lifecycle record at run time and asserts
equality. The comparison value is therefore never written in prose — the
authoritative form stays the shipped schema.

`delivery_id` is pinned although RFC-0096's follow-on row named only the other
two. A receipt whose `delivery_id` cannot be joined to the lifecycle record's
`delivery_id` cannot be traced back to the closeout that wrote it — and after
pruning, that trace through git history or a surviving record is the only route
a human has to the evidence.

### The carrier is the citing edge

`close-work` forbids creating "a permanent initiative shell, shipped-spec list,
third room, receipt store, or lifecycle schema"
(`packs/core/.apm/skills/close-work/SKILL.md:203-204`). An optional object on the
citing dependency edge creates none of them, and gives the receipt exactly the
lifetime RFC-0096 §7 specifies: delete the last citing edge and the receipt is
gone with it.

The cross-repository `coordination_receipts` block is a different contract for a
different purpose — nine fields, in a fenced block in a local brief, for a
*remote* artifact that was never readable. This receipt is for a *local*
artifact that is gone, so no second file survives to hold it. The two are kept
apart by distinct finding codes: a malformed cross-repository receipt reports
`invalid_receipt`, and a malformed completion receipt reports
`invalid_completion_receipt`. That separation is load-bearing rather than
cosmetic — `status-projection-and-context-exclusion`'s ticked AC57 uses
`invalid_receipt`'s single-emitter property as a test oracle, and broadening the
code would have falsified a criterion in a frozen spec.

## Consequences

A dependant on abandoned or superseded work keeps refusing, which is the point.
Wave 7c can prune an artifact whose dependants still cite it, provided it also
removes the workspace entry — leaving the entry behind makes the dependency
refuse at `structurally_blocked_paths` before any receipt is read.

The receipt records no obligation of its own. Whether an artifact's workspace
entry was removed is not recorded anywhere today, so a later wave cannot yet
distinguish a correct prune from a file deleted with its entry orphaned. That
gap is recorded as a follow-on rather than closed here.
