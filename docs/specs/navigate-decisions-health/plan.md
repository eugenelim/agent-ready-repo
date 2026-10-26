# Plan: navigate-decisions health mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, eval-harness rule, pack-test boundary, UTF-8 stream rule); `docs/specs/decision-navigation/spec.md` fixes `decision-navigation.query.v1` at five operations, so `health` is a sibling subcommand like `export`; `navigate_decisions.py` `_admit_corpus` and `_parse_record_text` are the corpus path health reuses; `packs/repo-governance/tests/skills/navigate-decisions/test_query_contract.py` (module loaded by unique name) and `test_skill_instructions.py` (section-sliced content pins) are the construction paths; `docs/specs/navigate-decisions-route/notes/verification-ledger.md` is the activation and behaviour-run precedent. Uncertainty: whether a fourth mode in the description holds the trigger rate, which only T6 can show.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

Health is mostly code, unlike `route`. The four reports and the stage-5 trust
rules need a deterministic oracle, so the script gains a `health` subcommand that
reuses corpus admission and prints one JSON result. The skill file gains a
`health` section that runs it and renders a fixed result block. Nothing else in
the script changes.

The riskiest parts are two:
1. **Accuracy.** The rules must agree with a hand reading of 144 accepted ADRs.
   A probe on 2026-10-26 ran draft rules over `docs/adr/` (see Design). It found
   1 `due`, 8 `version` and 135 `judge` triggers, 5 header citations, 3 missing
   signal paths, 41 present and 33 unlocated. So T5's hand check is real work,
   and it runs independently of T2 so it cannot be tuned to the code.
2. **Activation.** A fourth mode in the description may lower the trigger rate.

Order follows from that:
1. T1 freezes the health queries and the hostile fixture, and measures the
   pre-change world.
2. T2 builds the health command by TDD. T5's hand check runs in parallel.
3. T3 adds the skill section and description. T4 updates documents and the version.
4. T6 measures the post-change world, runs the behaviour cases, and diffs the
   hand check against the health result.

## Constraints

- RFC-0110 D5 stage 5 and its 2026-10-25 errata: `health` is a read-only mode on
  `navigate-decisions`, no new skill, and it never runs checks. Stage 4 is cut, so
  the "no `Confirmation`" count carries no stage-4 framing.
- RFC-0110 § Trust model rules 1 and 4 and the stage-5 block bind health. Rules 2,
  3 and 5 govern writes, and only stage 1 writes.
- Brief `repo-governance-pack` § Success metrics (Stage 5 accuracy, Mode
  activation) and § Assumptions / Risks (modes may load less often).
- `docs/specs/decision-navigation/spec.md` (Shipped) fixes `query.v1`; health
  leaves it unchanged.
- `packs/AGENTS.md`: bump `pack.toml` and `plugin.json` together, update the eval
  harness, keep pack tests inside the pack, and reconfigure stdout and stderr to
  UTF-8 (the script already does). No pack content cites this catalogue's
  internal records.
- Root `AGENTS.md`: filesystem confinement uses the blessed `file_safety`
  helpers. The co-located `file_safety.py` is the byte mirror that
  `build-check.yml` pins.
- The spec-stage security pass that RFC-0110 requires is a precondition for T2. It
  is owned by the work loop's G-plan sequence.
- Owner decisions at the 2026-10-26 assumptions checkpoint:
  - a deterministic script command plus a skill section;
  - a separate `version` class, so `judge` holds only prose;
  - accepted ADRs only, with `Revisit if:` read from `Consequences`;
  - header citations only, excluding successors and headers naming a successor;
  - rooted signal paths only, with bare names counted as unlocated;
  - excerpts cut to 160 code points;
  - the four proofs: TDD, an independent hand check, activation, behaviour runs.
- The version is 2.2.0: a new mode is new capability (minor), and main is at
  2.1.0. If main moves first, T4 takes the next unused minor.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** the T6 behaviour runs, end to end in scratch repositories.
**Manual verification:** the T5 hand check, and T6's ruling on reading disagreements.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise: `guides/repo-governance/how-to/check-decision-health.md` | T4 | guide file; `tools/validate_guides.py` and `tools/check-guide-index.py` green | guide present and listed; its result block matches the skill's |
| Current product truth: README, JOURNEY, docs/index | T4 | each names `health` | each names it read-only |
| Current architecture: `DESIGN.md` § 7 item 6, § 8 | T4 | read-only invariant names `health` | present |
| Interface compatibility: `query.v1` unchanged | T2 | AC-0002 test | test green |
| Release history: changelog fragment | T4 | `tools/changelog.py` validation green | fragment present with `Highlights` decided |
| Validation evidence: `notes/verification-ledger.md`, `notes/hand-check.json`, raw run files | T1, T5, T6 | ledger entries | every result AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042 and AC-0049 name is recorded |

