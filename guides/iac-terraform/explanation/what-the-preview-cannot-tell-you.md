---
title: What the preview cannot tell you
summary: The change preview is the strongest verification infrastructure work has — and it has three specific blind spots worth naming before you rely on it.
pack: iac-terraform
kind: explanation
order: 3
---

# What the preview cannot tell you

## Why the preview earns its place

Infrastructure tooling can compute the exact set of changes it would make
without making them. That preview is the artifact the whole loop is built
around: it can be read, checked against policy rules, priced, frozen, and
approved.

It is also the reason the cheap loop described in
[the release loop](../../release-engineering/explanation/the-release-loop.md)
is unusually productive here. Most disciplines have to reason about what a
release will do. Infrastructure gets to read it.

Which makes it worth being precise about what it does not cover. A check this
strong invites the assumption that a clean result means a safe change, and
three gaps sit underneath that assumption.

## Gap one: it does not know what the platform accepts

A preview validates that your definition is internally consistent. It does not
validate that the settings you used exist.

This is the failure mode automated generation is most prone to. Cloud platforms
change constantly; anything working from recollection will confidently produce
settings that were valid two years ago, or were never valid, and phrase them
plausibly enough to survive review. The preview may well accept them, because
they are well-formed.

The defence is to ask the platform itself what it currently supports and build
only from that answer, every time — not from memory, and not from an example
found elsewhere. Doing this eliminates an entire category of confident-sounding
error, and it is the single largest quality lever when generation is automated.

## Gap two: it compares a definition to reality, so it cannot see what has no definition

The preview works by comparing your recorded definition against the live state
of the things it knows about. Anything created entirely outside that
process — built by hand, in a console, with no record — is invisible to it.

This is not a defect to be fixed; it is what the mechanism is. But it means a
clean preview says *"the things I manage match what I expect."* It does not say
*"the environment matches what you expect."* Those are different claims, and
the gap between them is exactly where an emergency change made at 2am lives.

Two consequences follow. Any report should say plainly what it covered rather
than implying full coverage — a report that reads as complete when it is
partial is more dangerous than no report. And finding unmanaged resources needs
a separate sweep; it will not fall out of routine checking.

## Gap three: it is not a test that anything works

A clean preview confirms a change will apply. It says nothing about whether the
resulting system serves traffic.

Some failures only appear at the moment of creation: permissions that take
minutes to become effective, capacity limits, ordering problems between
resources, things that fail in ways no preview models. Others appear only
afterwards — the database exists and is unreachable, the service starts and
returns errors.

So the preview is a precondition, not evidence of working software. Confirming
the system actually responds requires exercising it for real, on the disposable
rehearsal environment, before production. That is why the rehearsal step exists
rather than going straight from a clean preview to a production change.

## What this adds up to

Treat the preview as what it is: an unusually good static check that catches a
large class of problems early and cheaply. Then keep three habits around it.

Build from what the platform says it supports today. State what your checks
did and did not cover, every time. And prove the thing runs before you believe
it works.

## Where to go next

For where this sits in the wider loop, see
[infrastructure in the release loop](infrastructure-in-the-release-loop.md).
For the governance that has to be in place before any of it starts, see
[deciding before generating](deciding-before-generating.md).
