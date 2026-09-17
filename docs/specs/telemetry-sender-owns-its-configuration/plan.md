# Plan: telemetry-sender-owns-its-configuration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/telemetry.md` § 5.3 owns how this
  configuration path is described, including the recorded reason a
  catalogue-level default cannot carry an endpoint (`:169-180`). Two analogous
  implementations: `jsonl_otlp_exporter/config.py:39-118` is the existing
  single-scope config read and endpoint precedence, tested in the package's
  config suite; `agentbundle/telemetry_layout.py:86-166` is the two-scope
  per-setting merge and scope-naming refusal being relocated, tested by
  `packages/agentbundle/tests/unit/test_telemetry_layout.py` — whose twelve cases
  are the behaviour inventory this delivery must reproduce on the sender side
  before deleting them. Named uncertainty: no repository precedent exists for a
  published CLI gaining a second file-valued flag of the same kind, so the
  `--user-config` naming is chosen by symmetry with `--config` rather than
  matched to a prior case.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `notes/verification-ledger.md`. A genuine artifact error follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

Relocate configuration resolution from a repository-side library into the sender,
then delete the library. The sender already owns every primitive the move needs,
so the change is a second call to an existing reader plus a merge, not new
machinery.

Order is forced by what breaks in between. The sender must accept
`--user-config` before the guide can document it; the guide must stop importing
`agentbundle.telemetry_layout` before that module can be deleted; and the roster
test that drives the documented invocation can only pass once both have landed.
Each task leaves the repository working.

## Constraints

- Both packages stay standard-library-only at runtime. `agentbundle` must not
  import the sender: it is an *optional* dependency of `packs/core`, so the
  import would not resolve on an install that declined it.
- No criterion added to the sender's contract may name a consumer, product,
  repository or catalogue. This rules out root-taking flags, because deriving
  `agentbundle-layout.toml` from a directory would put that filename in the
  sender's contract.
- `docs/specs/loop-telemetry-export/` is `Shipped` and frozen. No file in it is
  edited.
- `tests/roster/test_loop_telemetry_disclosure_contract.py` already pins the
  guide's `## What leaves your machine` heading, three literal strings, and the
  absence of any exit code in the reserved 2–9 band. The guide rewrite keeps all
  of them.
- Reviewable size is well under the 2,000-line tail-triage threshold; no review
  shape declaration or decomposition is required. Recorded so the check is not
  merely skipped.

## Construction tests

Package-level behaviour is verified in
`packages/jsonl-otlp-exporter/tests/` against fixture files and must not read
above that package — `tools/test-lint-pack-test-boundary.py` enforces the
downward half of that rule and runs directly, having no pytest surface.
Repository-level claims go to `tests/roster/`, anchored at
`Path(__file__).resolve().parents[2]`.

The twelve cases in `packages/agentbundle/tests/unit/test_telemetry_layout.py`
are the inventory: each one names a behaviour that must have a sender-side
equivalent before the file is deleted. Three of them are the load-bearing ones —
the caller cannot choose which file is read, the merged setting reaches the
invocation rather than only the settings mapping, and the refusal names the file
the setting came from. The first does not survive relocation and must not be
faked: the sender takes file paths, so its caller *does* choose the files. That
guarantee moves to the caller and is what AC-0003 pins instead.

**Grounding, probed 2026-09-16.** A throwaway run of the current sender
confirmed the three facts the T5 delivery control rests on, with no network and no
change to the tree: the `connection_factory` seam exposes the resolved
destination (observed `('http', '127.0.0.1', 4318)`); a `--config` file placed
outside `--root` resolved its endpoint, so AC-0062's carve-out works as written
and `--user-config` needs no new confinement exception; and `service.name`
appears on the emitted body as a resource attribute, so the criterion is
observable on the request rather than only on a mapping. The probe also confirmed
`build_parser()` carries no `--user-config` today. One caution it surfaced for
T2's fixtures: the transport calls `response.read()` with an argument, so a fake
response whose `read` takes no argument fails the run for a reason unrelated to
the behaviour under test.