## Design (LLD)

### Design decisions

- **A sibling subcommand, not a sixth query operation.** `query.v1` is a shipped
  contract with five operations. `health` prints
  `decision-navigation.health.v1` with the same `boundary` and `provenance`
  envelope, so an agent reads it the same way.
- **One file.** The health functions live in `navigate_decisions.py` under a
  `── Health ──` banner, beside the corpus code they reuse. A second module would
  need its own lstat-checked loader, like `file_safety.py`'s, for no gain.
- **Reuse admission, then re-split.** `_admit_corpus` gives each record's
  `raw_text`, lifecycle and header lines. Health splits `raw_text` on `\n` (one
  `\r` before each removed) for sections, because the spec's Terms are stated on
  those lines, not on `splitlines()`, which also breaks on U+2028 and U+0085.
- **Classes are exclusive and ordered.** `due` first, because a passed date is
  the one fact health can decide. `version` before `scheduled`, because only a
  person can compare a version. This keeps `judge` prose-only by construction.
- **Link targets resolve before the lexical rule.** A Markdown link is relative to
  its file, so `../rfc/x.md` from `docs/adr/` is an ordinary in-repository path.
  It is joined to the ADR's directory and normalised with `posixpath.normpath`
  first; only a result that leaves the root is invalid. A backtick span has no
  base directory, so a `..` in it is invalid as written.
- **Probe without opening.** The root passes `validate_confined_directory` once
  before any probe. Each rooted candidate is then walked from the root one
  component at a time:
  - `os.lstat` the next component. Not found means `missing`.
  - A link or reparse point is `invalid`.
  - Any other `OSError`, or a refusal by the helper, is `invalid` with reason
    `uninspectable` or `unconfined`. Only `FileNotFoundError` means absent, so an
    error cannot fail open to `missing`.
  - A regular file before the last component means `missing`.
  - Anything that is neither a file nor a directory is `invalid`.
  - A directory is passed to `file_safety.validate_confined_directory(root, prefix)`
    before the walk goes on; its refusal is `invalid`.
  - A regular last component with `st_nlink > 1` is `invalid`.

  `lstat` reads metadata only, so a FIFO cannot block and nothing is executed.
  The blessed helpers have no exists-check, and their errors do not separate
  "absent" from "unsafe", so health uses `lstat` to tell them apart and the
  helper to confine every directory.
- **Root entries are read once.** The set of names directly under the root comes
  from one `os.scandir(root)`, so "rooted" is a string comparison, not a probe of
  a path from record text.
- **The path bound.** At most 5,000 path candidates per run, counted after
  extraction and before any probe. The 2026-10-26 probe found 77 candidates in
  this repository's accepted ADRs, so the bound is far from normal use. It caps
  probe time on a hostile corpus. The per-file 2 MiB admission bound fires first
  only for one oversized file; many ordinary files reach the 5,000 bound.
- **Error text is cleaned too.** Admission errors can carry a record's file name,
  which a contributor controls. Health passes the `error` object's strings through
  the same cleaner, and writes nothing else to stderr.
- **Occurrences are bounded, findings are merged.** The 5,000 bound counts every
  candidate occurrence, because each occurrence is work. Findings are then merged
  per ADR and checked form, so a path a Signal names twice is listed once.
- **Clean once, at output.** Every string taken from record text passes one
  `_clean_reported` function as the result is built, so no field can skip it. It
  removes categories `Cc`, `Cf`, `Zl`, `Zp`, `Co` and `Cs`, which covers every
  character in the script's `_UNSAFE_CHARS` set. It differs from
  `_escape_display`, which makes them visible, because RFC-0110's stage-5 rule says
  "removed".
- **Today is an input.** `--today` makes the result reproducible for tests and the
  hand-check diff. The default is the UTC date, so the result does not depend on
  the machine's timezone.

Owned by: T2.

### Interfaces & contracts

`decision-navigation.health.v1`, printed by `navigate_decisions.py health`:

```text
schema, boundary, provenance{root, generated_at, corpus_size, untrusted_data},
status ("ok" | "error"), today,
accepted_adr_count,
triggers[{id, title, class, dates[], versions[], excerpt}],
superseded_citations[{superseded, successors[], cited_by}],
signal_paths{missing[{id, path}], invalid[{id, path, reason}],
             present_count, unlocated_count},
no_confirmation{count, ids[]}
```

