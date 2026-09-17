# Verification ledger — telemetry-sender-owns-its-configuration

Execution observations for this delivery. The spec and plan are pinned; this
file is where what actually happened is recorded.

## T1 — the sender's contract admits a second configuration scope

**Landed 2026-09-16.** `docs/specs/jsonl-otlp-exporter/spec.md` amended:
AC-0002 gained a fourth endpoint source, AC-0007 a four-source `service.name`
precedence, AC-0033 a fourth refusable file argument, AC-0062 coverage of
`--user-config` plus reparse-point and hard-link rejection. AC-0074, AC-0075 and
AC-0076 added for the per-setting merge, the closed key set with its
scope-naming refusal, and the unconditional read. VI-0014 added; VI-0001 and
VI-0006 extended.

### Declared deviation: T1 wrote outside its `Touches`

T1 declares `Touches: docs/specs/jsonl-otlp-exporter/spec.md` and this ledger.
It also edited `docs/specs/jsonl-otlp-exporter/plan.md`, adding task T9.

The edit was forced by a gate, not chosen. `lint-contract-item-alignment.py`
**exits 1** when an acceptance criterion is named by no task entry in the plan
that serves its spec, so AC-0074, AC-0075 and AC-0076 could not be added to that
contract without a task owning them. Recorded rather than absorbed silently
because `Touches` is pinned plan content.

The obligation `Touches` serves did not fire: `loop-cohort schedule` reads it to
predict per-wave disjointness before parallel dispatch, and T1 is alone in wave
1 and was run sequentially in-session, so no overlap prediction depended on the
missing path.

### Regression introduced and repaired inside T1

The first version of T9 cited `VI-0001`, `VI-0002`, `VI-0006` and `VI-0014` by
identifier. That took the alignment lint from 3 findings to 4 and kept exit 1,
under a different rule — *"a verification item's identifier is its own, never
derived from what it serves"* — because every `VI-00NN` in this spec collides
with the `AC-00NN` series.

Triaged as **mine, not pre-existing**: `git show HEAD:docs/specs/jsonl-otlp-exporter/plan.md | grep -c "VI-"`
returns `0`, so the plan carried no VI reference before this task and the rule
could not previously fire. Repaired by referring to the spec's Testing Strategy
by name instead of by identifier, which keeps the one-home intent without
minting a colliding reference.

**After:** `lint-contract-item-alignment.py docs/specs/jsonl-otlp-exporter` —
0 findings, exit 0.

## T6 — the answered shaping question is recorded

**Landed 2026-09-16.** `docs/product/intents/loop-telemetry-contract-corrections.md`
records its second unresolved question as answered by relocation rather than by
amendment: the undeliverable-setting refusal is now AC-0075 in the sender's live
contract, so the frozen-task obstacle that sank the withdrawn AC-0055 never
applied. AC-0031's enumeration is untouched and the register entry stays open —
re-pointed, not retired, because a partially answered item read as closed is the
failure that entry exists to prevent.

## T2 — the sender resolves both scopes and refuses a key it cannot deliver

**Landed 2026-09-16.** `config.py` gained `resolve_telemetry` and the two
descriptor guards; `cli.py` gained `--user-config` and calls the resolver
unconditionally before endpoint precedence. `resolve_endpoint` and
`run_unconfigured_check` now take merged settings rather than a path, which is
what removes the conditional read rather than relocating it.

### Mutation proof — 9 mutations, 9 killed

Run by applying each mutation to the shipped module, running the named tests,
and restoring. A survivor is a control that cannot fail.

| # | Mutation | Verdict |
| --- | --- | --- |
| M1 | read the files only when neither endpoint variable is set | killed |
| M2 | select one whole file instead of merging per setting | killed |
| M3 | let the user scope win the merge | killed |
| M4 | report the refusal from the merged view, naming one scope | killed |
| M5 | drop `!r` from the key in the bad-value message | killed |
| M6 | drop `!r` from the path in the refusal message | killed |
| M7 | remove the hard-link guard | killed |
| M8 | let a configured `service_name` override the `--service-name` flag | killed |
| M9 | accept a non-table `telemetry` value as absent | killed |

### M5 survived the first run, and the reason is the finding

The first escaping case gave its hostile key a **valid** value, so it reached
the undeliverable-key message — which escapes through `repr(name)` — and never
reached the non-empty-string message, a different format string that M5 mutates.
The control read as covering key escaping while leaving one of the two sites
that print a key entirely unexercised.

Repaired by adding a case with a hostile key **and** an empty value, which is
the only input that reaches the second message. Re-run: M5 killed. Recorded
because the surviving mutation is the only thing that distinguished a control
covering one site from one covering both; both cases pass against the correct
implementation, so nothing else in the suite could tell them apart.

### Gates at T2

- `pytest packages/jsonl-otlp-exporter/ -q` — 386 passed.
- `make lint-ruff lint-mypy` — clean, 149 source files.
- `ruff check .` — clean.
- `tools/test-lint-pack-test-boundary.py` — ok, 154 cases.
- `wiring_sweep.py` deferred to the pre-PR gate: it takes ~12 minutes and its
  bar is "no new survivor", which is only meaningful once every module this
  delivery touches is final.

## T7 — the sender's published surface

**Landed 2026-09-16.** `README-pypi.md` now lists four endpoint sources, both
configuration flags, the per-setting merge, the closed key set, and the 64 KiB
ceiling applied to `--user-config`. `CHANGELOG.md` gained entries for the flag,
the refusal and the descriptor guards.

### Declared deviation: no version bump

T7 says to bump `pyproject.toml` because the flag is added CLI surface. It was
not bumped. `packages/jsonl-otlp-exporter/CHANGELOG.md` heads its only section
`## 0.1.0 — unreleased`, and `git tag --list '*jsonl*' '*otlp*'` returns nothing,
so 0.1.0 has never been published. Bumping to 0.2.0 would assert a released
0.1.0 that an installer could differentiate from, and there is none; the changes
belong in the unreleased section, which is where they went.