Every control added here carries a recorded mutation in
[`notes/verification-ledger.md`](notes/verification-ledger.md): the mutation
applied, the observed red, and the suite that produced it. A control with no
recorded red is not trusted, because the previous delivery on this package
produced eleven review findings and every one was a control that could not fail.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility — `docs/specs/jsonl-otlp-exporter/spec.md` | T1 | Amended criteria and their Testing Strategy entries |
| Sender behaviour | T2 | Package suite green, mutation records per control |
| Sender published surface — its README, changelog, version | T7 | Option table and precedence list name `--user-config`; version bumped |
| User-facing promise — the guide | T3 | AC-0001, AC-0003 |
| Current architecture — `telemetry.md` § 5.3 | T3 | Section describes the shipped two-flag mechanism |
| Current product truth, release history — README, changelogs, version | T4 | AC-0004, version files agree |
| Repository pinning | T5 | The frozen contract's AC-0041/0043/0044 controlled; all controls green in CI, not only locally |
| Decision rationale — the answered shaping question | T6 | Intent records which question this closed |
| Reusable learning | T1–T6 | `notes/verification-ledger.md` |

## Design (LLD)

### Design decisions

**A second named flag, not a repeatable one.** `--user-config` appends a fourth
source to the endpoint chain and moves none of the three before it, so the
amendment to AC-0002 is additive. A repeatable `--config` would instead make
precedence positional, which is harder to document and easier for a hook to
assemble wrongly. Root-taking flags are excluded by the capability-scoped rule.

**The admitted-setting constant stays private.** Nothing outside the sender reads
it: the retirement removes the only other declaration of the deliverable set, so
there is no guard to satisfy and no drift to detect. It backs the refusal message
and nothing else, so exporting it would add public surface to a published package
for no consumer.

**Both files are read whenever their paths are supplied.** Today
`read_config_file` is reached only when both endpoint environment variables are
absent (`config.py:110-112`). Leaving the refusal inside that branch would stop
it firing whenever `OTEL_EXPORTER_OTLP_ENDPOINT` is set, which is a control that
cannot fail for the configurations most likely to carry a stale key. Reading and
validating unconditionally also matches the sender's existing behaviour for
`--profile`, which is validated even when nothing is configured so that a dry run
reports a broken profile, and it is already licensed by AC-0033's carve-out: a
refused `--config` exits 1 whether or not an endpoint resolves.

**Refusal over warning for an unknown key.** A warning on a hook's stderr is
rarely read, and the failure it describes — a setting the adopter believes is
active being dropped — is silent misconfiguration. Refusing also gives
cross-version safety with no version negotiation: an older sender meeting a newer
layout fails loudly. This is the resume cursor's `v`-field discipline applied to
a key set rather than a version integer.

**Retire rather than guard.** Keeping `telemetry_layout` as an early validator
would leave two declarations of the deliverable set with nothing able to
reconcile them at runtime, since `agentbundle` cannot import the sender. The only
remaining option would be a test asserting two constants are equal, which passes
whenever both are wrong together. Deleting the duplicate removes the failure mode
instead of detecting it.

### Interfaces & contracts

The sender's CLI gains `--user-config PATH`. Resolution order per setting:

| Setting | Order |
| --- | --- |
| `endpoint` | `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `--config`, `--user-config` |
| `service_name` | `--service-name`, `--config`, `--user-config`, the `--profile` filename stem |

`--user-config` takes `--config`'s open-time discipline verbatim — no-follow
open, regular-file proof on the descriptor, the 64 KiB ceiling, the short-read
refusal — and, for the same recorded reason, no `--root` confinement: a
user-scope configuration file legitimately lives outside any data root.

### Behavior & rules

- A `[telemetry]` value that is not a non-empty string is refused.
- A `[telemetry]` key outside the admitted set is refused, naming each scope it
  appeared in and listing the admitted set. Keys come from an untrusted file and
  reach a terminal, so each is rendered through `repr` — a key carrying a newline
  must not forge an extra error line, and one carrying an escape sequence must not
  repaint the display. `telemetry_layout.py:119-133` does this deliberately and
  the property survives relocation.
- Absence is not refusal. A `--config` or `--user-config` path that does not
  exist contributes nothing, matching today's `read_config_file`.

### Failure, edge cases & resilience

- Both scopes declaring the same setting: the repository scope wins, and the
  user scope's value is not reported as a conflict.
- The repository scope declaring only `service_name` while the user scope
  declares only `endpoint`: both must reach the run. This is the case
  per-scope selection gets wrong, and the T5 control for the frozen contract's
  AC-0041 is what pins it.
- The same file passed to both flags: read twice, merged with itself, no error.
- An unknown key present only in the user scope: refused, and the error names the
  user file rather than the repository file.

### Dependencies & integration

No dependency changes. `packs/core/pack.toml`'s optional runtime dependency on
`jsonl-otlp-exporter` is unchanged and gains no version pin: the schema admits
one, but the lint only tests presence via
`importlib_metadata.distribution(package)` (`catalogue_tooling/lint.py:1663-1666`),
so a pin would pass every gate while constraining nothing.

## Tasks

### T1: the sender's contract admits a second configuration scope

**Depends on:** none

**Touches:** docs/specs/jsonl-otlp-exporter/spec.md, docs/specs/telemetry-sender-owns-its-configuration/notes/verification-ledger.md

**Tests:**
- `python '<skill-dir>/scripts/lint-spec-status.py' --root .` clean: the amended
  spec keeps valid status vocabulary and its references resolve.
- No criterion added names a consumer, product, repository or catalogue —
  checked by reading each new criterion against the Boundaries' first "Never do",
  which is the rule the amendment is most likely to break.
- no stub (goal-based) — the artifact is contract text.

**Approach:**
- Amend AC-0002 to a four-source chain, appending `--user-config` and leaving the
  first three sources in place and unreworded.
- Amend AC-0007 so `service.name` names its full precedence rather than only the
  flag and the stem default.
- Amend AC-0062 to cover `--user-config` under the same open-time discipline and
  the same absence of `--root` confinement.
- Amend AC-0033 to include a refused `--user-config` in its exit carve-out. That
  criterion enumerates `--config`, `--profile` and `--from-cursor` by name
  (`docs/specs/jsonl-otlp-exporter/spec.md:145`), so adding a fourth refusable
  file argument without amending it leaves the exit rule silent about the new
  flag — and the unconditional read makes that interaction reachable, not
  theoretical.
- Add criteria for the per-setting merge, the admitted-key closure and its
  scope-naming refusal, and the unconditional read — the last one asserted with an
  endpoint environment variable set, which is the case a naive implementation
  passes everything else and fails.
- Record each amendment with its reason in the spec's amendment section, per the
  form the existing AC-0033 and AC-0039 carve-outs use.
- Add the matching Testing Strategy verification items.

**Done when:** every test above passes and each new or amended criterion is
listed in a Testing Strategy item.

### T2: the sender resolves both layout scopes and refuses a key it cannot deliver

**Depends on:** T1

**Touches:** packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py, packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cli.py, packages/jsonl-otlp-exporter/tests/, docs/specs/telemetry-sender-owns-its-configuration/notes/verification-ledger.md

**Tests:**
- Per-setting merge across both scopes, including the repository-declares-only-
  `service_name` case, asserted on the emitted request and its destination through
  the `connection_factory` seam rather than on a returned mapping.
- The unknown-key refusal fires when the endpoint comes from *each* source, as a
  parameterized case over `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`,
  `OTEL_EXPORTER_OTLP_ENDPOINT`, `--config` and `--user-config`. Both env-var arms
  are required, not just the base one: `config.py:106-108` returns early on the
  logs-specific variable, so a read placed after that return but before the base
  branch at `:110-112` would satisfy a base-only control while still being
  conditional. The mutation is to move the read after each precedence branch in
  turn, and every arm must red.
- `service.name` precedence across all four sources at once — distinct values via
  `--service-name`, `--config`, `--user-config` and the profile stem — asserting
  the flag value is the one emitted. Existing coverage at
  `tests/unit/test_cli.py:483` separates the flag from the stem only, so a merge
  test with no flag present would pass an implementation letting either config
  overwrite the flag.
- The refusal names the originating scope, for a key in the repository file only,
  the user file only, and both.
- Control characters are escaped in the refusal for **both** the key and the file
  path it came from. `telemetry_layout.py:119` states the rule for both ("Keys and
  paths both reach a terminal") and renders the path through `repr` at `:127`; a
  flag value is caller-supplied and can carry a newline or an escape sequence just
  as a key can.
- A `telemetry` value that is not a table is refused — `telemetry_layout.py:73`
  raises on a non-dict, and a run given `telemetry = "not a table"` must not
  proceed as though the section were absent.
- The opened descriptor is rejected when it is a reparse point or has
  `st_nlink > 1`. `file_safety._validate_regular_file_stat:343-346` applies both
  checks today and the sender's `read_config_file` applies neither, so relocating
  the read without them would silently drop two guards. Both are pure `stat`
  checks on an already-open descriptor and need no root, so they survive the
  path-valued interface.
- `--user-config` refuses a symlink, a FIFO, a directory and an over-ceiling file
  on the opened descriptor, and accepts a path outside `--root`.
- A non-string and an empty-string `[telemetry]` value are refused.
- Absence of either file contributes nothing and is not an error.
- `python3 packages/jsonl-otlp-exporter/tests/wiring_sweep.py` adds no survivor
  beyond the two `frozen=True` cases already reported.

**Approach:**
- Add `--user-config` to `build_parser`.
- Read and validate both supplied files unconditionally, before any endpoint
  precedence branch runs, so no refusal can be shadowed by either environment
  variable.
- Merge per setting, repository scope first, and take the merged mapping as the
  source for both `endpoint` and `service_name`.
- Keep `--service-name` ahead of the merged `service_name`, and the `--profile`
  stem last.
- Carry the reparse-point and hard-link rejections into the sender's own
  descriptor validation rather than reaching for `agentbundle`'s helper, which is
  unavailable and would reintroduce the dependency this delivery removes.
- Walk the twelve cases in the retiring `test_telemetry_layout.py` and confirm each
  has an equivalent here or a recorded reason it does not survive relocation. Three
  guards have no retiring test and must still be accounted for in the ledger: the
  absolute-root checks at `telemetry_layout.py:96-99`, the
  `validate_confined_directory` call at `:101`, and the derived-filename guarantee
  its docstring describes. None survives a path-valued interface, because the
  caller now names the files; that is the trade this delivery accepts, and AC-0003
  is what pins the caller's side of it.

**Done when:** `python3 -m pytest packages/jsonl-otlp-exporter/ -q` is green, the
sweep adds no survivor, and every control above has a recorded mutation and
observed red in the verification ledger.

### T3: the documented invocation needs no package dependency

**Depends on:** T2

**Touches:** guides/core/how-to/export-loop-telemetry.md, docs/architecture/telemetry.md, tests/roster/, docs/specs/telemetry-sender-owns-its-configuration/notes/verification-ledger.md

**Tests:**
- AC-0001: both documented blocks execute in a **subprocess** under a
  `sys.meta_path` finder refusing `agentbundle`, and the block-count floor holds.
  The subprocess is load-bearing: an in-process finder is skipped for anything
  already in `sys.modules`, and the runner may itself have imported
  `agentbundle`. The mutation is to reintroduce the import; the execution must
  red, which neither a lexical subset check nor a blacklist of dynamic-import
  spellings would.
- AC-0003: `--config` and `--user-config` carry the two layout paths. The
  documented argument list is additionally parsed with the sender's own
  `build_parser()`, so a renamed flag reds here rather than at an adopter's run.
- `tests/roster/test_loop_telemetry_disclosure_contract.py` stays green, so
  AC-0020's heading and literals and AC-0042's exit-code band survive the rewrite.
- no stub for the architecture edit (goal-based).

**Approach:**
- Replace both Python blocks with a standard-library-only form building the five
  paths from a repository root and the user layout directory.
- Drop the sentence claiming `resolved.arguments` "is already a list"; it
  described a `tuple[str, ...]` and disappears with the rewrite.
- Explain that the sender reads `[telemetry]` from both files, replacing the
  passage explaining why each non-endpoint setting became its own flag — that
  reason no longer exists.
- Refresh `telemetry.md` § 5.3 to describe the shipped two-flag mechanism in the
  present tense rather than the conditional. Keep the recorded finding at
  `:169-180` that a catalogue-level default cannot carry an endpoint; it is still
  true and now has a registered follow-on.

**Done when:** AC-0001 and AC-0003 pass *in this task* — their controls are
written here, not deferred to T5, because a task whose `Done when` names a
criterion its dependent task has not yet built cannot be observed when it
completes. T5 registers them with CI; it does not create them. `telemetry.md`
§ 5.3 names both flags and describes the mechanism in the present tense, and the
pre-existing disclosure roster test is still green.

### T4: `agentbundle` ships no telemetry-layout module

**Depends on:** T3

**Touches:** packages/agentbundle/agentbundle/telemetry_layout.py, packages/agentbundle/tests/unit/test_telemetry_layout.py, packages/agentbundle/tests/fixtures/telemetry-layout/, packages/agentbundle/README-pypi.md, packages/agentbundle/CHANGELOG.md, packages/agentbundle/pyproject.toml, packages/agentbundle/agentbundle/version.py, docs/product/changelog.md, tests/roster/

**Tests:**
- AC-0002: `importlib.util.find_spec("agentbundle.telemetry_layout")` is `None`.
  `find_spec` is used rather than an import attempt so a tombstone module raising
  `ModuleNotFoundError` from its body cannot satisfy it.
- AC-0004: no file under `packages/`, `guides/`, `packs/` or `tools/` names
  `telemetry_layout`, except in `packages/agentbundle/CHANGELOG.md` under the
  `## [0.45.0]` heading or in a `### Removed` subsection. The two-context form
  admits the historical entry and this delivery's own removal entry while still
  failing a current-version `Added` or `Changed` entry that advertises the
  resolver — which a "beneath any version heading" rule would have let through.
