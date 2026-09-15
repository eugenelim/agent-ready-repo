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
# `docs/specs/README.md` is a directory index, NOT a historical record, so the
# spec-directory exclusion is scoped to `docs/specs/*/` and leaves it in.
git grep -ln "${1:-CONVENTIONS}" -- . \
  ':(glob,exclude)docs/specs/*/**' \
  ':(glob,exclude)docs/rfc/**' \
  ':(glob,exclude)docs/adr/**' \
  ':(glob,exclude)docs/product/**' \
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
  ':(exclude)packs/core/seeds/docs/CONVENTIONS.md'