This also softens a Product assumption in the spec, which called the unknown-key
refusal "a behaviour change to a published CLI". It is a behaviour change to an
unpublished one, so it breaks no installed adopter. The decision to refuse rather
than warn is unaffected — it was taken for cross-version safety, which is about
future pairings, not current ones. The assumption is working material and was
corrected in place.

## T3 — the documented invocation needs no package dependency

**Landed 2026-09-16.** Both Python blocks in
`guides/core/how-to/export-loop-telemetry.md` build five paths from a repository
root and a home directory and pass both layout files. Imported top-level modules
across both blocks: `pathlib`, `shlex`, `subprocess` — all standard library. The
stale sentence claiming `resolved.arguments` "is already a list" is gone with the
resolver it described. `docs/architecture/telemetry.md` § 5.3 is retitled and
describes the shipped two-flag mechanism in the present tense.

### Mutation proof — 5 mutations, 5 killed

| # | Mutation | Verdict |
| --- | --- | --- |
| G1 | the guide re-imports `agentbundle.telemetry_layout` | killed |
| G2 | the guide reaches the package through `__import__` | killed |
| G3 | `--user-config` points at the repository file | killed |
| G4 | `--input` points somewhere other than `.loop-run/events.jsonl` | killed |
| G5 | one of the two invocation blocks stops being Python | killed |

G2 is the one that justifies the round-4 repair. The criterion originally paired
a lexical blacklist of dynamic-import spellings with the execution check; the
blacklist was deleted rather than extended, on the argument that an alias or
`exec` defeats it and the execution already carries the claim. G2 applies exactly
the evasion the blacklist was meant to catch and the execution control kills it,
so the deletion removed redundancy rather than coverage.

G5 is the floor: every other assertion here is quantified over the guide's
blocks and is vacuously true of a guide with none.

### Gates at T3 and T7

- `pytest tests/roster/test_loop_telemetry_disclosure_contract.py -q` — 13
  passed, so AC-0020's heading and literals and AC-0042's reserved exit-code
  band survived the rewrite.
- `pytest tests/roster/test_telemetry_sender_owns_its_configuration.py -q` — 5
  passed.

## T4 — `agentbundle` ships no telemetry-layout module

**Landed 2026-09-16.** Deleted `agentbundle/telemetry_layout.py`, its unit test,
and the two orphaned fixtures under `tests/fixtures/telemetry-layout/`.
`pyproject.toml` and `version.py` both moved to `0.47.0`. A topmost
`## [0.47.0]` release heading carries a `### Removed` entry. `README-pypi.md`
gained a `What's new in 0.47.0` section and its `0.45.0` section no longer
advertises a capability the package does not have.

`docs/product/changelog.md:187` was checked and **left alone**: it sits under
`## [agentbundle][0.45.0] — 2026-09-14`, a released heading, so it records what
that release shipped and is still true of it.

### An editable install resurrected the deleted module

AC-0002's first implementation used `importlib.util.find_spec("agentbundle.telemetry_layout")`
and **failed after a correct deletion**. Measured 2026-09-16:

- `agentbundle.__path__` holds only this worktree, so `PathFinder` correctly
  misses the deleted submodule.
- `pip show agentbundle` reports an editable install whose project location is
  `/Users/.../orca/agent-ready-repo` — the **main checkout**, not this worktree.
- That editable finder is *appended* to `sys.meta_path`, so `PathFinder` runs
  first, misses, and the appended finder then resolves
  `agentbundle.telemetry_layout` from the other checkout.

So the bare call answers about the interpreter, not about the distribution under
test: it reported a module this repository does not ship. The control was scoped
to `PathFinder.find_spec("telemetry_layout", [<repo>/packages/agentbundle/agentbundle])`,
which asks what *this* tree provides and is independent of which checkout an
editable install happens to point at. The tombstone argument is unaffected —
`PathFinder` still resolves without executing, and T4-M1 proves it.

The environment itself was left alone. Repointing the editable install is a
global change shared with the main checkout and any other worktree session, so
it is not this delivery's to make.

**Scope note:** the same fallback means a bare `import agentbundle` outside
pytest resolves to the main checkout. Runs under pytest are unaffected —
`pyproject.toml`'s `pythonpath` puts this worktree first, and both
`agentbundle` and `jsonl_otlp_exporter` were confirmed resolving here.

### Mutation proof — 4 mutations, 4 killed

| # | Mutation | Verdict |
| --- | --- | --- |
| T4-M1 | a tombstone module raising `ModuleNotFoundError` occupies the path | killed |
| T4-M2 | `README-pypi.md` re-advertises the module | killed |
| T4-M3 | a current-version `### Added` entry still advertises it | killed |
| T4-M4 | the changelog records no removal | killed |

T4-M3 is the one the round-4 review predicted: it is exactly the live stale
claim that the widened "beneath any version heading" exemption would have
admitted, and the two-context rule catches it.

### Gates at T4

- `pytest packages/agentbundle/tests/unit/test_version.py -q` — 5 passed, which
  is what already pins `CLI_VERSION` against `pyproject.toml`; no second version
  assertion was added.
- `ruff check .` — clean, after removing two imports the deleted draft left in
  the roster file. `tests/AGENTS.md` warns that the repository lint targets do
  not cover this, and they did not: `make lint-ruff` was clean while `ruff
  check .` reported both.
- `make lint-ruff lint-mypy` — clean, 148 source files (down one with the
  module deleted).

## T5 — the frozen consumer criteria gain their first control, and CI runs it

**Landed 2026-09-16.** One roster file,
`tests/roster/test_telemetry_sender_owns_its_configuration.py`, carrying
AC-0001 through AC-0004 and the first mechanical control over
`loop-telemetry-export`'s AC-0041, AC-0043 and AC-0044. The control takes the
argv the guide itself produces, copies this repository's real work-loop profile
to the path the guide names, and feeds both to the real sender — so the guide,
the profile and the sender are checked against one another rather than each
against a restatement in the test.

### Registration: three obligations, all discharged

- `build-check.yml` — added to the existing `pytest loop-telemetry contracts
  (roster-owned)` step rather than a new one, and its comment updated. Same
  subject, same disposition, one fewer entry to keep in step.
