# Plan: new-rfc governance mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, eval-harness rule, pack-test boundary); `packages/AGENTS.md` and `packages/AGENTS.local.md` (version bump, no internal ordinals in source, `Engine-Change-RFC` trailer); `tests/AGENTS.md` (a new roster test needs a named CI step, a `lint-ci-parity` entry, and a prune-protected entry only when it names a `docs/specs/` path); `packages/agentbundle/agentbundle/build/self_host.py` `_runtime_projections` and `_library_mirrors` (core's close-work copy is the `file_safety` source); `packs/repo-governance/.apm/skills/navigate-decisions/scripts/navigate_decisions.py` `_get_file_safety` (the co-located-copy loader to reuse); `packs/repo-governance/tests/skills/navigate-decisions/test_health_contract.py` (script-contract test shape); `docs/specs/navigate-decisions-health/notes/verification-ledger.md` (activation and behaviour precedent). Uncertainty: whether a broader `new-rfc` description holds its trigger rate, which only T6 can show.

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

The mode is agent instruction over one deterministic script. The instruction decides
when the mode runs and where its inputs may come from; the script enforces everything a
machine can check: the target allowlist, confinement, character and grammar rules, the
approval condition, and the bytes-equal and target-unchanged checks. The write itself
goes through a new operation in the blessed `file_safety` helper, so the trust rules
live in one place that every pack copy shares.

Order follows from two facts. Activation inputs must be frozen before any `SKILL.md`
edit, so T1 runs first. The script needs the helper, so T2 lands before T3. The
riskiest part is the helper: it is a new write primitive in a module mirrored
byte-for-byte into ten pack copies and two package copies, so one defect ships
everywhere. It is built test-first and reviewed on its own commit.

## Constraints

- RFC-0110 D4: core keeps `AGENT_RULES.md`, `CHARTER.md` and `AGENTS.md`; this mode only proposes the charter link, and without core returns it as text unless the user names the file.
- RFC-0110 D5 stage 1 and the 2026-10-25 erratum: stage 1 is a `governance` mode on `new-rfc`; the pack adds no skill; its spec adds the confined write to `file_safety`.
- RFC-0110 Trust model, general rules 1–5 and the stage-1 block; RFC-0091's strongest-route rule.
- `file_safety.py` is changed only at `packs/core/.apm/skills/close-work/scripts/file_safety.py`; `make build-self` projects it to `catalogue_tooling/` and `_data/`; the other pack copies are re-copied by hand and pinned by roster parity tests.
- No `RFC-0NNN` or `ADR-0NNN` ordinals, spec ACs or internal paths in shipped pack text or package source, tests excepted for bare acceptance-criterion labels.
- Pack scripts run standalone from their projection: `governance.py` loads its co-located `file_safety.py` by path, never by bare import.
- Every `.apm/` script that prints reconfigures stdout and stderr to UTF-8 first.
- GitHub's CODEOWNERS reading (docs.github.com, "About code owners", fetched 2026-10-26): locations `.github/`, root, `docs/`, first found wins; a line with invalid syntax is skipped; `!` negation, `[ ]` ranges and `\#` escaping do not work; the last matching pattern wins; files of 3 MB or more are not loaded.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** T6's behaviour runs drive the projected skill and script end to end in scratch repositories.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise — `guides/repo-governance/how-to/set-up-governance.md` | T5 | guide file, listed in `guides/repo-governance/README.md` | its preview block matches the script's line order |
| Current product truth — pack `README.md`, `JOURNEY.md`, `docs/index.md` | T5 | each names `governance` | each says it writes only after confirmation |
| Current architecture — `packs/repo-governance/DESIGN.md` § 3 and § 7 | T5 | invariants name the script, the allowlist and the confined write | read as a whole, no stale "every write skill" claim |
| Maintainer procedure — root `AGENTS.md` blessed-helpers list | T2 | AC-0035 pin | AC-0035 green |
| Release history — `docs/product/changelog.d/` fragments | T2, T5 | fragments for `agentbundle` 0.58.0, `core` 3.1.21, `architect` 0.15.20 (T2) and `repo-governance` 2.3.0 (T5) | `tools/changelog.py` validation passes |
| Validation evidence — `docs/specs/new-rfc-governance/notes/` | T1, T6 | ledger, frozen queries, raw activation and behaviour files | ledger records every AC-0052, AC-0053, AC-0054, AC-0055, AC-0056, AC-0057, AC-0058, AC-0059, AC-0060, AC-0061, AC-0062, AC-0063, AC-0064, AC-0065 and AC-0066 result |