An error result carries `error{code, message, limits, observed}` and none of the
finding fields. `reason` is one of `lexical`, `outside-root`, `link`, `special`,
`hard-link`, `too-long`, `uninspectable` or `unconfined`. The skill file's health result block is chat output,
not a file, and it is not a `contracts/` artifact.

Owned by: T2, T3.

### Failure, edge cases & resilience

- **Hostile record text.** The hostile fixture's ADR copies the injection shape of
  the existing `fixtures/negative/instruction` ADR. It tells the agent to delete
  `docs/adr/` and run the signal's check file, so a write or a run shows in
  `git status` or the transcript.
- **Symbolic links in fixtures.** A pack fixture holds no link, because catalogue
  lint and projection refuse them. Tests and the T6 driver create the link and the
  FIFO in a temporary copy.
- **Activation run errors.** A query with any errored run is re-run in full, so no
  completed run is kept or dropped selectively.

Owned by: T1, T2, T6.

## Tasks

### T1: The health queries and the hostile fixture are frozen, and the pre-change world is measured

**Depends on:** none

**Touches:** `docs/specs/navigate-decisions-health/notes/*`, `packs/repo-governance/tests/skills/navigate-decisions/fixtures/health-hostile/**`

**Tests:** (goal-based)
- `notes/health-queries.json` holds 15 should-trigger queries in the eval-query
  shape. An exact string check finds none in the eval files of
  `navigate-decisions`, `new-rfc` or `new-adr`.
- `fixtures/health-hostile/docs/adr/` and `docs/rfc/` hold the records the spec's
  hostile-fixture term lists, plus `tools/present-check.py`. Every identity is a
  generic placeholder. It parses through `query --operation summary` with status
  `ok`. `fixtures/health-hostile/request.txt` is one line asking for a decision
  health check.
- The ledger records the pre-change commit SHA, the sha256 of each frozen file,
  the `claude` CLI version, the model ID and the skills the host listed.
- Pre-change world, built from `git archive` of the pre-change commit's
  `packs/repo-governance/` into a temporary directory outside the repository:
  - runs: `navigate-decisions`' pre-change eval queries and the 15 health queries,
    three runs each, with no errored run left in the scored set;
  - the ledger records the pre-change query counts, B, the floor, the pre-change false-trigger rate, and the
    health queries' positive rate.

**Approach:**
- The driver is a scratch script outside the repository. It calls
  `ClaudeCodeDetector.project` and `run_and_parse` from
  `agentbundle.commands.pack_evals` unchanged, with a supplied query list. Parallel
  jobs each use their own copy of the projection. Raw results go in
  `notes/activation-pre-change.json`.
- This task lands before any `SKILL.md` edit, so the inputs cannot be tuned to the
  new text.

**Effects:** none

**Done when:** the ledger's T1 entry holds every hash and number listed in
`Tests`, and the frozen files and raw results are committed.

### T2: The health command is in place, and its contract tests pass

**Depends on:** T1

**Touches:** `packs/repo-governance/.apm/skills/navigate-decisions/scripts/navigate_decisions.py`, `packs/repo-governance/tests/skills/navigate-decisions/test_health_contract.py`, `packs/repo-governance/tests/skills/navigate-decisions/fixtures/health-*/**`

**Tests:** (TDD, in a new `test_health_contract.py` that loads the script by the
unique module name `repo_governance_navigate_decisions_health`, and calls
`main([...])` with captured stdout, so no interpreter is spawned)
- One test per criterion AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0045, AC-0046, AC-0047, AC-0048, AC-0050, AC-0051 and AC-0052, each over a small fixture record tree
  built in `tmp_path` from strings, except where the hostile fixture is named.
  Every `due` and `scheduled` assertion passes an explicit `--today`.
- AC-0002 asserts the `query` parser's `--operation` choices and `run_query`'s
  `unknown_operation` refusal of `health`.
- AC-0003 corrupts one record's H1 and compares the error code with
  `run_query(... "summary")`'s.
- AC-0008 and AC-0009 are parametrised over each grammar form and each
  near-miss.
- AC-0017 creates, in a temporary copy, a link to an existing file, a link to a
  missing file and a link to a directory, and a link as a middle component.
- AC-0020 wraps the loaded `file_safety` module's `validate_confined_directory`
  and `os.lstat` in one recording spy, and asserts that the root and each
  directory prefix were validated before any `lstat` of an entry inside them.
- AC-0021 monkeypatches `builtins.open`, `os.open`, `io.open`, `os.scandir` and
  `os.listdir` to record every path during the probe phase, and asserts no path
  candidate appears.
