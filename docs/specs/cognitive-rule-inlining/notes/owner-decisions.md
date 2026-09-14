# Owner decisions

Decisions the task owner made during execution that an artifact has to cite. A
conversation is not a reference; this file is.

## 2026-09-13 — the engine path-gate exemption carrier

**Decision: the approved spec carries the exemption. No RFC is required.**

`make build-check` failed at `lint-catalogue-curation-guard`: the changeset
touches `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, and
RFC-0059 D6 requires an engine-scoped RFC for a change under that tree. No RFC
governs this change.

The owner accepted the approved spec as the carrier, on the grounds that it
contracts the lint relaxation in ACs 8-10 and names the trust-boundary widening
in its Risks. ADR-0056 is the precedent: it names itself the exemption carrier
for its own landing PR, establishing that an approved artifact can stand in for
an RFC.

`n/a` was rejected as false. Engine behaviour does change: the lint's
accept/reject surface moves, and so does the selection between the confined
64 KiB read and a plain `read_text`.

Carried by the trailer on the empty commit `69e050224`.

## 2026-09-13 — the sweep criterion's exemption list

**Decision: add `docs/product/changelog.md` to the list.**

The criterion requires `rg --hidden -l 'agents/rules/cognitive-load'` to return
no hit outside a named set. Running it returns ten files; nine are exempt. The
tenth is `docs/product/changelog.md` — and the changelog criterion in the same
spec *requires* the Upgrading section to name the retired path, so an adopter
knows what to delete by hand. The contract forbade a hit it also mandated.

Two corrections ride along in the same criterion, both owner-approved:

- "these **four** bounded out of scope" precedes a list of five.
- A duplicated sentence: "This criterion is closed by running the command; it
  has been wrong three times when read. The criterion is closed by running the
  command, not by reading it." One point, said twice, which this repository's
  own prose rules forbid.

This is the `reason_ref` for the contract amendment that carries the edit.

## 2026-09-13 — the post-amendment gates

**Decision: proceed. The amendment's two human gates are answered by the
approval that authorized it.**

The contract amendment returned the engine to the spec/plan phase, which carries
two human gates: "Does this spec define the right thing to build?" and "Does this
plan describe the right way to build it?" Both were answered in advance. The
owner approved the criterion correction, and the plan was not touched by the
amendment — its hash is unchanged at `09965cec2bab`, and the completed task
sections are pinned against edits.

The amendment changed one acceptance criterion's exemption list. It changed no
objective, no boundary, no task, and no testing strategy.