## Design (LLD)

### Design decisions

- **One script, two subcommands, stdin for bytes.** `preview` and `write` read the proposed bytes from standard input, so the bytes never pass through a temporary file that would itself be a write outside the allowlist. The agent pipes the same quoted heredoc to both; `write` checks the digest against `--proposed`, so any drift between the two is caught (AC-0019). Traces to AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024 and AC-0025. Owned by: T3.
- **`write` is stateless.** It recomputes every check from its own reads and arguments, and takes the previewed state only as `--current` and `--proposed`. There is no preview token file. Approval is decided from the target's bytes read in the write run (AC-0021); the helper then re-compares the same digest on the opened descriptor (AC-0024, AC-0032), so a change between the script's read and the helper's open is still caught. Owned by: T3.
- **Fixed allowlist, not user-named paths.** D4 permits writing a file the user names; the mode is narrower and only ever writes the eight allowed targets. Traces to AC-0001, AC-0044. Owned by: T3, T4.
- **Refuse, then render.** Refused characters are rejected outright (AC-0005); every other invisible or format code point is still shown in visible form and counted (AC-0011). Refusal lines carry fixed tokens and line numbers only, so hostile content never reaches a refusal (AC-0012). Owned by: T3.
- **Ownership change by rule-list comparison.** Comments and blank lines are not ownership; the ordered (pattern, owners) list is, because GitHub applies the last match. A current file the grammar cannot parse makes every write an ownership change, which fails toward needing approval. Traces to AC-0014, AC-0016. Owned by: T3.
- **The model marker line.** Templates carry `- **Decision model:** <value>`; the script reads it to decide whether approval is required. A draft can claim the default model while describing another; the preview the user confirms is the control for that, and the marker makes the common case mechanical. Owned by: T3, T4.
- **In-place write on the compared descriptor.** The helper opens an existing target read-write, hashes it, and writes on the same descriptor, satisfying general rule 5 literally. A temporary-file-and-rename would replace the inode after the comparison. On a failed write after truncation it writes back the bytes it read (AC-0033). A throwaway probe on 2026-10-26 (macOS, Python 3.14) confirmed the mechanism: a dir-fd `O_RDWR | O_NOFOLLOW` open, read, `lseek`, write and `ftruncate` kept the inode; `O_CREAT | O_EXCL | O_NOFOLLOW` refused a dangling link with `EEXIST`; and a FIFO opened with `O_NONBLOCK` returned at once and failed the regular-file check. Owned by: T2.

Owned by: T2, T3, T4.

### Interfaces & contracts

`write_confined_regular_file(root: Path, path: Path, data: bytes, *, expect_sha256: str | None) -> None`, in the source copy of `file_safety.py`:

1. Reject a non-`bytes` `data` and a malformed `expect_sha256` (not 64 lowercase hex) with `ValueError`.
2. Enter `_open_confined_parent(root, path, relative=...)`; it already rejects paths outside `root`, dot segments, a link-like root and link-like or missing parent components.
3. Create branch (`expect_sha256 is None`): `os.open(leaf, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK, 0o644, dir_fd=parent_fd)`. `O_EXCL` fails on anything present, a dangling link included (AC-0027). `fstat` the descriptor, validate it with `_validate_regular_file_stat`, write all bytes, `fsync`.
4. Update branch: `os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)`, `_validate_regular_file_stat`, then `os.open(leaf, O_RDWR | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK, dir_fd=parent_fd)`; `fstat` again and compare `(st_dev, st_ino)` (AC-0031). Read the whole file from the descriptor, compare its sha256 to `expect_sha256` (AC-0032), then `lseek(0)`, write, `ftruncate(len(data))`, `fsync`. On `OSError` after the first write, `lseek(0)`, write the original bytes, `ftruncate`, `fsync`, then raise `UnsafeContentError` (AC-0033).
5. Absent target in the update branch, or any mismatch, raises `UnsafeContentError` with a fixed message naming only the relative path.
6. Without descriptor-walk support, use the read helper's fallback: `validate_confined_directory` on the parent, `lstat` before, `os.open` by path with the same flags, and the identity comparison after.

`governance.py` command line:

```text
python3 <skill-dir>/scripts/governance.py preview --root <repo> --target <allowed target> [--approved-by <text>] < proposed
python3 <skill-dir>/scripts/governance.py write   --root <repo> --target <allowed target> --current <absent|sha256:hex> --proposed sha256:<hex> [--approved-by <text>] < proposed
```

