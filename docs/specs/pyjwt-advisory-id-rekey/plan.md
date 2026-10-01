# Plan: PyJWT advisory id re-key

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0131 (a suppression is a governed allowlist entry)
  and ADR-0133 (an unfixed advisory retires on the first fix) govern the entry
  shape. `tools/run-pip-audit-gate.py:391` is the matching rule this delivery
  conforms to, `:242` pins the advisory source, and `:323-331` rejects a
  duplicate `(id, package)` pair. `tools/test-run-pip-audit-gate.py:171-177` is
  the analogous existing assertion of the matching rule. `tools/AGENTS.md` adds
  no delta this change crosses: it governs new `tools/` scripts, and this
  delivery adds none.

## Approach

The gate matches an allowlist entry to a reported advisory on the primary `id`
alone. The thirteen accepted PyJWT advisories are now reported under their
`PYSEC-2026-41xx` identifiers, so the entries are re-keyed to those identifiers
and nothing else moves. The gate, its self-test, and the governing records are
untouched.

## Constraints

- `tools/run-pip-audit-gate.py` is not edited. Alias matching is refused by
  design, for the reason the allowlist header states at lines 27-30.
- Every entry's accepted risk is unchanged. `PYSEC-2026-4146` keeps
  `fixed_in = "none"` under ADR-0133.
- The stop rule for a disagreeing advisory record is `spec.md` § Agent Rules ›
  Always do. It is self-contained there and needs no value from this plan.

## Construction tests

Three goal-based checks, each run against the real artifact rather than a
fixture, because the subject is stored data the live feed decides. Two further
bullets describe where the verifier lives and how it fetches, rather than
adding checks:

- `python3 tools/run-pip-audit-gate.py tools/requirements-sast.txt` — the gate's
  own verdict over the real report and the edited allowlist.
- A disposable verifier that joins `tools/pip-audit-allowlist.toml` to three
  sources: a `pip-audit --format json` run, the same file at the base revision
  AC5 names, and one advisory record per entry. The join key is the CVE, read
  from a different place on each side: at the base revision it is the entry's
  `id`; after the edit it is the `# alias:` comment above the entry. It reads
  the file as text to bind each `# alias:` line to the `[[allow]]` table that
  follows it, and uses
  `tomllib` only for field values and the entry count — `tomllib` discards
  comments, so the alias AC3, AC4 and AC6 depend on is unreachable from a
  parsed document, and Never-do bullet 3 rules out a comment-preserving
  dependency.
  It prints a run-date line and a per-entry line; AC4 retains that output
  together with the script's source, because the script is uncommitted and
  would otherwise leave AC3 resting on an unreproducible paste.
- It is written to the session scratch directory, outside the repository
  working tree. That keeps it clear of `tools/AGENTS.md`'s pure-stdlib
  standalone-entry-point contract and of the lint sweep T3 runs, and is why
  `spec.md` § Agent Rules › Ask first carves it out rather than treating it as
  a file change needing sign-off.
- The advisory lookup is a read-only `GET` to
  `https://api.osv.dev/v1/vulns/<entry id>` over stdlib `urllib.request` — no
  credentials, no write, thirteen requests, once. The root `AGENTS.md` declares
  no blessed outbound-HTTP helper, so this is named here rather than left
  implicit, and it leaves the repository with no new egress.
- `python3 tools/test-run-pip-audit-gate.py` — unchanged, and green proves the
  matching rule still behaves as its case 13 asserts.

A disposable spike confirmed the mechanism before approval: driving `evaluate()`
over the live report with only the thirteen `id` values substituted moves the
gate from exit 2 with 28 lines — thirteen advisories "no entry covers" and
thirteen entries "absent but the fix is not" — to exit 0 with thirteen accepted.
Re-keying alone is sufficient; nothing else in the file is load-bearing for the
failure.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth / `tools/pip-audit-allowlist.toml` header | T2 | Spec AC6 and AC8 | Every identifier in the header resolves to an entry, by equality or by its annotation, and a dated sentence records the re-key |

