# Verification ledger: captured items in their own files

## T7 — this repository's migration, 2026-10-26

The tree the repair read is branch head `f8b614d587358fd2767d698031cbe696a08bd6cb`.

1. **Before, old engine.** `workspace-status status` from the engine at `ce30822a0`, run from a `git worktree` of that commit at `.context/engine-ce30822a0`, over the tree above: 0 ready, 3 active, 30 blocked; canonical findings 33 `unsatisfied_dependency`, 26 `unsupported_legacy`, 8 `unapproved_spec` (67). Every one of the 58 `(deferred: <anchor>)` markers in `docs/specs/*/spec.md` resolved, by `lint-spec-status.py`'s `canonical_entry_anchor` rule.
2. **Plan.** `repair-plan --plan-file .context/captured-plan.json`: 77 `captured-to-file` operations (51 memberships, 26 legacy slug-only entries), no captured-item manual finding, and one unrelated existing finding (`type1-untracked`, `spec/plan-evolution-experiments`). Plan file sha256 `1e308ebaf50cd877401df904cfd3c49f21a0e1a7abb91fc6637e42ab14b857fb`, plan_id `b013339f277e01b1612c81c6734e35c3270c3903b180c8cc57cb9dd2f58d2ba6`. Assigned kinds: 74 `defect`, 2 `design`, 1 `intent` (`contract-discovery-reference-grammar`, `Type: shape`). The owner, eugenelim, confirmed this exact plan file on 2026-10-26.
3. **Apply.** `repair-apply --yes` on that plan, with the pinned `tomlkit` 0.15.1: `operations_applied` 77, `captured_equal` true, 77 items read and 77 records read back; the three copied `Depends on:` edges of `portfolio-outcome-entry-surfaces` equal before and after, keyed by `docs/product/captured/portfolio-outcome-entry-surfaces.md`. `workspace.toml` digest `ff94a2cb…a21a1` before, `ecc06489…a5a1` after.
4. **After, this slice's engine (AC-0034, AC-0035).** `canonical.ready`, `canonical.active`, and `canonical.blocked` paths equal the before set, and the 67 canonical findings equal it by code, with each migrated membership's old path mapped to its record path. The `captured` object lists 77 items and no finding, and no `unmigrated_captured_item` finding remains.
5. **Deferral anchors (AC-0036).** All 58 markers still resolve.
6. **Hand edits.** The copied `Depends on:` line was removed from `docs/product/design/portfolio-outcome-entry-surfaces.md`, and `workspace.toml`'s header comment now says where a captured item's entry points. `status` after these edits gives the same canonical result.

The comparison scripts were scratch files under `.context/` and are not committed.
