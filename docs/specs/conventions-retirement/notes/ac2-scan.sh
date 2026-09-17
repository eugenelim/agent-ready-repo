#!/bin/sh
# The single exclusion predicate. Step 2 discovery, step 4 check, and the AC2
# guard all invoke THIS file unchanged, so the enforced domain cannot drift from
# the criterion's prose.
#
# Matches `CONVENTIONS` without the `.md` suffix: live sources cite the document
# by section alone (e.g. `CONVENTIONS § 4`, `CONVENTIONS § "The argv ban"`), and
# a suffixed pattern misses 17 of them.
#
# Two exclusion classes:
#   historical records  — never edited to repair a reference
#   projection targets  — regenerated from their source, never hand-edited
# A directory index is NOT a historical record, so each exclusion over a
# record directory is scoped one level down and leaves the index itself in:
# `docs/specs/*/**` keeps `docs/specs/README.md`, and `docs/product/*/**` keeps
# `docs/product/README.md`. Round 9 found the unscoped `docs/product/**` form
# hiding a live index that still linked to the retired document. The one
# top-level product file that IS a historical record — the release changelog —
# is named directly, because `**/CHANGELOG.md` above matches only the uppercase
# spelling.
git grep -ln "${1:-CONVENTIONS}" -- . \
  ':(glob,exclude)docs/specs/*/**' \
  ':(glob,exclude)docs/rfc/**' \
  ':(glob,exclude)docs/adr/**' \
  ':(glob,exclude)docs/product/*/**' \
  ':(exclude)docs/product/changelog.md' \
  ':(glob,exclude)docs/knowledge/observations/**' \
  ':(glob,exclude)docs/knowledge/topics/**' \
  ':(glob,exclude)**/CHANGELOG.md' \
  ':(glob,exclude)**/fixtures/corpus/**' \
  ':(glob,exclude)web/**' \
  ':(glob,exclude).claude/**' \
  ':(glob,exclude).agents/**' \
  ':(glob,exclude).codex/**' \
  ':(glob,exclude)dist/**' \
  ':(glob,exclude).agentbundle/**' \
  ':(exclude)docs/CONVENTIONS.md' \
  ':(exclude)packs/core/seeds/docs/CONVENTIONS.md' \
  ':(exclude)packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py'