## Design (LLD)

### Design decisions

- **The CVE alias is a comment above each entry, not a sentence inside
  `reason`.** Neither form is visible to tooling: the gate reads `reason` only
  to validate it is a non-blank string (`run-pip-audit-gate.py:69`, consumed at
  `:312`), and the one `accepted` line it prints carries `id` and
  `unblocked_when`, not `reason`. So the consumer of this alias is a human
  reading the file, and both forms serve that reader equally. The comment is
  chosen because it is the less invasive of two equal options: every `reason`
  stays byte-identical to base, which keeps each accepted-risk argument
  provably untouched and lets AC2 be a plain comparison rather than a
  prepend-and-compare with an exception. AC3 pins the form as a
  `# alias: CVE-<digits>-<digits>` line immediately above the `[[allow]]` line,
  so binding a comment to its entry is a line-adjacency test rather than a
  judgement about which nearby comment was meant.
  What the comment trades away, recorded so a later reader does not rediscover
  it: a sentence inside `reason` is a parsed field the gate validates as
  non-blank and that travels with its entry under any reordering or mechanical
  rewrite, while a comment is bound by line position alone, is dropped by every
  TOML parser, and would go stale in silence if an entry moved. The verifier
  needing a separate lexical pass is that weakness showing up as cost.
- **One cross-reference inside a `reason` still changes.** A `reason` naming an
  *advisory* by its CVE stays correct, because the CVE remains a valid alias.
  The entry aliased `CVE-2026-101918` names another *entry* —
  "CVE-2026-102274's entry already dispositions", at
  `tools/pip-audit-allowlist.toml:294-295` — and after the re-key no entry
  carries that key. AC2 pins this as the only permitted edit to any `reason`.
- **The advisory lookup is a transcription check, not independent
  corroboration.** `run-pip-audit-gate.py:242` pins `-s pypi`, so the gate reads
  the PyPI Advisory Database — the corpus that mints `PYSEC-` identifiers and
  that `api.osv.dev` re-serves. A mis-published record would therefore look the
  same in both reads. What the lookup does catch is a transcription error in the
  mapping table below, which is the likelier failure and the one a hand-built
  table actually makes.
- **A CVE stays readable in the header, annotated rather than replaced.** An
  earlier draft exempted any sentence carrying a date, which would have exempted
  the `HOW THIS RETIRES` paragraph at `tools/pip-audit-allowlist.toml:50-54` —
  dated 2026-09-30, and naming `CVE-2026-101918` and `CVE-2026-103001` as the
  entries a maintainer should go find. That is the load-bearing forward-looking
  prose, so AC6 instead requires every `CVE-` token to carry the `PYSEC-` id of
  the entry that accepts it. The bound is the *next advisory identifier*: that
  identifier must be the required `id`. A window ending at the next identifier
  of any kind would exclude the very token it demands, and one running to the
  next `CVE-` token would be satisfied by a `PYSEC-` id anywhere in the 36 lines
  between the header's two CVE mentions — including the unrelated `id`-field
  gloss at `:27-30`. Requiring the *next* identifier to be the right one is
  tight, wrap-invariant, and still a pure token scan. A sentence then keeps what
  was true on 2026-09-30 and still resolves for a reader today:
  "CVE-2026-101918 (now PYSEC-2026-4141) needs >=2.15.0".

### Data & schema

Each `[[allow]]` entry keeps all five required fields. Only `id` changes, plus
the comment above it and the one cross-reference. The thirteen identifiers map
as follows, read from a `pip-audit` run and the OSV records on 2026-10-01 — a
point-in-time copy of feed data, and stale if the feed re-keys again:

| New `id` | Alias | `fixed_in` |
| --- | --- | --- |
| `PYSEC-2026-4140` | `CVE-2026-101917` | `2.14.0` |
| `PYSEC-2026-4141` | `CVE-2026-101918` | `2.15.0` |
| `PYSEC-2026-4142` | `CVE-2026-102265` | `2.14.0` |
| `PYSEC-2026-4143` | `CVE-2026-102266` | `2.14.0` |
| `PYSEC-2026-4144` | `CVE-2026-102267` | `2.14.0` |
| `PYSEC-2026-4145` | `CVE-2026-102268` | `2.14.0` |
| `PYSEC-2026-4146` | `CVE-2026-103001` | `none` |
| `PYSEC-2026-4147` | `CVE-2026-102269` | `2.14.0` |
| `PYSEC-2026-4148` | `CVE-2026-102270` | `2.14.0` |
| `PYSEC-2026-4149` | `CVE-2026-102271` | `2.14.0` |
| `PYSEC-2026-4150` | `CVE-2026-102272` | `2.14.0` |
| `PYSEC-2026-4151` | `CVE-2026-102273` | `2.14.0` |
| `PYSEC-2026-4152` | `CVE-2026-102274` | `2.14.0` |

### Failure, edge cases & resilience

The failure this delivery must not produce is a forced row; the stop rule is
`spec.md` § Agent Rules › Always do.

The second failure shape is a silently damaged `reason`. Each one is the
accepted-risk argument itself, so AC2 compares every `reason` to base rather
than trusting that only the intended edit landed.

### Dependencies & integration

This delivery adds none and edits one existing TOML file. The pull request it
ships in also carries the ruff parity fix, which pins `ruff==0.16.10` in
`tools/requirements.txt` — a pin on an already-present dev dependency, not a
new one, and outside this spec's scope per § Rollout.

## Tasks

### T1: Every entry is keyed on the identifier pip-audit reports, and its comment names the CVE

**Depends on:** none

**Touches:** tools/pip-audit-allowlist.toml

**Tests:**
- Each entry's `reason` compares equal to the base-revision entry for the same
  CVE, except the one permitted cross-reference edit. Verifies spec AC2.
- For each entry, the advisory record at its `id` lists exactly one `CVE-`
  alias, is not withdrawn, and that identifier is the one the entry's comment
  names. Verifies spec AC3.
- For each entry, the verifier's line carries the `id`, the comment's CVE and
  the `fix_versions` the advisory record reports, which is the per-entry shape
  AC4 retains. Verifies the AC4 output contract.
- For each entry, `package`, `fixed_in` and `unblocked_when` compare equal to
  the base-revision entry for the same CVE. Verifies spec AC5.
- The file parses under `tomllib` with exactly thirteen `[[allow]]` entries.
  Verifies spec AC7.

**Done when:** the verifier reports thirteen matched entries and zero
disagreements across all five checks above, and its source, run date and
per-entry output are saved for the pull-request description.

### T2: The header names each entry by the identifier that entry carries

**Depends on:** T1

**Touches:** tools/pip-audit-allowlist.toml

**Tests:**
- Above the first `# alias:` comment, every `PYSEC-` token equals the `id` of
  an `[[allow]]` entry, and every `CVE-` token is followed, within the region,
  by at least one further advisory identifier, the first of which is the `id`
  of the entry whose alias comment names that CVE.
  The check spans the whole header, not a line at a time, because the paragraph
  at `tools/pip-audit-allowlist.toml:50-54` puts its identifiers on different
  lines from its date. Verifies spec AC6.
- A sentence above the first `# alias:` comment states that the entries' `id`
  values changed from the CVE identifiers to the identifiers pip-audit now
  reports, and carries an ISO date no earlier than 2026-10-01. Verifies spec
  AC8.

**Approach:**
- T2 follows T1 because its check resolves header identifiers against the set of
  entry `id` values, and T1 establishes that set.

**Done when:** the verifier's AC6 check and its AC8 date-floor check both
pass. AC8's claim itself is read at closeout, which T4 owns.

### T3: The gate passes end to end

**Depends on:** T1, T2

**Touches:** none — this task edits no file.

