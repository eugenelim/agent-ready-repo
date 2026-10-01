# Spec: PyJWT advisory id re-key

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0131, ADR-0133
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer opening any pull request sees `gate-sast` pass, with the same
thirteen PyJWT 2.13.0 advisories accepted on the same reachability reasons as
before. Each acceptance is keyed on the identifier pip-audit reports as that
advisory's primary `id`, and still names the CVE the governing ADRs cite.

## What Changes

- The `id` of all thirteen `[[allow]]` entries — from the CVE identifier to the
  `PYSEC-2026-41xx` identifier — in `tools/pip-audit-allowlist.toml`.
- An `# alias: CVE-NNNN-NNNNNN` comment above each entry, so the identifier
  ADR-0131, ADR-0133 and `docs/specs/pip-audit-advisory-allowlist/` cite is
  still readable beside the entry — in the same file.
- One cross-reference inside one entry's `reason`, which names another entry by
  a key that entry no longer carries — in the same file.
- The header paragraphs that introduce the thirteenth entry and describe
  retirement, where each CVE now carries its entry's `PYSEC-` identifier — in
  the same file's leading comment block.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable — the allowlist header is the maintainer-facing account of why the file is not empty and how each entry retires, and it names entries by identifier | `tools/pip-audit-allowlist.toml` leading comment block | Implementing agent | Spec AC6 and AC8 | Every identifier in the header resolves to an entry, by equality or by its annotation, and a dated sentence records the re-key |
| Decision rationale | Not applicable — the header already defines `id` as "the advisory identifier as pip-audit reports it in `id`" (`tools/pip-audit-allowlist.toml:27`), so re-keying applies ADR-0131's existing contract rather than changing it | — | — | — | — |
| User-facing promise | Not applicable — the allowlist is maintainer-facing CI configuration; no shipped pack, CLI surface, or guide describes it | — | — | — | — |
| Release history | Not applicable — this repository publishes no changelog file | — | — | — | — |
| Interface compatibility | Not applicable — no published interface changes; the gate's matching rule and its self-test are untouched | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Stop and surface any entry whose advisory record does not list exactly one
  `CVE-` alias, is withdrawn, reports a `fix_versions` set disagreeing with the
  entry's `fixed_in`, or still reports the CVE as the primary `id`. Each of
  these is also what a degraded feed and a withdrawn advisory look like, so none
  is a row to force into the re-key.
- Confirm an entry's new `id` against a live `pip-audit --format json` run
  before writing it.
- Retain the verifier's source and output as it runs, so AC4's evidence exists
  before the pull request is opened rather than being reconstructed after.

### Ask first

- Before changing any file outside `tools/pip-audit-allowlist.toml` and this
  spec directory. Two carve-outs. The disposable verifier is written outside
  the repository working tree, so it creates no repository file and falls under
  no repository lint. And the ruff parity fix co-shipping in PR #1484 is a
  separate delivery with its own owner, so this rule does not reach the files
  it changes; `plan.md` § Rollout states which half this spec answers for.
- Before altering any `reason` beyond the single cross-reference AC2 permits.
- Before adding, removing, or merging an `[[allow]]` entry.

### Never do

- Never edit `tools/run-pip-audit-gate.py`. The matching rule and the reason
  aliases are deliberately not a match path live at
  `tools/pip-audit-allowlist.toml:27-30`.
- Never rewrite ADR-0131, ADR-0133, or `docs/specs/pip-audit-advisory-allowlist/`
  to the new identifiers. They are decision and delivery history, and the
  re-key does not change the retirement condition any of them records.
- Never rewrite the `semgrep-pyjwt-pin-blocks-every-sca-remediation` entry in
  `workspace.toml`. It is an open backlog item, not history, and the re-key
  does not unblock it: its `source` cites the CVEs as provenance, and those
  remain valid aliases.
- Never add a module, a top-level directory, or a dependency — including a
  committed verification script under `tools/`. The verifier for this delivery
  is disposable, because it checks a one-time data correction and the gate is
  the durable control.

## Testing Strategy

- **The gate's verdict — goal-based.** The gate is the thing under test and it
  already renders the verdict; a unit test around a re-keyed identifier would
  assert what the live run proves. `python3 tools/run-pip-audit-gate.py
  tools/requirements-sast.txt` exercises the real decision seam against the real
  feed, which is the same surface CI runs. Covers AC1, and AC7 follows from
  it: a missing entry makes its advisory blocking, and an extra entry is either
  rejected as a duplicate `(id, package)` pair or trips the retirement branch.
  AC7 states the collection floor because thirteen is the only written form of
  it.
