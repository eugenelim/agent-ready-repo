---
title: Infrastructure in the release loop
summary: Provisioning infrastructure is the release loop with a different payload — what carries over unchanged from shipping code, and the three places it genuinely differs.
pack: iac-terraform
kind: explanation
order: 1
---

# Infrastructure in the release loop

## This is not a separate process

Teams adopting infrastructure automation usually expect a new workflow. It
isn't one. Provisioning infrastructure runs the same loop as shipping code,
with a different payload.

Read [the release loop](../../release-engineering/explanation/the-release-loop.md)
first. Everything it says about the split between the cheap loop and the real
one, about approving an exact change set rather than an intention, and about
classifying what can't be undone — all of it applies here unchanged. This page
covers only what is genuinely different when the thing being shipped is
infrastructure rather than an application.

That framing matters practically. An organization standing up a central
infrastructure practice does not need a second governance model, a second set
of gates, or a second review culture. It needs the one it already has, pointed
at a different artifact.

## Where the gates land

The `iac-terraform` pack is the only pack in this catalogue that sits on both
of the release loop's gates:

**The build-to-release gate** is reached when a preview of the exact changes
exists, is checked, and is frozen. Nothing has been created yet. This is where
the authoring work stops — permanently. The tooling never applies anything;
it produces a reviewed, pinned change set and hands it over.

**The release-to-production gate** is the last human decision before real
infrastructure changes. It is reached only after the change set has been
rehearsed somewhere disposable and the evidence assembled.

The gap between them is where infrastructure differs most, and it is the
subject of [what the preview cannot tell you](what-the-preview-cannot-tell-you.md).

## What carries over unchanged

Most of it, which is the point:

- The cheap loop and the real loop are separate, and everything answerable in
  the cheap one gets answered there.
- A person approves a frozen, exact change set — not a branch, not a direction.
- Changes are classified by whether they can be undone, so that routine work
  moves fast and permanent work gets scrutiny.
- Convergence is proven on a disposable copy before production.

If your teams already work this way for application code, they already work
this way for infrastructure. There is no second thing to learn.

## The three real differences

**A preview is a genuine artifact here.** Infrastructure tooling can compute
the exact set of changes it would make and write it to a file. That file is
reviewable, checkable by policy rules, and freezable. Most application
deployments have no equivalent — you reason about what a release will do.
Here you read it. This is the single biggest advantage infrastructure work has,
and the loop is built around exploiting it.

**Undo is often not available at all.** In application code, most changes are
a revert away. In infrastructure, deleting a storage bucket or a database
table destroys data, and some settings cannot be turned off once enabled. The
reversibility classification the release loop already asks for stops being
paperwork and starts being the thing that decides which approvals are serious.

**Some failures only appear on the real system.** Permissions that take minutes
to propagate, capacity limits, resources that fail in ways no preview models.
A clean preview is necessary and not sufficient — which is exactly why the
rehearsal step exists rather than going straight to production.

## Where to go next

Two things upstream of any of this. The decisions that bind your infrastructure
have to be written down before anything is generated, or the generated result
is ungoverned by construction — see
[deciding before generating](deciding-before-generating.md).

And the preview that anchors the whole loop has known limits worth naming
before you rely on it — see
[what the preview cannot tell you](what-the-preview-cannot-tell-you.md).
