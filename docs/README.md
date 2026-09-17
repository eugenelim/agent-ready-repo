# docs/

What belongs where in this repository's documentation, and which parts must
match current reality.

Read this before adding a document. Putting a fact in the wrong layer is the
most common source of documentation rot: a decision recorded as current state
goes stale, and current state recorded as a decision never gets updated.

## The map

| Area | What belongs there | Lifecycle |
| --- | --- | --- |
| `architecture/` | How the code is organized today — the map you read to find things, and the golden path new work conforms to | living |
| `product/` | What the product is doing today: direction, release history, and the briefs behind in-flight work | living |
| `specs/` | The engineering contract for one feature, with its implementation plan | living while building, frozen once shipped |
| `knowledge/` | Practitioner residue — patterns, gotchas and antipatterns scoped to a file glob | living |
| `adr/` | Why we chose X over Y, one record per decision | frozen, save a small metadata block ([RFC-0102](rfc/0102-mechanically-checkable-adrs.md) § 4) it keeps writable |
| `rfc/` | Should we change this? Open until accepted, rejected or withdrawn | governance |
| `guides/` | How users use what we ship, in Diátaxis quadrants | living |

`adr/` and `rfc/` arrive with the `governance-extras` pack, which seeds a
generated index for each. The `core` pack installs the first four rows only.

### Two architecture documents, two jobs

`architecture/overview.md` is **descriptive** — the map of how the code is
organized today, read to find things. `architecture/reference.md` is
**normative** — the golden path (stack, building blocks, cross-cutting
standards) that new work conforms to. A thin repository has only the map; the
golden path appears once there are real architecture decisions to hold work to.

Getting these the wrong way round is the common mistake: a map written as a
standard goes stale the moment the code moves, and a standard written as a map
never gets enforced.

## The three lifecycle classes

Every document belongs to exactly one, and the maintenance rule differs:

- **living** — must match current reality, and is updated in the same change as
  anything that affects it. Drift is a bug, not debt.
- **frozen** — the prose is immutable once delivered: never rewritten to
  reflect a later change, only superseded by a new record that cites it. This
  names the whole record's lifecycle stage, not a per-field zone a record kind
  may define for itself under the same word — an ADR's own mutability zones,
  for example, include one it also calls "Frozen," narrower in scope than this
  class.
- **governance** — an in-flight proposal, open until it is accepted, rejected or
  withdrawn. It describes what someone wants, not what is.

A shipped spec moves from living to frozen. That transition is the one that
catches people out: once shipped, correct it by superseding it, not by editing
the body.

## The living layer

`docs/architecture/`, `docs/product/` and `guides/` are the living layer. They
describe what *is*, not what was decided or what is proposed, and each serves a
different audience: architecture for contributors, product for maintainers,
guides for users.

Governance and frozen records sit outside that layer. If a pack seeds
`docs/adr/` or `docs/rfc/`, they arrive with their own README.
