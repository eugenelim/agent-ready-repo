---
title: Deciding before generating
summary: Why governing sources and explicit decisions bind infrastructure work before generation.
pack: iac-terraform
kind: explanation
order: 2
---

# Deciding before generating

## The gate that comes before the loop

[The release loop](../../release-engineering/explanation/the-release-loop.md)
starts once you know what you're building. Infrastructure adds a step in front
of it, and it is not optional: **the decisions that bind the work must already
be written down.**

This is the difference between infrastructure that is automated and
infrastructure that is governed. Automated means something produced it fast.
Governed means someone can say why it looks the way it does, six months later,
without asking the person who built it.

## What gets decided once

A handful of questions get settled once for an organization and then inherited
by every piece of work:

- Where system-of-record data lives, and how concurrent changes to it are kept
  safe.
- How automated pipelines get permission to act — and whether long-lived
  credentials are allowed to exist at all.
- What must be labelled on every resource, so cost and ownership are
  attributable.
- Whether anything may be publicly reachable, and who owns the network layer.
- What may change without a person approving it.

Record which answers apply to the project so each change can be checked against
the same constraints.

## Sources bind the work directly

Repository instructions, accepted decisions and explicit caller inputs can govern
the work without an index or a shared decision template. Bounded discovery finds
candidate files; the agent selects the sources that apply and records their
constraints and exact-byte digests in a governance summary. The
[authoring gate](../reference/authoring-gate.md) checks that summary before code
is written.

A missing source, changed digest, conflict or unresolved issue stops the affected
step. Accepted decisions need a verbatim accepted-status line. This makes the
source of a requirement visible without asking every repository to adopt the
same record format.

An index or additional reviewer can help as an optional integration. It cannot
weaken a failed check. An unavailable integration leaves the direct path intact;
a refusal stops work until resolved. Retrying through a weaker local fallback
would hide the very decision the gate exists to expose.

## The failure this prevents

The expensive failure is not a wrong decision. It is a decision made silently,
by whoever was closest to the keyboard, and never recorded as one.

It looks harmless. A required setting is missing, something plausible gets
filled in, the work proceeds. What has actually happened is that a policy was
established — by accident, with no author, no rationale, and no visibility. It
then gets copied, because the next piece of work reasonably imitates the last.
By the time anyone notices, it is a convention, and convention is far harder to
change than a decision.

So when a piece of work touches an area nothing has decided, the correct
behaviour is to stop and raise it — not to fill the gap with something
reasonable. A stated assumption a human accepted is fine. A guess nobody saw is
not.

## Describe the need before naming the product

One habit is worth adopting alongside the recorded decisions: write down what
capability you require before naming any specific product.

"A managed relational database with these durability characteristics" is a
requirement. A vendor's product name is an answer to it. Keeping them separate
for one step means the requirement stays reviewable by people who don't know
that vendor's catalogue, and that revisiting the choice later means changing
one layer rather than rewriting the need.

The product names arrive one step later, when you decide *how*. They should
arrive as a consequence of the requirement, not as a substitute for having
written one.

## Where to go next

Once the decisions are recorded and the requirement is stated, the loop is the
ordinary one — see
[infrastructure in the release loop](infrastructure-in-the-release-loop.md) for
where the gates land, and
[what the preview cannot tell you](what-the-preview-cannot-tell-you.md) for the
limits of the check everything else rests on.