- `packages/agentbundle/tests/unit/test_version.py` stays green, which is what
  already pins `CLI_VERSION` against `pyproject.toml`; no second version
  assertion is added here.
- `ruff check .` clean — deleting a test orphans the imports only it used, and the
  repository lint targets do not cover that.

**Approach:**
- Delete the module, its unit test, and the two orphaned fixtures at
  `packages/agentbundle/tests/fixtures/telemetry-layout/` — that test is their only
  reader.
- Write the AC-0002 and AC-0004 controls here rather than in T5, for the same
  reason T3 writes its own.
- Remove the README-pypi paragraph advertising the resolver.
- Bump `pyproject.toml` and `version.py` together to a minor version: removing a
  public module is non-cosmetic and breaking, though not a release trigger under
  `packages/AGENTS.local.md`, which scopes release to CLI verbs, flag semantics,
  output layout and schema breaks.
- Add a topmost `### Removed` changelog entry under the new version. Leave the
  `## [0.45.0]` entry that introduced the resolver untouched: it describes what
  that release shipped and stays true of it.
- Check whether `docs/product/changelog.md:187` is a live claim or a historical
  release entry before editing it, and treat it as the latter if it sits under a
  released heading.

**Done when:** AC-0002 and AC-0004 pass, `ruff check .` is clean, and
`python3 -m pytest packages/agentbundle/tests/unit/test_version.py -q` is green.

