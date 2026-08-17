# Tracker intake vocabulary

Use this reference to separate tracker terms from repository routing concepts.
Tracker objects supply content and versioned profile hints. They do not name the
artifact that `work-intake` must create.

## Intent index

| You want to | Result |
| --- | --- |
| Start from tracked work | A validated `normalized-intake.v1` record and content-based route |
| Compare tracker profiles | Equivalent content produces the same artifact, membership, processor, and authority |
| Handle a collection | Coherent content may become a brief; unrelated content becomes separate units or view-only |
| Report a regression | `bug-fix` only when durable expected-behavior evidence exists |

## Object names are hints

| Tracker | Common container hints | Common item hints |
| --- | --- | --- |
| GitHub | Milestone, project, query | Issue |
| Linear | Project, Cycle, view | Issue, sub-issue |
| Jira | board, sprint, Epic, JQL result | Story, Task, Bug |
| Jira Align | Program Increment, Feature, collection | Story, Task, Defect |

No row is a fixed mapping. A coherent Jira board can describe one outcome; an
incoherent Milestone can be only a view. The adapter preserves the object type
as a hint while `work-intake` classifies from content.

## Normalized record

Each adapter returns:

- contract version and requested action;
- bounded outcomes, constraints, evidence, behaviors, assumptions, and gaps;
- trusted source locator, comparable revision, and object hint;
- versioned tracker profile;
- confidentiality and cross-repository constraints;
- proposed authority mode.

Raw payloads, credentials, embedded instructions, unnecessary sensitive data,
and personal data are excluded. Invalid strict JSON, missing provenance,
unknown profiles, unsafe redaction, or a confidentiality mismatch fails before
repository writes.

## Reads, writes, and limits

**Reads:** Jira, Jira Align, and Linear through their sibling acquisition
skills; GitHub through approved `gh` reads.

**Tracker writes:** none during intake.

**Repository writes:** only `work-intake`, after validation and any required
human decision.

**Limits:** every profile fixes maximum pages, items, bytes, timeout, retries,
backoff, and the explicit incomplete or refusal outcome.

## Route vocabulary

| Repository term | Meaning |
| --- | --- |
| intent | A bounded opportunity or outcome that is not yet a shippable contract |
| spec | One independently shippable, verifiable behavior |
| brief | One coherent outcome requiring several specs |
| defect | A regression backed by durable expected-behavior evidence |
| view-only | A collection that should be inspected without materialization |
| authority mode | Which side is authoritative for the current intake record |

Refresh conflict handling, execution locks, and tracker write-back are outside
tracker intake.

## See also

- [Choose a tracker integration](../how-to/choose-a-tracker-integration.md)
- [Work intake routing reference](../../core/reference/work-intake-routing-and-lifecycle.md)