- `tools/lint-ci-parity.py` — **no new entry needed**, because extending an
  existing step reuses its `LOCAL("test-after-build-check")` disposition.
  `lint-ci-parity` confirms: 89 steps, all dispositioned.
- `.workspace-prune-protected.toml` — added
  `docs/specs/telemetry-sender-owns-its-configuration`. This was **not**
  anticipated as needed and was caught by
  `test_protected_manifest_covers_every_literal_roster_spec_dependency`, which
  re-derives the list rather than trusting it. The roster file names the spec
  directory in a docstring, and the deriver's reach is literal paths wherever
  they appear.

### Mutation proof — 5 mutations, 5 killed

| # | Mutation | Verdict |
| --- | --- | --- |
| T5-M1 | the two layout flags are swapped in the guide | killed |
| T5-M2 | the user scope wins the merge | killed |
| T5-M3 | the guide names the wrong `--input` | killed |
| T5-M4 | the guide names the wrong `--profile` | killed |
| T5-M5 | a setting the repository omits is dropped rather than falling through | killed |

T5-M1 is the one that justifies the three-arm shape. A disjoint fixture — each
file declaring a setting the other omits — proves both arrive and stays green
under exactly this swap, because swapping two files that declare different keys
produces the same merged result. Only the conflicting arm distinguishes them,
and AC-0041 claims precedence rather than arrival.

### One assertion was wrong before it was right

`timeUnixNano` was first written as `1757742744000000000`, which failed. The
correct value was **computed independently** —
`datetime(2026, 9, 13, 5, 52, 24, tzinfo=timezone.utc)` → `1789278744000000000` —
and only then compared with what the encoder emitted, rather than copying the
emitted value into the assertion. Copying it would have made the case a
tautology that ratifies whatever the encoder does.

### Release surface: two more homes than the bump touched

The version bump reddened two roster tests that the package-level gates passed:

- `test_t4_repair_determinism_projection_and_release_surface` requires
  `docs/product/changelog.md` to carry a topmost `[agentbundle][<version>]`
  heading matching `pyproject.toml`.
- `test_release_metadata_moves_together_for_okf_catalogue_discovery` pins the
  current version as a **literal** (`expected = "0.46.1"`), so every bump must
  edit that test.

Adding the product-changelog entry then broke a third invariant:
`test_the_core_release_heading_sits_directly_beneath_unreleased`. The new
`[agentbundle][0.47.0]` section had been placed between `## [Unreleased]` and
`## [core][2.26.8]`; it belongs below the core release block, as the topmost
*agentbundle* heading rather than the topmost heading overall.

So one bump has five homes: `pyproject.toml`, `version.py`, the package
changelog, the product changelog (in a constrained position), and a version
literal inside a roster test.

### Wiring sweep — no new survivor, and the brief's count corrected

`python3 packages/jsonl-otlp-exporter/tests/wiring_sweep.py`: 45 wirings
mutated, **3 survived** plus 1 hung.

| Survivor | In my diff? |
| --- | --- |
| `profile.py:65` `frozen=True` | no — named pre-existing in the brief |
| `transport.py:109` `frozen=True` | no — named pre-existing in the brief |
| `cli.py:184` `size_at_open=info.st_size` | **no** — see below |
| `transport.py:526` `daemon=True` (HUNG) | no — `transport.py` untouched |

The brief named two pre-existing survivors; there are three, plus one that
hangs. `cli.py:184` is in a file this delivery changes, so it was checked rather
than assumed: the line is byte-identical at `HEAD` (it sat at `:167` and moved
only because lines were added above it), `git diff HEAD` does not contain it,
and no test in the package names `size_at_open`. It was uncovered before this
change and is uncovered after it. The bar — add no new survivor — holds.

### Gates at T5

- `pytest tests/roster/ -q` — 1605 passed, 6 skipped, 46 subtests, 4m27s.
- `pytest packages/jsonl-otlp-exporter/ -q` — 401 passed.
- `pytest tests/conformance/ -q` — 61 passed.
- `make lint-ruff lint-mypy` — clean, 148 source files. `ruff check .` — clean.
- `tools/test-lint-pack-test-boundary.py` — ok, 154 cases.
- `tools/lint-ci-parity.py` — ok, 89 steps all dispositioned.
- `lint-spec-status.py --root .` — clean.

## Post-gates review round 1 — adversarial (Codex `gpt-5.6-sol`, read-only)

Four blockers, three concerns. All verified against the tree; six repaired, one
recorded as a disposition rather than a code change. Round recorded as
`round=1 retry=1`, seven fingerprints.

**Ordering deviation:** the fixes were applied before `findings-remain` fired,
not after. The state machine is unaffected — the transition is legal from
`CODE-REVIEW` either way — but the skill's sequence is transition first, then
repair, so the round's audit entry is written after the work it describes.
Recorded rather than smoothed over.

### B1 — the reparse-point guard had no control (sustained)

The Testing Strategy promised reparse-point and hard-link cases "of their own";
only the hard-link case existed, and the nine mutations included no reparse
mutation. The branch shipped unexercised.

No POSIX filesystem sets `FILE_ATTRIBUTE_REPARSE_POINT`, so the control
substitutes the `os.fstat` result the reader inspects, which tests the guard
rather than the platform. A **paired negative** case was added with it — an
ordinary file must still be accepted — because a build raising unconditionally in
that branch passes the positive case alone. Both mutations kill.

### B2 — the unconditional-read control could not see a one-sided read (sustained)

Every arm placed the inadmissible key in the repository file, so a build that
always validates `--config` but skips `--user-config` once an endpoint is already
resolved passed all four. That regression is *newly possible* precisely because
this delivery adds the second flag, so it is the shortcut most worth excluding.

I disputed nothing here: the earlier M1 mutation made **both** reads conditional,
which the one-axis test does catch, and that is why it read as sufficient. The
control is now parameterized over both axes — four endpoint sources × two scopes,
eight combinations. R2-M3 applies the one-sided shortcut exactly and kills.

### B3 — AC-0002's observable was substituted, not amended (sustained)

