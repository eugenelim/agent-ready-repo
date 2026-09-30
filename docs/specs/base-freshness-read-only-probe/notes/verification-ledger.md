# Verification ledger: Read-only base freshness probe

## 2026-09-29 — projected-helper manual QA

The `.agents` projected helper was byte-identical to the canonical core source
before these runs. Each case used a disposable local Git origin, so no external
credentials or network destination was involved.

| Case | Exit | JSON result | Fetch command class |
| --- | ---: | --- | --- |
| Fresh explicit target | 0 | `{"status": "ok", "message": "head is current", "target": "origin/main"}` | Read-only dry-run advertisement only; no write-capable fetch |
| Writable stale target | 1 | `{"status": "surface", "message": "branch is 1 commit(s) behind 'origin/main' — run: git rebase refs/remotes/origin/main", "target": "origin/main"}` | Read-only dry-run advertisement, then exact-ref write-capable fetch to prepare the update path |
| Metadata-denied stale target | 1 | `{"status": "surface", "message": "branch is stale relative to 'origin/main', but this environment could not prepare the update because git metadata write was denied by local policy — ask the user to update the branch separately", "target": "origin/main"}` | Read-only dry-run advertisement, then an exact-ref write-capable fetch rejected by the disposable repository's read-only remote-tracking directory |

The denied-case directory permission was restored immediately after the run.
These observations cover AC-0001, AC-0002, AC-0003, and AC-0009.

## 2026-09-29 — fallback and repository gates

- `test_unsupported_porcelain_fallback_ls_remote_missing_target_ignores_cached_ref`
  forces the exact unsupported-porcelain fallback, returns an empty live
  `ls-remote` result while a cached tracking ref exists, and verifies a blocking
  missing-target result with no write-capable fetch. This covers the remaining
  AC-0006 verdict.
- Targeted helper suite: 56 passed.
- Ruff: passed.
- mypy: passed for 149 source files.
- `git diff --check`: passed.
- `make bootstrap-sites`: passed in the owner environment.
- Catalogue verification: passed in the owner environment.