### T5: the frozen consumer criteria gain their first control, and CI runs it

**Depends on:** T3, T4

**Touches:** tests/roster/, .github/workflows/build-check.yml, tools/lint-ci-parity.py, .workspace-prune-protected.toml, docs/specs/telemetry-sender-owns-its-configuration/notes/verification-ledger.md

**Tests:**
- `loop-telemetry-export`'s AC-0041, AC-0043 and AC-0044 gain their first
  control, in three arms. A **conflicting** arm where both scopes declare the same
  setting and the repository value is the one emitted: the disjoint case alone
  cannot prove precedence, because it stays green when the two flags are swapped,
  and precedence is what AC-0041 actually claims. A **fallthrough** arm where the
  repository file omits a setting the user file supplies. And an
  **input-and-profile** arm placing the only event at `.loop-run/events.jsonl`
  under the real work-loop profile, so a wrong `--input` or `--profile` fails
  instead of going unobserved — AC-0043 and AC-0044 had no assertion that could
  fail before this. Every arm asserts on the emitted request and its destination
  after a positive emitted-record count, since a run emitting nothing satisfies
  any claim quantified over emitted records.
- `python3 -m pytest tests/roster/ -q` green, covering the AC-0001 through AC-0004
  controls T3 and T4 wrote as well as this task's.