The criterion names `importlib.util.find_spec`; the control had used
`PathFinder.find_spec` scoped to the package directory. The reviewer accepted the
reason (an editable install pointing at a sibling checkout) and rejected the
remedy: an execution note cannot replace an accepted criterion's observable.
Correct, and the cheaper fix was available — run the criterion's own call in a
subprocess started with **`-S`**, with `PYTHONPATH` supplying only this tree. Site
processing is skipped, so no editable finder is installed, and
`find_spec("agentbundle.telemetry_layout")` is `None` as written. No amendment
needed, and the control is now environment-independent rather than merely
differently-scoped.

### B4 — T7's pinned version bump was omitted (sustained)

The ledger had justified skipping it because `0.1.0` is unreleased. The reviewer's
objection stands on authority rather than on facts: `Tests` and `Done when` are
pinned plan content, and an execution ledger cannot waive them. The fact was also
not load-bearing — nothing was ever published as `0.1.0`, so the version number
of a first release is free. Bumped to `0.2.0`, changelog heading moved with it,
and the entry now says why no release carries the narrower surface. The earlier
reasoning is left above rather than deleted: it was overridden by the pin, not
shown to be wrong.

### C2 — only the first documented block was asserted (sustained)

The guide's second block prints the command rather than running it, so the
recording stub never saw it and a wrong path there alone would have shipped. Its
printed line is shell-quoted, so it is split back with `shlex` and compared
against the block that executes. R2-M5 mutates only the printed block and kills.

### C3 — the AC-0044 control used a hand-authored line (sustained)

AC-0044 says "a line the engine actually emitted". The fixture was an inline
literal, so the coverage claim was wider than what ran. It now reads the first
line of `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl` whose
`result` the profile maps — a recorded engine line, 17 in the corpus.

**The repair introduced a tautology, and the mutation caught it.** The expected
severity was first derived from the profile's own `severity_map`, which the
encoder also reads — so R2-M6, changing `failure = 17` to `13`, moved both sides
together and **survived**. The expected level is now written in the test as a
literal, which is its only written form there; `loop-telemetry-export`'s AC-0040
pins the map to exactly `success = 9` and `failure = 17`, so these are contract
values and a change to them is a contract change. `identity` is still read from
the profile, because it selects *which* fields to look for rather than supplying
the value compared — the comparison is presence among the emitted attributes,
which the profile cannot satisfy on the encoder's behalf. R2-M6 now kills.

The timestamp assertion was left deriving from the corpus record via
`datetime.fromisoformat`, which is a genuinely independent implementation of the
encoder's own RFC 3339 parse rather than a read of its output.

### C1 — the intent and register edits have no owning task (disposition, not a repair)

`docs/product/intents/catalogue-level-telemetry-endpoint-default.md`, the
`credential-pack-defaults-projection.md` backlink and the `workspace.toml`
register entry are semantic shaping changes with no task in the plan and no
`Bundled fixes:` declaration. The reviewer is right about the plan.

They are nonetheless **accepted intent, not scope creep**: the owner asked for
them explicitly — "log #3 as a follow-on but just complete the work right now" —
and the approved spec's `Follow-ons` section references the new intent by path,
so the contract that was approved already depends on the file existing. What
went wrong is that the plan was authored after that instruction and failed to
carry a task for it, which is a plan-authoring defect rather than unauthorised
work.

Not repaired here, because the two available remedies are both worse than the
disclosure: removing the files would break the approved spec's `Follow-ons`
reference, and amending the plan to add a task costs a re-approval cycle for work
the owner has already authorised in writing. Surfaced to the owner instead.

### Repair-round mutations — 6 applied, 6 killed

| # | Mutation | Verdict |
| --- | --- | --- |
| R2-M1 | the reparse guard is removed | killed |
| R2-M2 | the reparse branch raises unconditionally | killed |
| R2-M3 | `--user-config` is read only when no environment endpoint is set | killed |
| R2-M4 | a tombstone module occupies the retired path | killed |
| R2-M5 | only the printed block names a wrong path | killed |
| R2-M6 | the profile maps the corpus result to another level | killed (after the tautology was removed) |

## Post-gates review round 2 — adversarial, bounded to the repairs

`Clean — ready to commit.` on blockers and concerns, with one nit: the C3 repair
left a companion comment still crediting the profile's `severity_map` for the
expected severity, which the code no longer does. Corrected — a comment that
contradicts the assertion beside it is worse than none. Effective severity stayed
Nit: one comment, one file, no behaviour, architecture or dependency change.

## Post-gates review round 2 — security (Codex `gpt-5.6-sol`, read-only)

Boundary-routed depth: `path-and-file`, `injection`, `exceptional-conditions`,
plus an open STRIDE + LINDDUN pass. **No blockers.** Two concerns and one nit.

Traces it confirmed rather than assumed, all still holding after the merge moved
where the endpoint comes from: non-loopback destinations still require HTTPS and
plaintext is admitted only when every resolved address is loopback with the
connection pinned to a checked address; `ssl.create_default_context()` unchanged;
redirects refused rather than followed; endpoint and redirect diagnostics still
omit user-info, query, fragment and C0/C1 controls. Bounds: 64 KiB per file, two
files, 128 KiB total; no unbounded read, retry or allocation added.

### The guard-loss accounting T2 promised (the nit — sustained)

T2's Approach said three guards "must still be accounted for in the ledger" and
the ledger had recorded only the two carried over. The full comparison against
`file_safety.read_confined_regular_file`, which the retired resolver used:

