# Spec: sender-bounds-its-configuration-read

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0115](../../adr/0115-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the sender's public surface is owned by
  [`jsonl-otlp-exporter`](../jsonl-otlp-exporter/spec.md), which this delivery amends
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Objective

The sender's configuration reader has two ways to fail quietly, both registered
in `workspace.toml`'s `[backlog].open` and neither blocking anything today. This
delivery closes both and corrects the criterion that was supposed to have caught
the first.

**It fails open at the exact ceiling.** A configuration file whose size is
sampled at exactly 65,536 bytes and is then appended to by a concurrent writer
still satisfies the reader's length check, because a read asking for 65,536 bytes
returns exactly that many and matches the sampled size. A valid TOML prefix of an
oversized file is then parsed and accepted, and the complete file is never seen.
Since the `[telemetry]` table admits a closed key set and refuses anything
outside it, a prefix that stops short of the inadmissible key converts a loud
refusal into a silent accept.

**It can hang with no diagnostic.** Both configuration files are opened and read
before the run clock is taken, and `O_NONBLOCK` does not bound `read(2)` on a
regular file. A configuration path on a slow or disconnected network mount blocks
the command indefinitely, and neither existing time bound can reach it: both
start at the first destination resolution, which happens only after every
configuration file has been read. Even `--for` does not help, because the run has
not started.

Of the two answers the registration offered — bound the acquisition, or document
that both paths must be local and require a supervisor timeout — this delivery
bounds it. The documented alternative asks every adopter to guarantee something
the command cannot check: it cannot tell a local path from a network mount, so a
stated requirement it does not enforce fails open in exactly the case the
requirement exists for, and leaves the failure looking like a hung process rather
than a refused configuration.

The correctness framing is deliberate for the first defect. Anyone who can
rewrite a configuration file can already set any endpoint, so the growth race
buys an attacker nothing they did not already have; what it costs is a refusal
the contract promises.

The criterion that governs the size ceiling is also wrong in two small ways, and
both are corrected with the code. It names only `--config`, although the same
code path serves `--user-config` — that flag was added to the neighbouring
confinement criterion on 2026-09-16 and missed here. And it measures "larger than
64 KiB" at sample time, which is precisely the hole: the refusal has to be
decided on the complete file.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the acquisition bound is a new limit an adopter can hit | `packages/jsonl-otlp-exporter/README-pypi.md` | spec owner | The `## Limits` table names the configuration-acquisition bound | AC-0004 green |
| Release history | Applicable — behaviour changes on an unreleased published distribution | `packages/jsonl-otlp-exporter/CHANGELOG.md` | spec owner | Both changes recorded under `## 0.2.0 — unreleased` | AC-0004 green |
| Interface compatibility | Not applicable — the mapping-profile interface is untouched | — | — | — | — |
| Decision rationale | Not applicable — ADR-0115 already places this capability; bounding its own I/O reverses nothing it decided | — | — | — | — |
| Reusable learning | Applicable — the delivery that found these recorded both, and this one records what repairing them taught | `docs/specs/sender-bounds-its-configuration-read/notes/verification-ledger.md` | spec owner | An observed red for every case the plan's `Tests` blocks pin, rather than a count that re-stales when a case is added | Ledger present, with one entry per pinned case |

## Boundaries

### Always do

- Decide a configuration refusal on the bytes the reader actually obtained, not
  on a size sampled at a different instant.
- Give configuration acquisition a bound with its own origin, stated separately
  from the request and run bounds rather than reusing either.
- Keep the standard library the only runtime dependency of the published package.
- Keep every criterion added to `docs/specs/jsonl-otlp-exporter/spec.md`
  capability-scoped: no consumer, product, repository or catalogue named.

### Ask first

- Changing `MAX_CONFIG_BYTES`, or any existing `ConfigRefused` message text — the
  module raises at ten sites and a message change obliges walking all ten.
- Moving where the run clock starts, which AC-0055 pins at the first destination
  resolution.
- Adding a CLI flag or any other new public surface on the published command.

### Never do

- Let a configuration file's valid prefix stand in for the complete file.
- Replace the enforced bound with a documented requirement the command cannot
  check.
- Assert that a bound exists in place of asserting that a blocking read ends.
- Leave a registered defect slug in `[backlog].open` once its defect is repaired.

## Testing Strategy

- **AC-0001 — the exact-ceiling growth race:** TDD. Two arms at exactly
  `MAX_CONFIG_BYTES`, and the pair is the criterion rather than either half. The
  growth arm samples the file at exactly the ceiling and appends to it before the
  read, which is the only size that exercises the defect: at 65,535 the read is
  short of the buffer and at 65,537 the sampled-size check already refuses, so
  neither reaches the branch. The non-growing arm is what stops a build that
  refuses everything at the ceiling from passing the growth arm — without it the
  positive arm is satisfied by an off-by-one that rejects a legal file. The
  growth is driven by appending through a second descriptor between the `fstat`
  and the `read`, which is the concurrent writer the defect describes.
  Each arm is asserted twice, at the two boundaries its clauses live at: a unit
  over the reader for the refusal and the parse, and an invocation of the command
  for the exit status and for the transport seam never being constructed. A unit
  over the reader cannot observe "nothing sent and exit 1", so placing the whole
  criterion there would leave half of it unverified.
  A third arm covers the residue the buffer alone leaves: a read that returns
  exactly the sampled size while the file has grown underneath it. It is driven
  by a substituted read that returns a ceiling-length prefix of a file that is
  already longer, which is the shape a network or FUSE mount produces and a local
  filesystem does not.
- **AC-0002 — the configuration-acquisition bound:** TDD, unit, driven through a
  substituted call that blocks until the test releases it — one case substituting
  the open and one substituting the read, because they are separate syscalls and a
  build that moves only the read onto an abandonable worker passes a read-only
  case while an unresponsive mount still hangs it at the open. The assertion is
  that the call returns with its refusal, not that a deadline was computed: a
  build that computes the deadline correctly and then issues an unabandonable
  call satisfies every assertion about the bound's value and still hangs forever,
  so a test that reads the constant proves nothing the defect does not already
  satisfy. Each substituted call blocks on an event the test sets in teardown, so
  no worker outlives the case.
- **AC-0003 — the amended capability contract:** goal-based check.
  `lint-contract-item-alignment.py` over `docs/specs/jsonl-otlp-exporter/` exits
  0, which is what proves the new criterion is named by an owning task and sits
  in exactly one verification group; a read of the two criteria confirms the
  scope and origin wording the lint cannot see.
- **AC-0004 — published surface and registration:** goal-based check over the
  authored files: a `grep` for each slug in `workspace.toml`, and for the
  acquisition bound in the README limits table and the unreleased changelog
  section.
- **Whole-package regression:** goal-based check, owned by T4's completion gate
  so it has a task that gates it rather than living only here. The package suite
  and `tests/roster/test_telemetry_sender_owns_its_configuration.py` are run
  unfiltered, and `packages/jsonl-otlp-exporter/tests/wiring_sweep.py` is run
  against the merge base **before** it is run against the change, so a
  pre-existing survivor is not mistaken for a new one. The bar is no new
  survivor, not zero survivors.

## Acceptance Criteria

- [x] **AC-0001.** A configuration file sampled at exactly the 64 KiB ceiling and
  appended to before its bytes are read is refused, with nothing sent and exit 1,
  whether or not the read itself returns the extra bytes; and a configuration file
  whose complete content is exactly 64 KiB and is not appended to is accepted and
  parsed. These are one criterion: the accepted side is the only thing that
  distinguishes the repair from an off-by-one that refuses every file at the
  ceiling, and every side is the same predicate — the refusal is decided on the
  file the reader actually obtained, proven unchanged across the read — substituted
  at each side of the boundary.
- [x] **AC-0002.** Configuration acquisition that blocks ends the run with a
  refusal naming the bound, rather than blocking the command. The subject is the
  whole acquisition path — opening each configuration file, proving what the
  descriptor names, and reading it — under one deadline established before the
  first file is opened, not the read alone: `open(2)` on an unresponsive mount
  blocks before any flag applies, so a build that bounds only the read satisfies
  a read-shaped criterion and still hangs on the case this delivery exists to
  remove. Asserted by substituting, separately, an open and a read that do not
  return within the bound, and observing the call return each time; a build whose
  bound is computed but never enforced fails this and passes any assertion about
  the bound's value.
- [x] **AC-0003.** `docs/specs/jsonl-otlp-exporter/spec.md` states its
  configuration-size refusal for every configuration-file argument the command
  accepts and decides it on the complete file, and carries a criterion bounding
  configuration acquisition at **5 seconds** from the start of acquisition, with
  that origin stated and distinguished from the request and run bounds. This is
  the one canonical statement of the value in this delivery's contract: AC-0002
  and AC-0004 refer to the bound and do not repeat the number, so there is one
  place for it to be wrong. `lint-contract-item-alignment.py` over that spec
  directory exits 0.
- [x] **AC-0004.** `packages/jsonl-otlp-exporter/README-pypi.md`'s `## Limits`
  table names the configuration-acquisition bound, the `## 0.2.0 — unreleased`
  changelog section records both behaviour changes, and neither
  `pre-existing-config-exact-ceiling-growth-race` nor
  `pre-existing-config-io-outside-every-deadline` remains in `workspace.toml`'s
  `[backlog].open`.

## Follow-ons

- spec owner: `sender-cannot-explain-its-effective-configuration` in
  `workspace.toml`'s `[backlog].open` — a diagnostic mode that reports the
  resolved configuration is new public CLI surface and stays registered, not
  built here.

## Assumptions

- Technical: `os.read` is one `read(2)` and may return fewer bytes than asked
  for, so asking for `MAX_CONFIG_BYTES + 1` detects growth past the ceiling in
  every case where the read is not short, and a size re-sampled on the same
  descriptor after the read detects the growth a short read would otherwise hide.
  Measured on this machine 2026-09-17 over a file armed at exactly 65,536 bytes
  and grown by 1, 8, 4,096 and 200,000 bytes between the `fstat` and the `read`:
  the read returned 65,537 bytes in all four, and the re-sampled size differed
  from the sampled size in all four, so the two checks fire independently rather
  than one carrying the other (source: probe run, and
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py` for the checks it
  joins).
- Technical: a size unchanged across the read establishes that the bytes obtained
  are the whole file as of the read; it does not establish that the content was
  not rewritten in place at the same length. That is a different question from the
  registered defect, which is growth, and no criterion here claims it (source:
  the registered entry in `workspace.toml`'s `[backlog].open`).
- Technical: a blocking syscall that accepts no timeout is already bounded in
  this package by running it on an abandonable daemon worker and joining with a
  deadline — the same shape `getaddrinfo` needed (source:
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/transport.py` `_resolve_bounded`).
- Technical: `packages/jsonl-otlp-exporter/` is not a curation-guard protected
  tree, so no `Engine-Change-RFC:` trailer is required (source:
  `workspace.toml` registration and the repository's guard configuration).
- Process: `docs/CONVENTIONS.md` no longer exists; commit format and PR shape
  come from `AGENTS.md` (source: commit 813f533f1).
- Process: `lint-contract-item-alignment.py` resolves a criterion reference only
  inside the spec directory it is run over, so this delivery's references to the
  capability contract's identifiers report as unresolved here. That is the same
  result `telemetry-sender-owns-its-configuration` carries for the same reason;
  AC-0003 therefore pins the lint over `docs/specs/jsonl-otlp-exporter`, which is
  the directory the new criterion actually lives in (source:
  `.claude/skills/new-spec/scripts/lint-contract-item-alignment.py:91` and a run
  over both spec directories, 2026-09-17).
- Product: bounding configuration acquisition, rather than documenting a
  locality requirement, is the chosen answer of the two the registration offered
  (source: user confirmation 2026-09-17).
