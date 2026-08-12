# Spec: Governance guide reference cleanup

- **Status:** Shipped
- **Owner:** unassigned
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Adopters receive a `guides/` tree whose Markdown does not point into repository-only governance records or changelogs. Maintainers have a deterministic, pure-stdlib lint command and CI gate that prevents links to those records, numbered ADR/RFC citations, and citations of real internal spec slugs from returning, while preserving generic governance teaching, placeholders, commands, and invented workflow examples.

## Boundaries

### Always do

- Scan every Markdown file below the selected guides root and report every violation with its path, line, and reason.
- Preserve generic governance concepts, placeholder paths, documented commands, and invented example slugs named in the task.
- Remove Type-A references at their source in `guides/`, retaining the surrounding teaching prose wherever it still makes sense.
- Add schema-valid frontmatter to every guide changed by this scrub and remove those pages' transitional navigation-baseline entries.
- Treat a same-line or immediately preceding `<!-- guides-lint: allow <reason> -->` marker as an explicit, reviewable exception.

### Ask first

- Ask before widening the scrub or guard beyond Type-A governance records and changelogs.
- Ask before adding an escape marker to a guide instead of fixing the reference.
- Ask before changing repository files outside `guides/`, `guide-nav-baseline.toml`, the new lint tool and test, the existing route-docs lint assertion needed by `build-check`, `.github/workflows/docs.yml`, `workspace.toml`, `docs/specs/governance-guides-cleanup/`, and the authorized `docs/specs/README.md` index row.

### Never do

- Never edit anything elsewhere under `docs/` beyond `docs/specs/governance-guides-cleanup/` and the authorized `docs/specs/README.md` index row.
- Never remove or reword the kept concept, placeholder, command, or invented-example usages named in the task.
- Never weaken a detection rule to make an offending guide pass.
- Never modify or retire `packs/user-guide-diataxis/`.
- Never add a runtime or test dependency.

## Testing Strategy

- Guard behavior uses **TDD** through the real CLI: fixture repositories cover each forbidden link class, numbered RFC/ADR tokens, real spec-slug matching, exclusions, escape markers, diagnostics, help, and exit semantics (AC1–AC6).
- Guide cleanup and deprecated-stream replacement use a **goal-based check** through the new guard and focused searches, plus **manual QA** for pending spec citations and preservation of the named examples (AC7–AC8).
- CI wiring uses a **goal-based check** against the workflow plus the repository build gate (AC9).
- The integrated adopter-facing result uses **goal-based checks** through all requested guide validators and tests, plus a **manual QA** scan for malformed Markdown (AC10).
- Frontmatter migration uses **goal-based checks** through `validate_guides.py` and the guide-site regression tests, plus manual verification that only scrub-touched guides were migrated (AC11).
- Construction coverage: one TDD task with a compilable red test file; three goal/manual tasks with no stubs.

## Acceptance Criteria

- [x] AC1: `python tools/lint-guides-no-repo-only-refs.py` recursively scans `guides/**/*.md`; `--guides-root` selects a fixture or alternate root, and `--help` succeeds. The CLI canonicalizes its repository, guides, and real-spec roots; refuses symlink or junction directories before descent; records each resolved directory before processing so cycles fail closed; rejects any selected root or resolved child that escapes its designated root; and exits 2 with a concise error when path resolution raises `OSError` or `RuntimeError`.
- [x] AC2: Markdown link targets containing an `adr`, `rfc`, or `specs` path segment, or `changelog` in any path component or filename regardless of case, fail with `path:line: <reason>` diagnostics.
- [x] AC3: standalone `ADR-` or `RFC-` tokens followed by two through four digits fail with `path:line: <reason>` diagnostics.
- [x] AC4: `spec/<slug>` and `docs/specs/<slug>` references fail only when the slug is a real directory below the runtime repository's `docs/specs/`; angle-bracket placeholders, `spec/plan`, `spec/loop`, `spec/slice`, commands with `<slug>`, and invented examples absent from that tree pass.
- [x] AC5: an inline `<!-- guides-lint: allow <reason> -->` marker on the violating line or immediately above it suppresses that line's violations; the script header documents this escape hatch and the pending-spec limitation.
- [x] AC6: any violation exits 1; a clean scan exits 0 and prints exactly `OK — no repo-only governance references in guides/`.
- [x] AC7: every Type-A reference in `guides/**/*.md` is removed, including real and pending spec citations found by human judgment, while the task's named concept, placeholder, command, and invented-example cases remain unchanged.
- [x] AC8: every `user-guide-diataxis` mention in `guides/` points readers to `product-documentation` instead, without changing the compatibility pack under `packs/`.
- [x] AC9: `.github/workflows/docs.yml` invokes the new guard in the existing direct-Python style and its pull-request path filter includes `guides/**` and `tools/lint-guides-no-repo-only-refs.py`.
- [x] AC10: all requested verification commands pass, the primary guard is exercised end to end, and the scrub leaves no empty Markdown targets or orphaned link text.
- [x] AC11: all 19 guides changed by the scrub have schema-valid `title`, `summary`, `pack`, and `kind` frontmatter; their transitional entries are absent from `guide-nav-baseline.toml`; and no otherwise-untouched guide is migrated.

## Assumptions

- Technical: the guard mirrors `validate_guides.py` with default `guides/` and a `--guides-root` override (source: `tools/validate_guides.py:299`).
- Technical: the real spec-slug set is the set of directories directly below the runtime repository's `docs/specs/` tree (source: `docs/specs/` directory probe).
- Technical: documentation CI invokes repository tools directly with Python (source: `.github/workflows/docs.yml`).
- Product: `guides/` is the public adopter-facing documentation source and has no existing link checker (source: `guides/AGENTS.md`).
- Product: the scrub is limited to Type A and preserves the named teaching cases unchanged (source: user confirmation 2026-08-12).
- Process: the change is mixed-shaped and is registered as independent work under `ini-007` (source: user confirmation 2026-08-12).
- Process: current local refs are accepted despite unavailable remote freshness verification (source: user authorization 2026-08-12).
- Process: `docs/specs/README.md` carries the required active-spec index row (source: user authorization 2026-08-12).
- Product: every guide touched by the scrub is migrated to required frontmatter in the same change (source: user authorization 2026-08-12).