- `python3 tools/lint-ci-parity.py` green, which is what refuses a roster step
  present in one place and absent from the other; no criterion restates it.

**Approach:**
- Add this task's integration control to the roster file T3 created, rather than a
  second file: one roster file means one registration.
- Add the naming step to `build-check.yml`, since `pytest tests/` reaches these
  files but a pull request does not.
- Add the `STEP_DISPOSITION` entry as `LOCAL("test-after-build-check")`.
- Add a `.workspace-prune-protected.toml` entry only if the test names a
  `docs/specs/<slug>` path as a literal; confirm whether it does rather than
  adding the entry unconditionally.

**Done when:** the roster suite and the CI-parity lint are both green, and the
new test is named by a `build-check.yml` step.

### T6: the answered shaping question is recorded

**Depends on:** T1

**Touches:** docs/product/intents/loop-telemetry-contract-corrections.md

**Tests:**
- The intent states which of its two unresolved questions this delivery closed
  and that AC-0031's enumeration remains open.
- `workspace.toml` parses, and the register entry still resolves to a file that
  exists.
- no stub (goal-based) — the artifact is a Living product document.

**Approach:**
- Record that the undeliverable-setting refusal now has a criterion in the
  sender's contract, so that question is answered by relocation rather than by a
  `loop-telemetry-export` amendment.
- Leave the entry in `[backlog].open` rather than retiring it: its AC-0031 half
  is untouched, and re-pointing an entry is what keeps a partially-answered item
  from being read as fully closed.

**Done when:** the intent distinguishes the closed question from the open one,
and `workspace.toml` parses.

### T7: the sender's published surface describes the flag it now has

**Depends on:** T2

**Touches:** packages/jsonl-otlp-exporter/README-pypi.md, packages/jsonl-otlp-exporter/CHANGELOG.md, packages/jsonl-otlp-exporter/pyproject.toml

**Tests:**
- The README's option table names `--user-config`, and its endpoint-precedence
  list names all four sources in order. The table at `README-pypi.md:59` and the
  precedence list at `:28` are the published description of exactly what T2
  changes, so leaving them is shipping a stale contract to PyPI.
- The README's stated `64 KiB each` ceiling at `:134` covers `--user-config` too.
- `pyproject.toml`'s version is bumped: the flag is an added CLI surface and the
  unknown-key refusal changes flag semantics, which `packages/AGENTS.local.md`
  names as a release trigger.
- no stub (goal-based) — the artifacts are published prose and a version literal.

**Approach:**
- Add `--user-config` to the option table and extend the precedence list.
- Add a changelog entry covering both the new flag and the refusal, the latter
  called out as a behaviour change for a config carrying an unknown key.
