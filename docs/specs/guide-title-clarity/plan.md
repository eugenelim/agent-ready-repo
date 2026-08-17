# Plan: Guide title clarity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Approach

Pin the four approved strings and the five no-change controls in the existing
title-lint surface, update source headings and applicable navigation labels,
then build both sites and inspect the emitted title surfaces. Metadata absent
from these pages remains the responsibility of the dependent metadata spec.

## Constraints

- Follow `docs/design/principles/tech-site.md` and the existing platform
  aesthetic direction.
- Preserve paths, slugs, aliases, and link targets.
- Keep the change limited to the nine reviewed title decisions.

## Construction tests

**Integration tests:** full site generation, both Astro builds, title lint, and
combined rendered-link checking.

**Manual verification:** inspect the four emitted pages in navigation and
search/title contexts against the precision-authority design goal.

## Design (LLD)

### Design decisions

The source H1 is the canonical fallback title until metadata is present.
Navigation labels match the approved title where the page participates in
navigation. No route is derived from the new wording. Traces to: AC1-AC7.

### Component / module decomposition

The source Markdown owns page wording, `guide-nav-baseline.toml` owns pinned
sidebar labels, and generated Starlight pages provide the emitted evidence.
Traces to: AC1-AC7.

### Quality attributes (NFRs)

The four titles remain understandable in a five-second scan and introduce no
Major design finding against the approved directions. Traces to: AC8.

## Tasks

### T1: Title contract tests pin four changes and five controls

**Depends on:** none

**Touches:** tools/lint-guide-titles.py, tools/test_lint_guide_titles.py, guide-nav-baseline.toml, guides/**/*.md

**Tests:**
- TDD: require each of the four approved source-title mappings (AC1-AC4).
- TDD: pin the five reviewed no-change titles (AC6).
- TDD: require applicable navigation labels to agree (AC5).

**Approach:**
- Extend the existing title-linter fixture and assertions.
- Test public behavior and mappings rather than line numbers.

**Done when:** the focused tests fail on the old four strings and protect the
five controls.

### T2: Source and navigation use the approved titles

**Depends on:** T1

**Touches:** guides/frontend-engineering/how-to/page-screen-contract.md, guides/frontend-engineering/how-to/run-an-audit.md, guides/frontend-engineering/tutorials/scaffold-a-component.md, guides/iac-terraform/README.md, guide-nav-baseline.toml

**Tests:**
- Goal-based: run the title linter and its focused tests (AC1-AC6).
- Goal-based: search the four sources for the retired strings and require zero
  hits (AC1-AC4).

**Approach:**
- Change each source H1 exactly once.
- Change only the applicable baseline labels; do not add navigation entries.

**Done when:** all source and navigation title contracts pass.

### T3: Emitted titles and routes remain coherent

**Depends on:** T2

**Tests:**
- Goal-based: build both sites and assert the four generated H1/title surfaces
  (AC5).
- Goal-based: run combined rendered-link checking and route assertions (AC7).
- Visual/manual QA: review navigation and search/title presentation at desktop
  and phone widths (AC8).

**Approach:**
- Use emitted HTML as evidence rather than source-only assertions.
- Record screenshots only as temporary review evidence, never tracked output.

**Done when:** all four titles are correct in emitted behavior and every route
still resolves.

## Rollout

This is a content-only change on existing routes. Reversion restores the old
strings without migration; no alias or redirect changes.

## Risks

- A baseline label may drift from the source title.
- The later metadata backfill could reintroduce an old title unless it consumes
  this spec's approved strings.
- A route accidentally derived from title wording would break inbound links.

## Changelog

- 2026-08-17: initial plan derived from the approved tech-site completion brief.