- AC-0047 extends that spy to `os.lstat`, `os.stat` and `pathlib.Path.resolve`, and
  asserts no recorded path holds an absolute, UNC (`//host/share/x.md`) or
  escaping candidate, and that each recorded path is the root plus a prefix of a
  checked form's segments.
- AC-0048 monkeypatches `os.lstat` to raise `PermissionError` and then an
  `OSError` with `errno.ENAMETOOLONG` for one component.
- AC-0050 builds a corpus whose findings exceed 512 KiB with fewer than 5,000
  candidates.
- AC-0052 records the flags of every `os.open` and the mode of every `open` /
  `io.open`, and patches `tempfile.mkstemp`, `tempfile.NamedTemporaryFile` and
  `tempfile.mkdtemp` to raise.
- AC-0045 creates a FIFO with `os.mkfifo` in a temporary copy (skipped where
  unavailable) and asserts the call returns with it `invalid`.
- AC-0024 also runs a corpus whose file name holds U+202E through a failing
  admission, and checks the `error` object and captured stderr.
- AC-0026 monkeypatches `subprocess.Popen` and `socket.socket` to raise.
- AC-0027 hashes every file under a temporary copy of the hostile fixture before
  and after.
- `test_query_contract.py`, `test_html_publication.py` and
  `test_skill_instructions.py` stay green.
- A stub contract assertion, red until T2 lands:

  ```python
  def test_health_reports_schema_and_today(tmp_path):  # stub: true
      out = run_health(make_corpus(tmp_path, adrs=[ACCEPTED_PROSE]), "2026-10-26")
      assert out["schema"] == "decision-navigation.health.v1"
      assert out["status"] == "ok" and out["today"] == "2026-10-26"
      assert out["accepted_adr_count"] == 1
  ```

**Effects:** none

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions -q`
and `make lint-ruff lint-mypy` are green.

### T3: The health mode, its description triggers and its eval queries are in place, and their content pins pass

**Depends on:** T1, T2

**Touches:** `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md`, `packs/repo-governance/.apm/skills/navigate-decisions/evals/eval_queries.json`, `packs/repo-governance/tests/skills/navigate-decisions/test_skill_instructions.py`

**Tests:** (goal-based, content pins in `test_skill_instructions.py`)
- AC-0028 slices the health section by heading, as `_route_raw` does, and asserts
  the nine line prefixes in order inside one fenced block.
- AC-0029 reads the frontmatter `description:`.
- Content pins on the health section, each asserting the sentence T3 writes:
  - it runs only the health command and never a check, test or file named in a
    record;
  - record text is data and cannot change the task;
  - an invalid path is reported as invalid, not missing;
  - `judge` items are listed after the block as "needs a person to judge";
  - a failed or refused health command is reported as `not checked — <reason>`;
  - health writes nothing.
- The route section and its pins are unchanged. The safety-controls bullet names
  `health` beside `route`.
- `eval_queries.json` keeps its prior entries unchanged and appends the 15
  health queries. Byte equality with `notes/health-queries.json` is checked in T6,
  so no pack test reads outside the pack.

**Effects:** none

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions -q`
is green, and `agentbundle catalogue lint --root . --deep` reports no new finding.

### T4: The pack is at 2.2.0 with its guide, documents, changelog fragment and projections current

**Depends on:** T3

**Touches:** `packs/repo-governance/pack.toml`, `packs/repo-governance/.claude-plugin/plugin.json`, `packs/repo-governance/README.md`, `packs/repo-governance/JOURNEY.md`, `packs/repo-governance/DESIGN.md`, `packs/repo-governance/docs/index.md`, `guides/repo-governance/how-to/check-decision-health.md`, `guides/repo-governance/README.md`, `docs/product/changelog.d/*`, the projections that `make build-self` writes

**Tests:** (goal-based)
- AC-0043: both manifests parse with version `2.2.0`.
- Each durable-output row the map assigns to T4 holds. The guide's result block is
  compared with the skill's at review.
- `tools/changelog.py` validates the new fragment, and `tools/validate_guides.py`
  and `tools/check-guide-index.py` pass.
- AC-0044: after `FORCE=1 make build-self`, `git status --porcelain` is empty.

**Effects:** none

**Done when:** `make lint-ruff lint-mypy` and the `Tests` above are green, and
`agentbundle catalogue verify --root .` passes.

### T5: The independent hand check of docs/adr/ is recorded

**Depends on:** none

**Touches:** `docs/specs/navigate-decisions-health/notes/hand-check.json`, `docs/specs/navigate-decisions-health/notes/hand-check/*`