- Bump `pyproject.toml` only. `packages/AGENTS.md`'s "update both `version.py` and
  `pyproject.toml`" rule does not apply here: this package deliberately has no
  `version.py`, reading its version from installed metadata instead
  (`jsonl_otlp_exporter/__init__.py`), so there is no second literal to keep in
  step. Recorded because a blanket reading of that rule would have an implementer
  create one, reintroducing the drift the package avoided.

**Done when:** the README describes the four-source precedence and the new flag,
the changelog names the behaviour change, and the version is bumped.

## Rollout

No migration and no adopter action. An adopter's `agentbundle-layout.toml` is
unchanged in name, location and content; only the process that reads it changes.
An adopter carrying an unknown `[telemetry]` key sees a refusal where they
previously saw the key silently ignored, which the spec's Assumptions record as
accepted.

The only reachable caller today is the guide's documented invocation, which lands
in the same change, so no external caller is stranded by the module's removal.

## Known non-blocking gate condition

`lint-contract-item-alignment.py` reports 21 findings against this spec
directory, all of the form `AC-NNNN resolves to no criterion`, and exits 0.
Every one is a **cross-spec** citation: this spec cites `loop-telemetry-export`'s
AC-0041, AC-0043 and AC-0044 as the owners of obligations it deliberately does
not re-author, and `jsonl-otlp-exporter`'s AC-0002, AC-0007, AC-0033 and AC-0062
as the criteria T1 amends. The lint's reference extractor is
`CRITERION_REF = re.compile(r"\bAC-\d{4}\b")` and it resolves identifiers
within one spec directory only, so it has no way to distinguish a citation of
another spec's criterion from a dangling local reference.

What the lint proves here: every criterion in this spec carries a unique
well-formed identifier and is named by a task entry. Its blind spot: it cannot
see cross-spec ownership, which is the single structural property review round 1
spent its blockers on.

Suppressing these findings by removing the citations would hide that ownership
and reintroduce the second-home defect, so they are left in place and recorded
here instead. Worth a lint enhancement — a qualified `<spec-slug>#AC-NNNN` form —
but that is a change to a shipped skill script and outside this delivery.

## Risks

- **An adopter's config carries an extra `[telemetry]` key and starts exiting 1.**
  Accepted deliberately over a warning. Mitigated by the error naming the key, the
  scope and the admitted set, so the fix is visible from the message alone.
- **The relocation drops a guard that only the retiring test covered.** Mitigated
  by walking all twelve cases in T2 and recording, per case, the sender-side
  equivalent or the reason it does not survive.
- **The roster test passes locally and never runs on a pull request.** This is the
  failure `tests/AGENTS.md` describes, and why T5 treats the three registration
  edits as part of the task rather than as follow-up.

## Changelog

- 2026-09-16 — drafted. Two premises in the original framing were corrected before
  authoring: there is no install-time validation to keep, since
  `telemetry_layout.resolve` has no production caller; and `loop-telemetry-export`'s
  AC-0041 needs no re-homing, since it constrains the documented invocation rather
  than the implementing package, which is fortunate because its spec is frozen.
  The owner chose retirement over a drift guard and a structural unknown-key
  refusal over a version pin, which together removed the roster drift guard and its
  three registration edits from the original shape. A catalogue-declared endpoint
  projected into the user profile was logged as a follow-on rather than built.
- 2026-09-16 — contract review round 1 (Codex `gpt-5.6-sol`, read-only) returned
  five blockers, two concerns and one nit; all eight were verified against the
  tree and sustained, and all eight repaired. Two corrected my own errors: the
  `agentbundle-layout` assumption rested on truncated `head -30` grep output and
  named one reader where 84 files match, and the frozen-spec rule is at
  `docs/CONVENTIONS.md:430-432` with a mechanical-rewrite carve-out at `:178-182`,
  not the retention paragraph at `:435`. The structural repair was ownership: the
  original AC-0003 and AC-0004 authored second homes for obligations the frozen
  `loop-telemetry-export` criteria already own, so the criteria narrowed to the
  genuinely new two-file shape and the roster test now supplies those three
  criteria's first control instead of restating them. AC-0001 moved from a lexical
  import-subset check, vacuous on an empty guide and blind to `__import__`, to
  executing the blocks with `agentbundle` unimportable; AC-0002 moved to
  `find_spec` so a tombstone module cannot pass; AC-0004's exemption narrowed from
  any `CHANGELOG.md` to release entries only.