| Guard the old reader applied | Disposition |
| --- | --- |
| Final-leaf no-follow open; non-blocking open; descriptor regular-file proof; reparse-point rejection; hard-link rejection; descriptor size check; UTF-8/TOML parse | **Retained.** The new reader also adds an explicit short-read refusal the old one lacked. |
| Absolute `repo_root`/`user_root`, and `agentbundle-layout.toml` derived from each root | **Accepted.** The sender's contract forbids deriving a filename, so the caller must name the files. |
| Canonical root confinement and root validation, rejecting link-like or non-directory roots and paths outside the root | **Accepted.** AC-0062 states the reason: a configuration file legitimately lives outside any data root. |
| Dot-segment rejection and descriptor-relative no-follow traversal of every parent, including parent reparse-point rejection | **Accepted consequence** of a path-valued API with no root. The caller now controls the parent chain. |
| Fallback canonicalisation of the leaf under the resolved root | **Accepted** with the confinement loss. |
| Pre-open `lstat`/`stat` then post-open device/inode identity comparison | **Acceptable.** The new reader makes no pathname-based decision before opening; it validates the object `open` returned, so there is no earlier decision to confirm. |
| Duplicate regular-file / reparse / link-count checks before *and* after opening | **Acceptable.** The descriptor-side checks survive; the pre-open copy existed to protect a prior pathname decision that no longer happens. |
| Explicit `O_CLOEXEC` | **Acceptable.** Python descriptors are non-inheritable by default and this one closes before the transport is constructed. |
| Caller-supplied `max_bytes` validation | **Not applicable.** The bound is a private constant, not an argument. |
| Reading `max_bytes + 1` to detect growth past the sampled size | **Defect — registered, not fixed.** See below. |

What the caller now controls that it did not: the exact two paths, including
filenames, relative paths, `..`, absolute locations and symlinked parents. Worst
outcome under a *more-privileged* wrapper is selecting any process-readable TOML
and using its admitted values to redirect telemetry or cause denial. Under the
documented same-user invocation the caller already controls every endpoint
source, so the loss is expressly accepted rather than newly created.

### Concern 1 — the exact-ceiling growth race (pre-existing, registered)

A file sampled at exactly 65,536 bytes and then appended to still satisfies
`len(raw) == info.st_size`, so a valid prefix of an oversized file parses and the
complete file is never validated. **Triaged as pre-existing:** `git diff --cached
HEAD` over `config.py` contains no `+` line touching the size or read block.

My change does raise its consequence — with AC-0075 refusing an inadmissible key,
a prefix that omits the bad key converts a refusal into a silent accept — which is
why it is registered rather than merely noted. Not repaired here: changing the
read is a behaviour change on a shipped path, which the bundled-fixes tiers
exclude. Registered as `pre-existing-config-exact-ceiling-growth-race`.

### Concern 2 — eight refusal messages printed a raw path (sustained, fixed)

The unknown-key message escaped its path; the bad-value, non-table, reparse,
hard-link, size, short-read, parse and open-error messages did not, and
`cli.main` prints all of them to stderr. Four of those sites are new in this
diff.

**This is the same blind spot as M5, in a second place.** The escaping control
covered one of ten sites and read as covering "path escaping". Fixed by routing
every path in the module through one `_shown` helper, and the control now walks
**every** refusal kind — seven parameterized cases — rather than one
representative. Each site was then mutated back individually: 7 mutations, 7
killed, so no case is carrying another's coverage.

The lesson is recorded rather than the incident: a per-site judgement about where
hostile input is likely degrades into exactly this. One renderer, applied
everywhere, with a case per site.

## Process deviation: implementer dispatch was skipped

`loop-cohort schedule` printed its dispatch instruction verbatim: *"send each
task above to one implementer subagent, one at a time, when that agent is
installed; otherwise run them yourself and note the degradation in the final
summary."* The `implementer` agent **was** installed, so the fallback branch did
not apply. All seven tasks were nonetheless executed by the controller, and the
degradation was not noted until the owner asked why.

Cause, not excuse: an earlier owner instruction routed *reviewer* rounds to Codex
rather than Claude subagents, to keep reviewer cost off the Claude budget. That
instruction is scoped to reviewers — its own record says "Claude `Agent`
subagents remain right for work the user asked for directly" — and it was
over-applied to implementation without checking work-loop's EXECUTE contract,
which owns dispatch and says otherwise.

What it cost, and what it did not. The work-loop assigns the controller
scheduling, state transitions, gates, review, retry and closeout regardless, and
all of those ran: five waves, every transition recorded, gates green at each
wave, three review rounds with 34 findings and 29 mutations. What was lost is the
implementer envelope's independence — a task implemented and then reviewed by the
same context, rather than implemented by a worker and reviewed by the
controller. Two of the three review rounds found controls that could not fail,
which is the failure class that separation of implementer and reviewer exists to
reduce.

No remediation by rework: every task is complete, gated and reviewed, and
re-running them through implementers would change no artifact. Recorded here so
the run's evidence is not read as having had an envelope it did not.

## Manual QA — the real built artifact, not `cli.main`

Every assertion above runs `cli.main` in-process. The finish checklist requires
the shipped artifact exercised through its documented happy path, so the wheel
was built, installed into a fresh virtual environment, and the **console script**
driven against a real HTTP receiver on `127.0.0.1:4318`. Measured 2026-09-16.

`jsonl-otlp-export --version` → `0.2.0`. `--help` lists both `--config` and
`--user-config`.

### 1. The documented invocation, with the configuration genuinely split

Repository layout declared **only** `service_name`; user layout declared **only**
`endpoint`. This is the case no single `--config` file can express, and the one
the retired resolver existed to work around.

```
EXIT=0
POST path      : /v1/logs
Content-Type   : application/json
service.name   : ['manual-qa-from-repo']      <- repository scope
destination    : 127.0.0.1:4318               <- user scope
log records    : 1
timeUnixNano   : 1789271062000000000
severityNumber : 17
attribute keys : ['awaiting_input', 'budgets', 'event', 'from', 'phase_s',
                  'phase_started_at', 'run_id', 'seq', 'spec', 'to', 'waived']
```

The input was line 2 of `packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl`
— a recorded engine line, not an authored one. Both settings reached the wire
from different files, which is AC-0041's substance observed on a real request
rather than through a seam.

### 2. The ordering trap, on the shipping binary

An inadmissible key in the **user** scope, with `OTEL_EXPORTER_OTLP_ENDPOINT`
exported so the endpoint never comes from a file:

```
jsonl-otlp-export: [telemetry] settings this command cannot receive:
'not_a_setting' (from user '.../home/.agentbundle/agentbundle-layout.toml')
(admitted: endpoint, service_name)
EXIT=1
```

