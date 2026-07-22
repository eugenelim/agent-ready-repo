# Adversarial review — round 4

**Date:** 2026-07-22  
**Reviewer:** adversarial-reviewer subagent

## Blocker (applied)

**1. T5 awk anchor wrong.** `^\[Unreleased\]` never matched `## [Unreleased]` header. Fixed: `^## \[Unreleased\]`.

## Concerns (applied)

**2. Spec/plan disagreed on AC1b/AC1d artifact location.** Spec said "transcript"; plan said "transcript.md or tutorial-review.md"; T1 runs before transcript exists. Fixed: both spec (Testing Strategy) and plan (T1 step 5) now say `notes/tutorial-review.md`.

## Nits (applied)

**3. No-terminal grep was narrow** (missed `git clone`, `git log` etc.). Fixed: pattern now matches `git ` broadly.

**4. Changelog entry used conventional-commit format** instead of Keep-a-Changelog bold-lead bullet. Fixed: prescribes a `### Added` bold-lead entry matching surrounding entries.
