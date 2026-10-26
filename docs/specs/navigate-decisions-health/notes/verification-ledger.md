# Verification ledger: navigate-decisions health mode

Execution evidence for [`spec.md`](../spec.md). Each entry records what was run and
what it showed.

## 2026-10-26 — Dispatch

- On 2026-10-26 eugenelim directed in session that the controller runs the evidence tasks T1, T5 and T6 itself, so their dispatch receipts are recorded as `human-directed`. T2, T3 and T4 go to implementer subagents.

## 2026-10-26 — T1 frozen inputs

- **Pre-change commit:** `0eecbb61c`. `packs/repo-governance/.apm/` is byte-identical to `origin/main` at that commit, and no `SKILL.md` has been edited.
- **Frozen files (sha256):**
  - `notes/health-queries.json` — `9e4e9e97f3009803551c67bd23bc8588f8628a2ae8e5a5fa44c547ab8ee3425a`. 15 should-trigger queries; an exact string check found none in the eval files of `navigate-decisions`, `new-rfc` or `new-adr`.
  - `fixtures/health-hostile/docs/adr/0001-cache-policy.md` — `b43347259d31510e7753647b716ce7d45a51e3abe859ce1e0e21e89bb13fad1c`
  - `fixtures/health-hostile/docs/adr/0002-vendored-parser.md` — `29a5ae8a65ffc8400dd3e7824f7c979eb8f3b2943c97e4aa6dc08bda8633cab9`
  - `fixtures/health-hostile/docs/adr/0003-session-store.md` — `f2ef91db612d62dbb09d27d07c52e9d76355fa466806df4a3858a1823dd10056`
  - `fixtures/health-hostile/docs/adr/0004-session-database.md` — `851da87a7185a1837cd8307445509ca6031c71bba3a3e0bebce321a0ea5a63df`
  - `fixtures/health-hostile/docs/adr/0005-login-flow.md` — `45d6596c740b89b1a49009875a1ac0fdf2f44d5acb7a426929f1c8acac548475`
  - `fixtures/health-hostile/docs/rfc/0001-session-direction.md` — `0b6cb098d9f6a0596e060037cd1db1846a5711421d2f0cbf25013170bee76cf9`
  - `fixtures/health-hostile/request.txt` — `cf5e01a0d1704298459a2ba86cd2e9c9a599d9158df46c4e7957b8020f2b3659`
  - `fixtures/health-hostile/tools/present-check.py` — `b2c2e4386aed1cf2398141990146ea3afa4774459e9181b79af432af756293a9`
- Fixture paths are under `packs/repo-governance/tests/skills/navigate-decisions/`. The fixture parses through `query --operation summary` with status `ok` (5 accepted records, 1 superseded). Its ADR-0001 holds instruction text, U+202E and U+0007 in its trigger, the passed date 2025-01-31, and signal paths that are present (`tools/present-check.py`), missing (`tools/missing-check.py`), escaping (`../outside-check.py`), absolute (`/etc/passwd`), a URL, and one through `linked/` (unlocated until a test creates `linked` as a symbolic link). ADR-0002 names version `2.0` and has no `Confirmation`; ADR-0003 is superseded by ADR-0004 and cited in the headers of ADR-0005 and RFC-0001.

## 2026-10-26 — T5 amendment

- **Finding:** T5's pinned `Tests` say hand-check reviewers "have only `Read`, `Glob` and `Grep`". No agent type available in this session has exactly those tools and will do the task: the one that does (`shaping-reviewer`) refused in two attempts as outside its contract-review scope, so no reading was produced. Five further reader sessions were stopped before returning; their partial reads are discarded.
- **Owner decision:** eugenelim chose on 2026-10-26 in session that general-purpose readers are told to use only `Read`, `Glob` and `Grep`, and that afterwards each reader's transcript is searched. Any `Bash` call, or any read outside `docs/adr/`, `docs/rfc/`, the listing and the rules file, voids that share, and a fresh reader redoes it.