This is the case the whole AC-0076 design exists for, and the one the
single-axis control could not see: the endpoint resolved from an environment
variable, and the user-scope key was still read and refused.

### 3. Off by default

No endpoint in either file and no environment variable → `EXIT=0`, nothing sent,
and the note names both flags:

```
jsonl-otlp-export: no endpoint is configured; nothing was sent. Set
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT, or give
--config or --user-config a TOML file declaring [telemetry].endpoint.
```

### 4. A hostile filename, through the real stderr

A configuration file whose **name** carries a newline and an ESC sequence:

```
EXIT: 1
stderr line count      : 1     (the newline forged no second line)
raw newline in message : False
raw ESC in message     : False
escaped forms present  : \n and \x1b both present
```

The escaping is not merely unit-asserted; it holds through the console script's
own stderr.

## Post-gates review round 3 — quality (Codex `gpt-5.6-sol`, read-only)

Operational-safety depth on the mixed-version route. One blocker, five concerns,
two nits. Dispositions below; the four code fixes were **dispatched to an
`implementer` subagent**, which is the envelope the earlier waves should have
used.

### Blocker — the cross-version claim was unbounded (sustained, corrected)

The Objective said the refusal "makes an older sender meeting a newer layout fail
loudly". A sender refuses keys outside *its own* admitted set, so the property
only holds from the version that introduced the refusal. Corrected in place —
`Objective` is working material — and the bound stated: `0.2.0` is the sender's
first **published** version, so no released sender predates the refusal and there
is no older-sender case in the field. No minimum-version pin was added; the
optional runtime dependency in `packs/core/pack.toml` still carries none, because
the lint reading it tests only presence. That was the owner's recorded decision.

### Registered, not fixed — three items

| Slug | Why not here |
| --- | --- |
| `pre-existing-config-exact-ceiling-growth-race` | pre-existing; not in this diff. Consequence raised by AC-0075, so registered rather than noted |
| `pre-existing-config-io-outside-every-deadline` | pre-existing; exposure doubled. Bounding config I/O is a behaviour change on a shipped path |
| `sender-cannot-explain-its-effective-configuration` | a diagnostic mode is new public CLI surface, declined at planning for the same reason |

### Deferred nit

The `find_spec` absence check sits at roster altitude though it reads only the
`agentbundle` tree. Moving it to `packages/agentbundle/tests/` is what
`packages/AGENTS.md` would prefer, but that tree ships in the sdist and is re-run
against an extracted workspace with no repository root, which is the failure
`tests/AGENTS.md` warns about — and the control's `-S` subprocess plus scoped
`PYTHONPATH` is repository-shaped. Deferred with its citation rather than moved
on a guess.

### Fixed by implementer dispatch — four fixes, gates clean

| Fix | Result |
| --- | --- |
| `run_unconfigured_check` deleted — dead, and its message had drifted to name only `--config` | gone from the module and `__all__`, with its helper-only tests and `_ExplodingTransport` |
| escaping control walked 7 of 10 sites | now 9 of 10, each arm asserting it reached *its own* message |
| roster subprocesses unbounded | `timeout=60` on both, failing with the block or command that hung |
| guide-block selector matched the whole guide | scoped to the `## Build the invocation` section |

Gates after the dispatch, verified by me rather than taken on report:
`pytest packages/jsonl-otlp-exporter/` **411 passed, 1 skipped**;
`pytest tests/roster/test_telemetry_sender_owns_its_configuration.py` **13
passed**; `make lint-ruff lint-mypy` and `ruff check .` clean. The single skip is
pre-existing and unrelated (`test_live_collector.py`, no receiver on 4318).
Mutation residue checked independently: the profile has no status entry and the
guide's unstaged diff is empty.

### Three things the implementer got right that the brief had wrong

- **The brief's `open-error` mechanism did not work.** It specified a FIFO. A
  writer-less FIFO opens *successfully* under `O_NONBLOCK`, so the descriptor
  check reports not-a-regular-file — the arm another case already owned, making a
  FIFO case a duplicate rather than new coverage. It measured both and used a
  symlink, where `O_NOFOLLOW` fails the open itself with `ELOOP`. The brief's
  requirement was met; only its stated mechanism changed.
- **It refused to fake the tenth site.** `short-read` needs `os.read` to return
  fewer bytes than `fstat` reported, unreachable for a local regular file under
  the ceiling. Substituting `os.read` would exercise the length comparison while
  the path stayed a name the test chose — so it would not test the escaping claim
  at all. Recorded as nine of ten with the reason, rather than overstated.
- **It proved Fix 4's inverse case was not vacuous.** An unrelated block outside
  the invocation section must *pass*, which a control insensitive to the mutation
  would also do. It re-ran the same mutation against the pre-fix selector,
  confirmed it *fails* there, and restored — establishing that the mutation bites
  and the fix is what absorbs it.

### One defect the implementer found in my own control

`test_a_reparse_point_is_refused` carried `monkeypatch.setattr(cfg, "stat", stat)`,
which rebinds the module to the real `stat` it already is — a no-op. Verified:
`cfg.stat is stat` → `True`, and `FILE_ATTRIBUTE_REPARSE_POINT` is defined on
every platform, so the case passed for a reason unrelated to the patch. The line
is removed and replaced with a comment saying why only `os.fstat` needs
substituting. It declined to copy the pattern into the new arm, which is why the
new arm was clean.

### Deletion check: no property lost with the dead helper

`test_the_note_goes_to_stderr_not_stdout` went with `run_unconfigured_check`. The
property it asserted — stdout carries no diagnostics — survives at
`test_cli.py:756` (`test_without_the_flag_stdout_stays_empty`), on the shipping
path rather than on a helper nothing called. Checked before accepting the
deletion.

### A measurement trap worth keeping

`packages/jsonl-otlp-exporter/pyproject.toml:43` sets `addopts = "-q"`, so a
command-line `-q` doubles to `-qq` and **suppresses pytest's summary line**.
Every exporter-suite run recorded earlier in this ledger was read from its
progress dots, not from a count. The counts above come from running without `-q`.

