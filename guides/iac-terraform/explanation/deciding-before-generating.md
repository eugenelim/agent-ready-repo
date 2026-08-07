---
title: Deciding before generating
summary: Why recorded decisions have to exist before infrastructure is generated, why the index is a lookup rather than a library, and why quietly inventing a policy is the expensive failure.
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

None of these are per-project questions. Answering them per project is how an
estate ends up with six authentication patterns and no one able to say which
is correct.

## The index is a lookup, not a library

The recorded decisions themselves are prose — a page each, explaining what was
chosen and what it rules out. What sits in front of them is a short index that
maps a decision area to the pages covering it.

That distinction does more work than it appears to. Without an index, "consult
the decisions" means reading everything, which means nobody does it, which
means the decisions exist and do not bind. With one, the question "what governs
network exposure?" resolves to two pages, and it resolves to the *same* two
pages for everyone — a new engineer, a contractor, an automated assistant.

The index is also the thing that makes coverage visible. A decision area with
no pages behind it is an unanswered question sitting in plain sight, rather
than one that surfaces halfway through a build.

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