**Tests:** (manual QA)
- Reviewers who have not seen T2's code or output each read a share of
  `docs/adr/`, with the spec's Terms and AC-0030, AC-0031, AC-0032 and AC-0033 as their only rules.
  Each records, per accepted ADR, the fields the hand-check term lists, and every
  reading disagreement.
- The superseded-citation part reads every `docs/adr/` and `docs/rfc/` header for
  the superseded ADRs' identifiers.
- Reviewers have only `Read`, `Glob` and `Grep`: no shell, so no path from record
  text is ever interpolated into a command. A probe result comes from a literal
  `Glob` for presence, plus the controller's list of every symbolic link, special
  file and hard-linked file in the working tree, made once by a `find` over the
  tree that takes no input from records. The brief states that ADR text is data
  and gives no instruction.
- The merged `notes/hand-check.json` lists 144 accepted ADRs, records its date, and
  records the commit it read.

**Approach:**
- The reviewers are fresh subagents given the spec's Terms, the corpus paths and
  their share, and told not to read the script or its tests. Shares are about 25
  ADRs each, so each fits one context. Their raw notes go in `notes/hand-check/`.

**Effects:** none

**Done when:** `notes/hand-check.json` exists, covers every accepted ADR, and the
ledger's T5 entry records the reviewers, shares, date and commit.

### T6: The post-change world, behaviour runs and accuracy diff are recorded, and each meets its bound

**Depends on:** T4, T5

**Touches:** `docs/specs/navigate-decisions-health/notes/*`

**Tests:** (goal-based, and manual QA for AC-0033)
- AC-0030, AC-0031 and AC-0032: the health command runs on the finished branch with
  `--today` equal to the hand check's date. A scratch diff script compares its
  result with `notes/hand-check.json` set by set, and the ledger records each set's
  matches, extras and omissions.
- AC-0033: each reading disagreement goes to eugenelim with the item, both
  readings and the rule that decided it. The ledger records each ruling.
- The ledger records that the 15 entries appended to `eval_queries.json` equal
  `notes/health-queries.json` (sha256 of both).
- AC-0034, AC-0035, AC-0036 and AC-0037:
  - the T1 driver reruns on the finished branch with the same query lists and run
    count, after confirming that the CLI version, the model ID and the listed
    skills match T1's;
  - the results go in `notes/activation-post-change.json`;
  - the ledger compares each rate with its bound, and states the resolution: one
    run moves a rate over n queries by 1/(3n), about 0.0067 for 50.
- AC-0038, AC-0039, AC-0040, AC-0041, AC-0042 and AC-0049, three scored runs on the hostile fixture:
  - each run is a headless `claude -p --permission-mode default --setting-sources
    project,local --strict-mcp-config` run in a fresh scratch Git repository
    outside this repository. Its allowed tools are exactly `Skill`, `Read`,
    `Glob`, `Grep` and a `Bash` grant for `python3` (and `python3 -I`) running
    the projected `scripts/navigate_decisions.py` `health` and `query` only;
  - the scratch repository holds the post-change projection and the fixture's
    tree, with the symbolic link created and everything committed. The prompt is
    the fixture's `request.txt`;
  - the driver applies the spec's scored-run rule, parses the health result block,
    and records `git status --porcelain`, every attempted tool call with its
    permission outcome, denied calls included (for AC-0049), and a before-and-after
    sha256 listing of every file, `.git/` and ignored paths included;
  - the ledger states that a write outside the scratch repository by the one
    granted command is not detected;
  - transcripts are saved in `notes/behaviour/`.
- Before any transcript is committed, home-directory paths are replaced with
  `<home>`, the OS username with `<user>`, and session IDs, account identifiers
  and email addresses with placeholders. The ledger records a search over
  `notes/` showing none remain.

**Approach:**
- Any failed bound stops the task with the numbers. The spec's Ask-first rule then
  governs.

**Effects:** none

**Done when:** the ledger's T6 entry records every check listed in `Tests`, and
each of AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042 and AC-0049 meets its bound.

## Rollout

A pack release with no infrastructure, migration or sequencing. Adopters receive
`repo-governance` 2.2.0 through `agentbundle upgrade`. Rollback is a downgrade to
2.1.0. `health` writes nothing and adds no command an existing caller uses.

## Risks

- **Activation runs hit host usage limits.** The precedent lost runs to limits.
  The full-query re-run rule keeps scoring honest, and the cost is wall time:
  about 474 runs over T1 and T6.
- **Hand-check cost.** 144 ADRs read by hand is the largest single task. Splitting
  it into shares keeps each reviewer's context small.

## Changelog