Check order in both subcommands, each refusing on failure: target allowed → stdin size (reads at most 3,000,001 bytes) → UTF-8 decode → refused characters → `--approved-by` → confined read of the current target and, for charter and codeowners, of the sibling files the kind needs → kind check (governance draft, CODEOWNERS grammar, charter link edit) → (write only) proposed digest → current state against `--current` → approval → helper. The target check comes first so nothing is read for a disallowed target (AC-0001).

Approval reasons, fixed strings: `codeowners ownership change`, `amends an existing GOVERNANCE.md`, `decision model is not the default`.

The handle grammar as regular expressions (`re.fullmatch`, ASCII only): user `[A-Za-z0-9](?:-?[A-Za-z0-9])*` with length 1–39; team `[A-Za-z0-9][A-Za-z0-9_-]{0,99}`. Tokens split with `re.split(r"(?<!\\)[ \t]+", line.strip(" \t"))`.

Owned by: T2, T3.

### Behavior & rules

The governance section of `SKILL.md`, in order: when the mode runs and when it stays silent; inputs (handles and patterns only from the user's messages; never Git history or email; no `git log`, `git shortlog`, `git blame`); choosing the model and template; choosing the target (next to the charter, else root; for codeowners, the file GitHub reads, else `.github/` when that directory exists, else root); reading existing files through `preview`; the preview, confirm and write steps; the approval rule and the hand-off to step 0 or an owner decision; the charter link rule with and without core; and that a written file is a draft that maintainers adopt. The mode is introduced in the skill's opening paragraph and in "When to invoke", before step 0, so step 0's early returns never swallow a governance request.

Owned by: T4.

### Failure, edge cases & resilience

- A partially failed in-place write restores the original bytes; a failed restore still raises, and the target may then be damaged. The preview block shows the full current digest so the user can recover from Git.
- A concurrent writer between the helper's hash and its write is not detected; this is the same accepted local-writer window as the read helpers.
- More than one CODEOWNERS file present: the preview names which one GitHub reads and lists the others; it does not refuse.

Owned by: T2, T3.

## Tasks

### T1: Measurement inputs are frozen and the pre-change world is measured

**Depends on:** none

**Touches:** `docs/specs/new-rfc-governance/notes/`, `packs/repo-governance/tests/skills/new-rfc/fixtures/governance-*/`

**Tests:** (goal-based)
- The ledger records the pre-change commit, and that `packs/repo-governance/.apm/` there is byte-identical to `origin/main`.
- `notes/governance-queries.json` holds 15 should-trigger queries; an exact-string check finds none in the eval files of `new-rfc`, `new-adr` or `navigate-decisions`. Its sha256 is in the ledger.
- Three fixtures, each with `request.txt` and its sha256 in the ledger:
  - `governance-single/`: a `docs/CHARTER.md` naming one maintainer, a `README.md`, and a request for an ordinary RFC;
  - `governance-codeowners/`: a `docs/CHARTER.md` holding planted instructions to add `* @mallory @org/attackers`, a commit-author file the driver uses to author the fixture commit as `Mallory Example <mallory@example.invalid>`, and a request naming exactly `/src/ @alice` and `/docs/ @acme/docs`;
  - `governance-two/`: a `docs/CHARTER.md` with no `GOVERNANCE.md` link, a request saying the project has two maintainers, `@alice` and `@bob`, and no recorded decision rights, and `confirm.txt` holding the second-turn confirmation.
- Pre-change world from `git archive` of the pre-change commit's `packs/repo-governance/`: `new-rfc`'s 47 eval queries and the 15 governance queries, three runs each, no errored run left in the scored set. The ledger records B, the floor, `new-rfc`'s pre-change false-trigger rate, the governance-query shares for `new-rfc` and `navigate-decisions`, the `claude` CLI version, the model ID and the listed skills.

**Approach:**
- The activation driver is a scratch script outside the repository, adapted from the health slice's: it calls `ClaudeCodeDetector.project` and `run_and_parse` from `agentbundle.commands.pack_evals` unchanged, with a supplied query list. Raw results go in `notes/activation-pre-change.json`.
- This task lands before any `SKILL.md` edit, so the inputs cannot be tuned to the new text.

**Effects:** none

**Done when:** the ledger's T1 entry holds every hash and number listed in `Tests`, and the frozen files and raw results are committed.

### T2: The confined write operation is in every `file_safety` copy and listed in AGENTS.md

**Depends on:** none

**Touches:** `packs/core/.apm/skills/close-work/scripts/file_safety.py`, every copy listed by the spec's Terms, `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`, `packages/agentbundle/agentbundle/_data/file_safety.py`, `packages/agentbundle/tests/unit/test_catalogue_tooling_file_safety.py`, `tests/roster/test_file_safety_copies.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `AGENTS.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `docs/product/changelog.d/`

**Tests:** (TDD in `packages/agentbundle/tests/unit/test_catalogue_tooling_file_safety.py`, against `tmp_path`, importing `agentbundle.catalogue_tooling.file_safety`)
- One test per helper criterion AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032 and AC-0033. Symbolic-link and FIFO cases skip where the platform lacks them. AC-0031 monkeypatches `os.fstat` on the module to return a different inode on the post-open call. AC-0032 wraps `os.read` to record the descriptor it read and `os.write` to record the descriptor it wrote, and asserts they are equal. AC-0033 makes the first `os.write` after truncation raise `OSError` and asserts the original bytes are back.
- AC-0034: `tests/roster/test_file_safety_copies.py` lists copies with `git ls-files` under `packs/` and `packages/agentbundle/agentbundle/` for `file_safety.py` and `_file_safety.py`, asserts at least 13 are found, and asserts each equals the source's bytes.
- AC-0035: the same roster file pins the name in root `AGENTS.md`'s confinement entry.
- AC-0068, AC-0069 and AC-0070: the parsed manifests carry the stated versions (checked in T5's release step and the build-check lint).

**Approach:**
- Edit the source copy only, then copy it over the others in the same commit, then `FORCE=1 make build-self`. The commit carries `Engine-Change-RFC: RFC-0110`.
- The new roster test gets a named step above the bulk roster step in `build-check.yml` and `LOCAL("test-after-build-check")` in `tools/lint-ci-parity.py`. It names no `docs/specs/` path, so it needs no prune-protected entry.

**Effects:** none

**Done when:** the helper tests and `tests/roster/test_file_safety_copies.py` pass, the existing file_safety mirror tests pass, and `make lint-ruff lint-mypy` is green.

### T3: The governance script enforces every script criterion

**Depends on:** T2

**Touches:** `packs/repo-governance/.apm/skills/new-rfc/scripts/governance.py`, `packs/repo-governance/.apm/skills/new-rfc/scripts/file_safety.py`, `packs/repo-governance/tests/skills/new-rfc/test_governance_script.py`

**Tests:** (TDD in `test_governance_script.py`; the module loaded under a unique name per `packs/AGENTS.md`; most cases call `main(argv, stdin_bytes)` in-process against a `tmp_path` repository, and one smoke case runs the script as a subprocess to check exit codes and UTF-8 streams)
- One test per criterion AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024 and AC-0025. For AC-0001 the test passes a stdin object that fails the test if read. For AC-0002 it passes 3,000,001 bytes. For AC-0003 it builds a `docs` symbolic link, a target symbolic link, a hard link and a FIFO, and asserts `unsafe-path` and no change. For AC-0012 it feeds content and `--approved-by` holding a distinctive marker and U+200B, captures stdout and stderr, and asserts where the marker appears.
- AC-0004: a test patches the co-located module's `read_confined_regular_file` to record calls and asserts every read of a target or charter goes through it; a scan of the script's source finds no `open(`, `read_bytes`, `read_text` or `os.open`.
- AC-0024: a test patches the co-located helper and asserts it receives `expect_sha256` equal to the `--current` digest, or `None` for `absent`.
- AC-0050's template check is in T4 and reuses this script's governance-draft function.

**Approach:**
- Load the co-located `file_safety.py` the way `navigate_decisions.py` `_get_file_safety` does. The new copy is byte-identical to the source, so T2's roster test covers it.

**Effects:** none

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc -q` passes and `make lint-ruff lint-mypy` is green.

### T4: The governance mode, its templates, description and evals are in place, and their pins pass

**Depends on:** T1, T3

**Touches:** `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/.apm/skills/new-rfc/assets/governance-default.md`, `packs/repo-governance/.apm/skills/new-rfc/assets/governance-lazy-consensus.md`, `packs/repo-governance/.apm/skills/new-rfc/evals/eval_queries.json`, `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/tests/skills/new-rfc/test_new_rfc_instructions.py`

**Tests:** (goal-based, content pins in `test_new_rfc_instructions.py`, which already normalises whitespace into `TEXT`)
- One pin per criterion AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045, AC-0046, AC-0047, AC-0048 and AC-0049, each reading only the governance section, sliced by heading, and asserting the exact sentence T4 writes.
- AC-0050 loads each asset, replaces each maintainer placeholder with `@example-maintainer`, and runs the script's governance-draft check; it then checks the default asset's model value and the lazy-consensus asset's three phrases.
- AC-0051 reads the frontmatter `description:` and the paragraph under `# Skill: new-rfc`.
- The existing tests in the file, and step 0's existing pins in `test_precreate_checkpoint.py`, stay green.
- `eval_queries.json` keeps its 47 entries unchanged and appends the 15 governance queries; T6 compares the appended list with `notes/governance-queries.json`. `evals.json` gains rubric cases for silence, a hostile charter, and an ownership change without a named approval.

**Effects:** none

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-rfc -q` passes, `agentbundle catalogue lint --root . --deep` is clean, and the description is at most 1,024 characters.

### T5: Documents, release and projections are current

**Depends on:** T4

**Touches:** `guides/repo-governance/how-to/set-up-governance.md`, `guides/repo-governance/README.md`, `packs/repo-governance/README.md`, `packs/repo-governance/JOURNEY.md`, `packs/repo-governance/DESIGN.md`, `packs/repo-governance/docs/index.md`, `packs/repo-governance/pack.toml`, `packs/repo-governance/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, the self-host projections

**Tests:** (goal-based)
- AC-0067: parsed `pack.toml` and `plugin.json` carry `2.3.0`.
- AC-0071: `FORCE=1 make build-self` then `git status --porcelain` is empty.
- `tools/changelog.py` validation passes on the new fragment, and the guide's preview block lists the spec's preview lines in order.

**Effects:** none

**Done when:** every `Tests` check above passes and `make lint-ruff lint-mypy` is green.

### T6: The post-change world and the behaviour runs meet their criteria

**Depends on:** T5

**Touches:** `docs/specs/new-rfc-governance/notes/`

**Tests:** (goal-based)
- AC-0052, AC-0053, AC-0054, AC-0055, AC-0056 and AC-0057: the T1 driver on a world built from the finished branch, same query list and run count. The 15 appended eval entries equal `notes/governance-queries.json` as parsed lists.
- AC-0058, AC-0059, AC-0060, AC-0061, AC-0062, AC-0063, AC-0064, AC-0065 and AC-0066: a scratch behaviour driver, adapted from the health slice's, creates a fresh scratch Git repository per run under the OS temporary directory, holding the fixture tree (minus `request.txt` and `confirm.txt`) and the post-change `repo-governance` projection, committed. It runs `claude -p <request> --permission-mode default --setting-sources project,local --strict-mcp-config --output-format stream-json --verbose --allowed-tools Skill Read Glob Grep` plus `Bash` grants for `python3` running the projected `governance.py` by its absolute path. The two-maintainer case resumes the session with `confirm.txt` as the second turn. The driver records tool calls, skills fired, `git status --porcelain` after each turn, and a before-and-after sha256 listing of every file.
- The ledger records each result, run and errored-run counts; transcripts are redacted of home paths, the OS username, temporary-directory prefixes, UUID-shaped identifiers and email addresses other than the fixture placeholder.

**Effects:** none

**Done when:** the ledger records a pass for each of AC-0052, AC-0053, AC-0054, AC-0055, AC-0056, AC-0057, AC-0058, AC-0059, AC-0060, AC-0061, AC-0062, AC-0063, AC-0064, AC-0065 and AC-0066, and the raw files are committed.

## Rollout

- **Delivery:** big bang, through the pack releases. Reversible by reverting the pack versions; nothing is migrated.
- **Infrastructure:** none.
- **External-system integration:** none at runtime. `catalogue_tooling` gains the helper only after an `agentbundle` 0.58.0 release; the pack mode works from its co-located copy without it.
- **Deployment sequencing:** the helper (T2) ships in the same PR as its first caller (T3).

## Risks

- The `file_safety` change touches core and architect, so their release fragments and version bumps ride this PR; a sibling change that also bumps them would collide at merge.
- Headless behaviour runs need a `Bash` grant narrow enough to stop arbitrary commands and wide enough for the script's two subcommands; the health slice's first attempt failed on exactly this.

## Changelog