- **Carried-forward content — goal-based, by comparison against base.** Whether
  a field survived the edit unchanged is a diff, not a behaviour, so the check
  is a comparison with the base revision AC5 names. Covers AC2 and AC5.
- **Alias fidelity — goal-based, exercised against the advisory record.**
  Whether an entry's alias comment names the CVE the record lists is a fact
  about the feed, not about this repository, so a read-only lookup per identifier is the
  only check that can observe it. It establishes transcription fidelity only:
  the gate reads the same corpus, so neither read corroborates the other.
  Covers AC3. The gate never reads an alias and the self-test never reads the
  real allowlist, so AC4 retains the verifier's source and output as AC3's only
  reproduction path.
- **Header identifier resolution — goal-based.** Every identifier in AC6's
  region is resolved against the entry it refers to, which is a token scan
  rather than a reading. AC6 is the single statement of that region. Covers
  AC6.
- **The re-key is legible as an event — read by the reviewer at closeout.** AC8
  is a claim about what a sentence says, which no token check decides. It is
  named as a reading so a completion gate does not mistake a green AC6 script
  for covering it.
- **The gate's own decision logic — goal-based, by an unchanged suite.**
  `python3 tools/test-run-pip-audit-gate.py` drives the gate's pure seam against
  synthetic JSON and never reads the real allowlist, so a green run after this
  change is evidence the matching rule is untouched. Covers AC9.
- **CI agreement — goal-based.** AC10 is observed on the pull request, because a
  local pass cannot establish that the gate's CI job agrees.
- **No TDD mode.** This delivery adds no logic with an invariant to compress; it
  corrects stored values in a governed register.
- **No manual QA mode.** The gate is the artifact a user invokes, and AC1
  exercises it end-to-end through its documented command.

## Acceptance Criteria

- [ ] **AC1.** `python3 tools/run-pip-audit-gate.py tools/requirements-sast.txt`
      exits 0.
- [ ] **AC2.** Each `[[allow]]` entry's `reason` is byte-identical to the
      base-revision entry carrying the same CVE, except in the entry whose alias
      comment names `CVE-2026-101918`, where the single reference to
      `CVE-2026-102274` is replaced by the `id` of the entry aliased
      `CVE-2026-102274`.
- [ ] **AC3.** Each `[[allow]]` line is immediately preceded by a line
      matching `# alias: CVE-<digits>-<digits>`, and that CVE is the sole
      `CVE-` alias that the advisory record the PyPI Advisory Database
      publishes for that entry's `id` lists.
- [ ] **AC4.** The pull-request description carries the verifier's source and
      its complete output, including the run date and one line per entry naming
      that entry's `id`, the CVE its comment names, and the fix version the
      advisory record reports.
- [ ] **AC5.** Each `[[allow]]` entry's `package`, `fixed_in` and
      `unblocked_when` are byte-identical to the entry carrying the same CVE at
      base revision `2372e9851`, which is the base revision this spec means
      wherever it names one.
- [ ] **AC6.** Above the first `# alias:` comment in
      `tools/pip-audit-allowlist.toml` — an advisory identifier being any
      `CVE-` or `PYSEC-` token, and no other prefix — every `PYSEC-` token
      equals the `id` of
      an `[[allow]]` entry, and every `CVE-` token is followed, within the
      region, by at least one further advisory identifier, the first of which
      is the `id` of the entry whose alias comment names that CVE.
- [ ] **AC7.** `tools/pip-audit-allowlist.toml` declares exactly thirteen
      `[[allow]]` entries.
- [ ] **AC8.** Above the first `# alias:` comment, a sentence states that the entries'
      `id` values changed from the CVE identifiers to the identifiers pip-audit
      now reports, and carries an ISO date no earlier than 2026-10-01. The
      sentence sits inside AC6's region, so it names no bare advisory
      identifier — not a family pattern such as `PYSEC-2026-41xx`, which equals
      no entry's `id`. "Every entry below is now keyed on the identifier
      pip-audit reports for it, re-keyed from its CVE identifier on
      2026-10-01." satisfies both.
- [ ] **AC9.** `python3 tools/test-run-pip-audit-gate.py` exits 0.
- [ ] **AC10.** On the pull request, the `gate-sast` check and the
      `make build-check` aggregator both conclude successfully.

## Follow-ons

none

## Assumptions

- Technical: the thirteen advisories keep the identifiers this delivery writes —
  the feed re-keyed them once on 2026-10-01 and could do so again, which would
  red the gate exactly as it did this time (settled by: the next `gate-sast` run
  against the live feed).
