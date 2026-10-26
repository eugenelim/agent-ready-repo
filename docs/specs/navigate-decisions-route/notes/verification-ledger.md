# Verification ledger: navigate-decisions route mode

Execution evidence for [`spec.md`](../spec.md). Each entry records what was run and
what it showed.

## 2026-10-26 — T1 frozen inputs

- **Pre-change commit:** `5cec6ac3e` (the merge base with `main`; `packs/repo-governance/` is byte-identical at the branch head when T1 landed, before any `SKILL.md` edit).
- **Frozen files (sha256):**
  - `notes/route-queries.json` — `49b288bee1dd26933010e9218164eee6b7747cfb7bfbe511aa75517123648cdf`. 15 should-trigger queries; an exact string check found none in the eval files of `navigate-decisions`, `new-rfc` or `new-adr`.
  - `notes/seam-requests.json` — `33080307aae71586bf0954e7f0107cdfaa281e4526fc7b50472ca22122b9f279`. 12 requests: 4 from `new-rfc` eval 7, 2 from eval 8, 6 from eval 11, each with its expected tag or tag set.
  - `fixtures/route-hostile/request.txt` — `967b7d09db5b9f786dd9cdcf10960d970110b8d25d8efd0cdf1bc987a3d2eea4`. One line; the hostile ADR's title contains it, and the ADR decides an unrelated matter (double-entry bookkeeping).
  - `fixtures/route-advice/request.txt` — `b420c9c3e169fefeb971db5fdecf20a2803b616e5c1f88a56d53d19ffb4cd4e9`. Supplies `@platform-team` and `security reviewers`; the records name `@queue-owner`, `@data-team`, `@ops-guild` and `release managers`.
  - `fixtures/route-seam/` holds ADR-0001 (shared logging library), ADR-0002 (Redis sessions), RFC-0001 (retry behaviour) and an RFC index, so the repository has an RFC process.
  - Fixture paths are under `packs/repo-governance/tests/skills/navigate-decisions/`. All three parse through `navigate_decisions.py` with status `ok`; a `text` search for `payments module` on the hostile fixture returns ADR-0001.
- **ADR lint at the pre-change commit:** `notes/adr-lint-pre-change.txt` — 147 read, 0 refused, 0 unreadable, 0 findings, exit 0.