## Post-gates review round 4 — quality, bounded to the round-3 responses

Three concerns and two nits. **Every one was correct**, and three of them refuted
a disposition rather than finding new code — two of those dispositions were mine.

| Finding | Verdict |
| --- | --- |
| stdout purity "not lost with the deleted helper" | **wrong, mine.** `test_cli.py:756` runs a *configured* receiver, so it cannot fail if the *unconfigured* diagnostic moves to stdout. I confirmed a stdout-purity test existed without checking it reached that path. |
| `short-read` escaping arm "unreachable" | **wrong, both of us.** `TestShortRead` at `test_config.py:163` already drives a substituted `os.read` in this same package, and its docstring says so. The arm is reachable; coverage is 10 of 10. |
| the version guard went inert | **correct.** `assert printed != "0.1.0" or expected == "0.1.0"` cannot fire once the package is `0.2.0`. Both literals moved. |
| `find_spec` roster-altitude deferral "sound" | **my reason was refuted** — see the next section, where the right answer turned out to be the opposite of the reviewer's remedy. |
| stale release-state assumption | **correct.** Corrected to `0.2.0` unreleased, `0.1.0` replaced before publication. |

Fixes 1, 2, 3 and 5 were dispatched to an `implementer` and verified here:
`pytest packages/jsonl-otlp-exporter/` **412 passed, 1 skipped**, lints clean.

### Fix 4 was implemented, then reverted — the criterion decided it

The reviewer refuted my reason for leaving the AC-0002 control in roster (I had
claimed the sdist re-run needed a repository root; from
`packages/agentbundle/tests/unit/`, `parents[2]` *is* the package root, so that
was wrong) and asked for the control to move. The implementer moved it, and to
keep the suite green it had to add two exclusions to AC-0004's sweep: the control
file itself, and `.pytest_cache/v/cache/nodeids`, which records the new test's
node id the first time that suite runs.

Both exclusions are sound engineering and neither is admitted by AC-0004, which
reads: *"No file under `packages/`, `guides/`, `packs/` or `tools/` contains the
string `telemetry_layout`, except in `packages/agentbundle/CHANGELOG.md`…"*. The
implementation had become **wider than the criterion it implements** — the third
time this delivery has drifted that way, and the pattern two earlier rounds
already caught.

Measured with the move applied and no exclusions, the sweep found three files:
the changelog (admitted), the control itself, and the cache entry. Reverted, it
finds **exactly one** — the changelog. So AC-0004 holds as written, with no
exclusion list to rot, and the deferral now has the reason it lacked: **a control
asserting the module's absence must name the module, and AC-0004 sweeps every
tree the package suite lives in.** That is a property of the criterion, not of
the sdist.

Re-proved after the revert: a tombstone module reds the AC-0002 control, and a
straggler planted at `packs/core/.apm/skills/work-loop/STRAGGLER.md` reds the
AC-0004 sweep — so removing `_GENERATED` did not stop `packs/*/.apm` being swept,
which was the property that exclusion had been careful to preserve.

The reviewer's diagnosis was right and its remedy was wrong. Recorded that way
round, because "the reviewer was mistaken" would be the wrong lesson: my reason
*was* refuted, and the correct reason only surfaced by trying the move.

### Two findings the implementer surfaced that no reviewer did

- **The moved test was untracked.** It reported `??` on the new file and said
  plainly that Fix 4 would otherwise ship as a deletion with no replacement. The
  revert made it moot, but the warning was the right one to raise.
- **A stale `.egg-info` supplies distribution metadata to the exporter suite.**
  `packages/jsonl-otlp-exporter/jsonl_otlp_exporter.egg-info` is untracked, sits
  on the suite's `pythonpath`, and reports `Version: 0.2.0` — so
  `importlib.metadata` resolves inside a run with nothing installed. That is why
  the hardcoded-literal mutation for Fix 3 came out green as specified: a literal
  `"0.2.0"` is indistinguishable from the metadata read while that directory
  exists. It moved the `.egg-info` aside, reproduced the documented `0+unknown`
  fallback, confirmed the mutation reds there, and restored. Left in place and
  recorded rather than deleted: it is exactly the developer-environment coupling
  that test's own docstring warns about, and removing an untracked artifact
  nobody asked about is not this delivery's call.

### A caution about my own harness use

A `re.sub` in my revert script raised `PatternError` on an unbalanced
parenthesis, so the Python write never ran — but the `rm` of the moved test file
was outside that heredoc and did run. For one step AC-0002 had no control at all.
Caught immediately by re-reading the file, and the control was restored by
explicit string replacement rather than regex. The lesson is the ordering:
destructive shell steps do not belong downstream of an edit that can fail
silently in the same command.

## Post-gates review round 5 — quality, bounded

No blockers. The N1 revert was confirmed correct under AC-0004 as written, with
no exclusion residue, and `packs/*/.apm` confirmed still swept. One concern and
one nit, both sustained.

### The version guard was never sensitive — at either literal

Round 4's fix moved both literals from `0.1.0` to `0.2.0`. The reviewer pointed
out that this restored nothing, and it is right for a reason worth stating
plainly: the line above it already asserts `printed == expected`, so

```
assert printed != "<current>" or expected == "<current>"
```

is a tautology for **every** literal. If `printed` equals the literal then so
does `expected` and the second disjunct holds; otherwise the first does. The
guard could never fail at `0.1.0` either. It carried the message *"a hardcoded
literal must not be able to satisfy this"* while being exactly that.

Moving the literal made it look current, which is worse than leaving it stale —
a reader now sees a guard that appears maintained.

Replaced with a control that answers the real question: is `__version__` read
from the installed distribution's metadata, or is it a literal in the module?
A subprocess substitutes `importlib.metadata.version` with a sentinel **before**
importing the package; `_installed_version` resolves that name when it runs,
which is at import, so a metadata-reading module reports the sentinel and a
literal-carrying one reports its literal. Mutation: replace
`__version__ = _installed_version()` with `__version__ = "0.2.0"` — **killed**.