**Tests:**
- `python3 tools/run-pip-audit-gate.py tools/requirements-sast.txt` against the
  live feed. Verifies spec AC1, and AC7 by the entailment AC7 states.
- `python3 tools/test-run-pip-audit-gate.py`, unchanged. Verifies spec AC9.

**Done when:** the gate exits 0 with no blocking advisory and no retirement
message, the self-test exits 0 with every case passing, `make lint-ruff
lint-mypy` is clean, and `git diff --check` is silent.

### T4: The pull request carries its evidence and both required checks conclude

**Depends on:** T3

**Touches:** none — this task edits no repository file.

**Tests:**
- The pull-request description carries the verifier's source and its complete
  output, including the run date and the per-entry lines. Verifies spec AC4.
- `gate-sast` and the `make build-check` aggregator both conclude successfully
  on the pull request. Branch protection requires both by name, together with
  `gate-main`, `gate-export-boundary` and `gate-credbroker`, per the live
  settings Rollout cites. Verifies spec AC10.
- A reviewer reads the header sentence T2 wrote and confirms it records the
  identifier change rather than restating the existing `id` definition. This is
  AC8's closeout reading, which no script decides.

**Done when:** `gh pr checks` reports both required checks successful, the
description carries the evidence AC4 names, and AC8's reading is recorded.

## Rollout

- **Delivery:** big bang, in PR #1484. Reverting only this delivery's commit
  returns `gate-sast` to the failure `main` shows today and leaves the ruff
  fix and `gate-main` intact; reverting the whole pull request withdraws both
  and re-reds `gate-main` as well. The two halves are independently
  revertible, which is the reason to keep them in separate commits.
- **Infrastructure:** none.
- **External-system integration:** the PyPI advisory feed, read-only, through
  the existing `pip-audit` invocation. The verifier's advisory lookup is
  one-time and disposable, per `## Construction tests`.
- **Deployment sequencing:** this change ships in PR #1484 alongside the ruff
  parity fix, rather than in a pull request of its own. The two are deadlocked
  otherwise. Branch protection requires `make build-check`, `gate-main`,
  `gate-sast`, `gate-export-boundary` and `gate-credbroker`, read from the
  live settings via `gh api repos/{owner}/{repo}/branches/main/protection`;
  note that the comment at `.github/workflows/build-check.yml:1487-1490` names
  only three of those five and is stale against that configuration, which is a
  defect in that comment and not something this delivery changes. A branch
  carrying only the ruff fix still fails `gate-sast` on the stale allowlist,
  and a branch carrying only the re-key still fails `gate-main` on the ruff
  violations. Neither can merge alone. Combining them is the owner's decision,
  taken over an administrative bypass, and it is why a linter pin and a
  guarding-control change share one review surface. #1478, #1479 and #1480
  rebase onto a green `main` after it lands.
- **What the combined PR does to this contract.** The ruff parity fix is a
  separate delivery with its own owner, carried by the first three commits of
  PR #1484 and holding no durable spec, because no risk trigger routed it to
  one. This spec answers for the `tools/pip-audit-allowlist.toml` half only.
  Two consequences follow. `spec.md` § Agent Rules › Ask first bounds this
  delivery's own edits; it does not reach the co-shipped half, and the files
  that half touches are outside this spec's `What Changes` by design rather
  than by omission. And AC10 becomes a joint check: it concludes successfully
  only if both halves are correct, so a failure is attributed to one half
  before it counts against either contract.

## Risks

- **A row that disagrees is forced into the re-key.** Mitigated by `spec.md`
  § Agent Rules › Always do and by AC3's per-entry alias check.
- **The feed re-keys again.** Not mitigated by this delivery, and not a defect
  in it: the gate reports both halves loudly and names the entry, which is how
  this occurrence was found. Recorded as the spec's one assumption.

## Changelog

- 2026-10-01 — Drafted.
- 2026-10-01 — Shipped in PR #1484 (`e512ca462`).