- 2026-09-16 — adversarial review round 1 (Codex `gpt-5.6-sol`, read-only,
  mechanism and code paths) returned four blockers, five concerns and one nit; all
  ten were verified against the tree and sustained, and all ten repaired. The
  sharpest was an ordering control that could not fail: the planned unknown-key
  test set only `OTEL_EXPORTER_OTLP_ENDPOINT`, but `config.py:106-108` returns
  early on the logs-specific variable, so a read placed between the two branches
  would pass it while still being conditional — the control is now parameterized
  over all four endpoint sources with a per-branch mutation. Two genuine gaps were
  found: relocation would have dropped the reparse-point and hard-link rejections
  that `file_safety._validate_regular_file_stat:343-346` applies and
  `read_config_file` does not, so T2 now carries both; and the sender's own
  published surface — its README option table, precedence list, changelog and
  version — had no task at all, which is now T7. Task ownership was also wrong:
  T3 and T4 named criteria in their `Done when` whose controls T5 was to build,
  so each task now writes its own and T5 only registers them.
- 2026-09-16 — convergence round (Codex `gpt-5.6-sol`, read-only, bounded to the
  repairs) returned three blockers, three concerns and one nit; all seven verified
  and repaired. One was a defect the previous round's own repair introduced:
  AC-0004's exemption, narrowed to a single occurrence under `## [0.45.0]`,
  forbade the `### Removed` entry T4 must write naming the module it removed — the
  exemption is now scoped to release entries. Two were stale companions the
  renumbering left behind, and one was T7 inserted after `## Rollout` so it read as
  a Rollout subsection rather than a task. The substantive two: AC-0001's control
  now runs each block in a **subprocess**, because an in-process `sys.meta_path`
  finder is never consulted for a module already in `sys.modules` and the runner
  may itself have imported `agentbundle` — its lexical dynamic-import blacklist was
  dropped rather than patched, since an alias or `exec` defeats it and executing
  the block already carries the claim. And T5's control grew from one disjoint arm
  to three: disjoint settings prove arrival but not precedence, and stay green if
  the two flags are swapped, while AC-0041 claims precedence — so a conflicting arm
  and an input-and-profile arm were added, the latter giving AC-0043 and AC-0044
  their first assertion that can fail.
- 2026-09-16 — pre-EXECUTE convergence rounds 4 and 5 (Codex `gpt-5.6-sol`,
  read-only, each bounded to the previous repair set). Round 4 returned two
  blockers, both on the previous round's own repair: widening AC-0004's changelog
  exemption to "beneath any version heading" let a current-version `Added` or
  `Changed` entry advertise the retired module — a live stale claim, which is the
  failure the criterion exists to catch — and VI-0002 still stated the superseded
  "exactly one occurrence" rule, contradicting both AC-0004 and T4. Fixed by
  pinning one two-context rule in all three places: an occurrence is admitted only
  under `## [0.45.0]` or in a `### Removed` subsection. Round 5 returned
  `Clean — ready to commit.` Five rounds, 27 findings, all sustained on
  verification against the tree and all repaired; three of the five rounds found a
  defect introduced by the preceding round's repair, which is where this artifact
  spent most of its review cost.
- 2026-09-16 — owner approved spec and plan. Enterprise-baked telemetry defaults
  bind the individual user rather than a team repository, so they occupy the user
  layer and need no additional configuration source; the two-file shape is final
  for this delivery.
