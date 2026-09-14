# Show an initiative's name and milestone at orientation

- **Status:** Draft
- **Level:** feature

## Outcome

A session running `workspace-status` can tell which initiative is which.
Orientation reads `ini-002 — Platform Core (milestone: P5 · Adopt (M1-M5
shipped))` rather than a bare slug. The values already sit in `workspace.toml`
and are withheld by a redaction whose motivating threat the repository has
since placed out of scope.

## Boundary

- Admits the two fields `initiatives[].name` and `initiatives[].milestone`,
  the emitter that replaces them with the redaction sentinel, and the
  `workspace-status` skill contract that describes them.
- Admits deciding whether any bound applies on the way out, and whether the
  sentinel survives as the degraded result for a value that fails it.
- Admits the two tests that currently pin the redaction. Both invert under
  this outcome, so changing them is in scope; weakening any other assertion in
  those files is not.
- Excludes the backlog projection's `summary` and `needs`. That pass-through
  is deliberate and is now recorded in the code.
- Excludes any change to the `workspace.toml` schema. This changes what the
  projection emits, not what an author may write.
- Determinism is a property of this tool. Same input, same output, before and
  after.

## Owner

eugenelim

## Unresolved questions

- Does any bound apply at all, or do these values pass through as written, as
  `summary` and `needs` already do? Consistency with the backlog decision
  argues for no bound; a length cap may still be wanted to stop one long
  milestone string from dominating the orientation output.
- Two tests pin the current behaviour: one feeds a hostile payload, one feeds
  this repository's real values. Both invert. Does the contract keep a case
  asserting something about these fields afterwards, and what would it assert?
- Does the skill contract return to what it said before the redaction, or to
  something new? The rendering template and the key list were rewritten to
  describe the sentinel and would both change again.
- Is a partial restore worth considering — `name` without `milestone`? `name`
  is short and slug-like in practice; `milestone` is the long free-text field
  and the one that would dominate the line.

## Projection

- A spec under `docs/specs/`, carrying a `security-reviewer` pass because the
  change reverses a control rather than adding one.
- A core pack version bump and a changelog entry, because it changes what an
  adopter's agent prints at session start.
- No RFC. This applies a threat-model decision the repository has already
  made; it proposes no new convention.

## Opportunity

The redaction was added by the pass that bounded every public value in this
projection, at a time when display prose from `workspace.toml` was treated as
untrusted input. The skill contract was corrected separately to stop promising
values the projection never emits, which removed the visible defect: a session
no longer prints `ini-002 — workspace.toml (milestone: workspace.toml)`.

What remains is the cost without the benefit. The owner has since settled that
`workspace.toml` is working material for developers in the same repository,
carrying the same threat profile as the source code beside it. Under that
model the redaction guards nothing, and the same reasoning has already been
applied to the sibling backlog projection, which passes its display prose
through as written.

The adopter question that would otherwise gate this is settled rather than
open: `workspace.toml` lives inside the repository it describes, so anyone who
can reach it already has access to that repository's source, on every install
route.

Measured on this repository: four active initiatives, so orientation lists
four bare slugs. Every one of them has a name and a milestone in
`workspace.toml` that the reader cannot see. Orientation is the first thing a
session reads, and naming the initiative is most of what that section is for.

## Assumptions

The riskiest assumption was that the trust model holds for every repository
that installs this pack, not only for this one, because the redaction ships to
adopters and safety here looked like a property of this repository rather than
something the pack can check.

The owner has settled it, and the argument does not depend on any install
route. `workspace.toml` lives inside the repository it describes, so anyone
who can read or write it already has access to that repository's source. Its
trust level is the repository's trust level, everywhere the pack is installed.
A route that could supply a hostile `workspace.toml` could supply hostile
source in the same breath, which is the threat the repository already accepts
and reviews for. There is no route-by-route case left to enumerate.

What remains assumed is narrower and cheap to see if it fails: that no
consumer downstream of this projection treats these two fields as though they
were already bounded. Nothing in the current contract promises a bound,
because the contract promises the sentinel, so a consumer that assumed one
would have been reading a value it was told not to render.

## Source

- Mode: repo-origin
- Locator: packs/core/.apm/skills/workspace-status/scripts/workspace_status.py
- Revision: commit:003709805ae14ac5f349cac72e7e544037c14033
- Authority: repo-origin
