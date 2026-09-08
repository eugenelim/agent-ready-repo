---
title: Tracker intake vocabulary
summary: Distinguish tracker objects and profile hints from the repository artifacts and lifecycle routes selected by `work-intake`.
pack: _shared
kind: reference
---

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
| Refresh registered tracked work | A reviewed field delta governed by the artifact's source-authority record |
| Write coordination facts back | One profile-declared action after one fresh exact confirmation |

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

## This reference covers intake only

The table above is deliberately hint-shaped because intake classifies from
content, not from an object's name. The **outbound** direction is the opposite:
projecting a repository-owned intent tree out to a tracker uses a fixed
level-to-object mapping per profile, because the canonical model is already
known. That mapping is in
[Project intents and slices out to a tracker](../how-to/project-slices-to-a-tracker.md).

Do not read a row here as the inverse of a row there. Intake asks "what is this
content?"; projection asks "where does this known level land?".

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

Refresh preserves this intake boundary. It is a later operation against an
existing tracker-origin artifact, not another intake route. Local requirement
decisions and remote coordination writes are separate: approving one never
approves the other.

## Route vocabulary

| Repository term | Meaning |
| --- | --- |
| intent | A bounded opportunity or outcome that is not yet a shippable contract |
| spec | One independently shippable, verifiable behavior |
| brief | One coherent outcome requiring several specs |
| defect | A regression backed by durable expected-behavior evidence |
| view-only | A collection that should be inspected without materialization |
| authority mode | Which side is authoritative for the current intake record |

## Refresh vocabulary

| Refresh term | Meaning |
| --- | --- |
| compared revision | Latest source revision successfully compared, even when local values are kept |
| accepted revision | Source revision whose requirement values were accepted locally |
| conflict | A reviewed `revise-both` result that remains unresolved |
| local receipt | Evidence that the artifact and workspace mirror advanced together |
| remote-action receipt | Pending, failed, or succeeded evidence for one separately confirmed tracker mutation |

Implementing specs and Executing briefs refuse requirement refresh. Shipped
requirements stay locked, while the active profile may allow confirmed
coordination-only write-back.

## See also

- [Choose a tracker integration](../how-to/choose-a-tracker-integration.md)
- [Work intake routing reference](../../core/reference/work-intake-routing-and-lifecycle.md)
- [Use work intake](../how-to/use-work-intake.md)