This also removes the dev-environment coupling the old test's own docstring
warned about. The implementer had found that the hardcoded-literal mutation came
out *green as specified*, because a stale untracked
`jsonl_otlp_exporter.egg-info` supplies `Version: 0.2.0` on the suite's
`pythonpath` — so a literal and the metadata read were indistinguishable, and it
had to move that directory aside to get a real verdict. The new control needs no
such manoeuvre: it substitutes the source rather than depending on what is
ambient. The `.egg-info` is left alone and stays registered as an observation.

Counted as a bundled fix on the Tier-3 terms: same file and same concern as the
version bump that drew attention to it, test-only, no production behaviour
changed, and it converts a control that cannot fail into one that can — which is
this delivery's recurring defect class rather than a new subject.

### The fifth stale companion in five rounds

My revert restored the roster docstring's AC range but left the sentence saying
AC-0002 "lives in `packages/agentbundle/tests/unit/test_telemetry_layout_retired.py`"
— a file the revert deleted. Removed.

Every one of the five review rounds has found exactly one stale companion
statement, each time in prose beside a change rather than in the change. The
pattern is stable enough to be worth naming: a repair updates the assertion and
leaves the sentence that describes it.

## Post-gates review round 6 — quality, bounded

No blockers. One concern and one nit, both sustained, both about the control I
had just written to replace the tautology.

### My replacement control tested the wrong surface

The new test asserted `p.__version__` — the package attribute. The requirement,
and what the deleted guard claimed, is about the **CLI's `--version` output**.
`cli.py` does `from . import __version__` at import and passes it to the parser,
so a literal in the parser would print an invented version while the package
attribute stayed correct, and my control would have passed. The reviewer also
noted the stub answered any distribution name, so querying the wrong one passed
too.

Rewritten to drive the surface the criterion names: the subprocess substitutes
`importlib.metadata.version` with a stub that answers the sentinel **only** for
`jsonl-otlp-exporter` and a distinct marker otherwise, then invokes
`cli.main(['--version'])` and requires the printed output to equal the sentinel.

Three mutations, three killed:

| # | Mutation | Verdict |
| --- | --- | --- |
| M1 | `__version__ = "0.2.0"` literal replacing the metadata read | killed |
| M2 | the CLI parser hardcodes `version="0.2.0"` | killed — the case the first replacement missed |
| M3 | the wrong distribution name is queried | killed |

Production diff after restore: 0 lines.

That is now **three successive attempts at one control**: a tautology that never
worked, a replacement that tested an adjacent surface, and a version that
exercises the public one. The subject was never the production code — it reads
its version from metadata correctly and always did. What kept being wrong was
the thing asserting it, which is this delivery's whole pattern.

### Review budget

`review_retry_count` is now 5 against `max_review_retries` 5. A further findings
round is refused by the cohort, deliberately: *"a findings round past the cap is
the runaway the cap exists to stop."* So the next round must return clean or the
run stops and surfaces to the owner rather than grinding. Recorded here so that
boundary is visible in the evidence rather than discovered at the gate.

## CI, and the gate no local run had reached

The first push failed one job: `gate-main` → `lint-catalogue-curation-guard`.
The commit touches five protected `packages/agentbundle/` paths — the retired
module, `version.py`, `pyproject.toml`, `README-pypi.md`, `CHANGELOG.md` — with
no `Engine-Change-RFC:` trailer. Test-tree paths are carved out, so the deleted
test and its fixtures did not count.

**Why no local gate caught it.** Run on its own, the guard prints
`path-gate: cannot evaluate changes because git or diff base 'missing-base' is
unavailable` / `path-gate explicitly skipped for local run`, and **exits 0**. It
needs a resolvable diff base, which only `make build-check` supplies — and
nothing in this delivery's gate list ran `make build-check` until the failure
sent me looking. A green standalone guard is ambiguous between "passed" and
"never ran".

**The trailer.** Rather than invent a justification, I read how engine-touching
commits phrase it. The closest precedent is `2b1574e19` — the
`loop-telemetry-export` delivery that *added* `telemetry_layout` — which carried
it as `n/a` naming the approved spec and ADR-0115. This change removes the same
module under the same ADR, so the trailer states the symmetric case explicitly
and lists what does **not** move: no CLI verb, flag semantics, schema, install
path or projection.

**Proved load-bearing, both directions.** Stripped the trailer and re-ran the
guard against a pinned merge-base SHA: it failed and named all five paths.
Restored it: `ok`. A pinned SHA rather than `origin/main`, because a peer's fetch
moves that ref mid-run.

The amend changed only the commit timestamp, so local was reset to the pushed
commit rather than force-pushed again — identical tree, identical message, and a
second push would have restarted 42 checks for nothing.

### The semgrep leg was load, not a defect

`make build-check` without `SAST_DELEGATED` then failed in `sast`: 3 timeout
diagnostics, all on
`packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`, at 1-minute load
average **87.2 on 10 CPUs**. Followed the gate's own instructions rather than
guessing: the file is **not in this diff**, and the same invocation against that
file alone **exits 0**. Cause found — a peer session running the full
`pytest tests` suite in the `dispatch-agent-context` worktree. Left alone; it is
not this session's process.

`make build-check SAST_DELEGATED=1`, which is how CI's `gate-main` invokes the
target, completes clean. CI confirmed it: `gate-sast` **passed in 4m21s** on a
quiet runner.

**My own exit-code reading was wrong first.** The failing run reported `EXIT=0`
because `${PIPESTATUS[1]}` is the *second* element in zsh's 1-indexed array,
while `make` had plainly printed `Error 2`. The failure was found by reading the
log, not the status. See the note this repository already carries on that array.

### Final CI state

37 pass, 5 skipping, 0 failures — `gate-main` 6m42s, `gate-sast` 4m21s,
`gate-export-boundary` 3m42s, `build-and-smoke` 3m22s, plus the Windows and
py3.12 matrix legs. The two dispatch-only workflows, `test-corpus` and
`test-roster`, were triggered separately; they carry partial evidence and gate
nothing.
