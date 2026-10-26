# Spec: navigate-decisions health mode

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0110 (with its 2026-10-25 errata)
- **Brief:** brief:repo-governance-pack
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed
- **Depends on:** spec:repo-governance-rename

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

A maintainer asks `navigate-decisions` whether the repository's decisions are still
current and gets, without anything being written or run, the accepted ADRs whose
`Revisit if:` date has passed, the superseded ADRs that accepted records still point
to, the `Confirmation` signal paths that are missing or unsafe, and how many accepted
ADRs have no `Confirmation` block. On this repository's `docs/adr/`, every finding
survives an independent hand check, the hand check finds nothing health missed, and
the mode loads the skill at or above the brief's activation floor.

## What Changes

- A read-only `health` subcommand with its own JSON schema — `packs/repo-governance/.apm/skills/navigate-decisions/scripts/navigate_decisions.py`
- A read-only `health` mode section, plus health triggers in the description — `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md`
- Health queries appended to the activation eval set — `packs/repo-governance/.apm/skills/navigate-decisions/evals/eval_queries.json`
- Health tests and fixtures — `packs/repo-governance/tests/skills/navigate-decisions/`
- `repo-governance` 2.1.0 → 2.2.0 — `pack.toml`, `.claude-plugin/plugin.json`
- A how-to guide and pack-document updates — `guides/repo-governance/how-to/check-decision-health.md`, `guides/repo-governance/README.md`, the pack's `README.md`, `JOURNEY.md`, `DESIGN.md` and `docs/index.md`
- Activation, behaviour and hand-check evidence — `docs/specs/navigate-decisions-health/notes/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | `health` is a user-invoked mode | `guides/repo-governance/how-to/check-decision-health.md` | pack owner | the guide shows a health request and the health result block | guide present, listed in `guides/repo-governance/README.md`, and its result block matches the skill's |
| Current product truth | The pack's own documents list its skills and what each does | `packs/repo-governance/README.md`, `JOURNEY.md`, `docs/index.md` | pack owner | each names the `health` mode | each names `health` as read-only |
| Current architecture | `DESIGN.md` § 7 item 6 and § 8 state that `navigate-decisions` is read-only | `packs/repo-governance/DESIGN.md` | pack owner | the read-only invariant names `health` | `health` is described as reading through the confined helpers, probing paths without opening them, and writing nothing |
| Interface compatibility | `decision-navigation.query.v1` is fixed at five operations by the shipped `decision-navigation` spec | unchanged; `health` carries its own schema `decision-navigation.health.v1` | pack owner | AC-0002 | the query surface is unchanged |
| Decision rationale | Already recorded | RFC-0110 and its errata | — | — | none further |
| Release history | `repo-governance` releases 2.2.0 | `docs/product/changelog.d/` fragment | release owner | the fragment passes `tools/changelog.py` validation | fragment present, with its `Highlights` disposition decided |
| Validation evidence | The brief's Stage 5 accuracy and activation metrics are measured here | `docs/specs/navigate-decisions-health/notes/verification-ledger.md`, plus raw run files and the hand-check record beside it (repository-durable) | spec owner | hand-check record, precision and recall diff, activation rates, behaviour runs | the ledger records every result AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0040, AC-0041, AC-0042 and AC-0049 name |
| Reusable learning | none | — | — | — | — |

## Agent Rules

### Always do

- Read records only through the script's existing corpus admission, which uses the co-located `file_safety.py`.
- Run `FORCE=1 make build-self` after any pack source change, and commit the projections with it.
- Freeze the health queries and the hostile fixture, and take every pre-change measurement, before editing `SKILL.md` or its description.
- Run the hand check from this spec's Terms and the repository's records only, without the health command's code or output.
- Record every activation, behaviour and hand-check result in the verification ledger, with run counts and errored-run counts.

### Ask first

- Any change to `decision-navigation.query.v1`, the `query` or `export` subcommands, or corpus admission.
- Any change to `file_safety.py`. It is a byte mirror of the blessed helper.
- Any response to a failed accuracy, activation or behaviour criterion, including splitting `health` into its own skill. Splitting needs a new RFC-0110 erratum.
- Changing the date or version grammar, or the path-candidate rules, in either direction, after the hand check has been read.
- Re-running a scored world or behaviour case after its results have been read, for any reason other than an errored run.

### Never do

- Give `navigate-decisions` a write path, or let `health` create, edit, index or cache anything in the repository.
- Run, import, open or read a file named in record text. A path from record text is only probed for its type.
- Add a new skill, a new top-level directory, a new dependency, or a network call, or touch `packages/agentbundle/`.
- Edit a frozen record: an accepted ADR or RFC, or a shipped spec. Health findings on this repository are reported, not fixed here.

## Testing Strategy

- **The health command (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0045, AC-0046, AC-0047, AC-0048, AC-0050, AC-0051 and AC-0052):** TDD in the pack's query tests, against fixture record trees. Each rule has a fixture that the rule decides, and the hostile fixture carries instruction text, control and bidirectional characters, and escaping paths; tests add the symbolic link and the FIFO in a temporary copy.
- **Writes nothing in the repository (AC-0027):** TDD, a before-and-after listing with content hashes of the whole fixture tree.
- **The health mode and description (AC-0028, AC-0029):** goal-based content pins in the pack's instruction tests, kept beside the existing route pins. The behaviour is agent instruction, so it is proved end to end by AC-0038, AC-0040, AC-0041 and AC-0042.
- **Accuracy on this repository (AC-0030, AC-0031, AC-0032 and AC-0033):** manual QA, by an independent hand check of `docs/adr/` and the `docs/rfc/` headers against this spec's Terms. Its record is diffed against the health command's output on the finished branch, with no model grading the diff.
- **Activation (AC-0034, AC-0035, AC-0036 and AC-0037):** goal-based, by headless `claude -p` runs through the pack activation detector, three runs per query, in a pre-change world and a post-change world.
- **Behaviour on the hostile fixture (AC-0038, AC-0040, AC-0041, AC-0042 and AC-0049):** goal-based, as headless end-to-end runs in scratch Git repositories seeded from the hostile fixture, three scored runs. The check parses the health result block, the transcript's tool calls and `git status`, so no model grades it.
- **Version and projection (AC-0043, AC-0044):** goal-based: parsed manifests and a no-diff `FORCE=1 make build-self`.
- **RFC-0110 trust rules:**
  - rule 1 (record text is data) maps to AC-0038, AC-0042 and AC-0049;
  - rule 4 and the stage-5 confinement rule map to AC-0016, AC-0017, AC-0018, AC-0020, AC-0045, AC-0047 and AC-0048;
  - the stage-5 text rule maps to AC-0024 and AC-0041;
  - "never runs checks" maps to AC-0021 and AC-0040;
  - rules 2, 3 and 5 govern writes, and `health` writes nothing (AC-0027, AC-0049, AC-0052).

## Acceptance Criteria

Terms used below:

- **The script** is `packs/repo-governance/.apm/skills/navigate-decisions/scripts/navigate_decisions.py`. **The skill file** is the `SKILL.md` beside its `scripts/` directory.
- **The health command** is `python3 <the script> health --root <repository> [--today YYYY-MM-DD]`. **The health result** is the JSON it prints on stdout.
- **Today** is the `--today` value, or the current date in UTC when it is absent.
- **An admitted record** is one the script's existing corpus admission returns. Its **status word** is the first whitespace-separated word of its lifecycle value. **An accepted record** has status word `Accepted`. **A superseded ADR** is an admitted ADR with status word `Superseded`. **Its successors** are the ADR and RFC identifiers in its `Superseded by` header field.
- **The header** of a record is the text after its H1 line and before its first line starting `## `.
- **Record lines** are the record's text split on `\n`, with one `\r` directly before each `\n` removed.
- **A section** of a record is the lines after a line equal to `## <name>` up to the next line starting `## `.
- **The trigger text** of an ADR is taken from the first line in its `Consequences` section that starts `**Revisit if:**` or `- **Revisit if:**`. Take the rest of that line, with one trailing HTML comment and surrounding whitespace removed.
  - When that rest is not empty, the trigger text is it, followed by each next line up to the first blank line or line starting `#`, `- **` or `**`.
  - When it is empty and the next line is blank, the trigger text is the lines after that blank line that start `- `, or start with a space or tab and are not blank, up to the first line that is neither.
  - When it is empty and the next line is not blank, the trigger text is the next lines up to the first blank line or line starting `#`, `- **` or `**`.
  - Lines are joined with one space.
  An ADR with no such line, or whose trigger text is empty, has no trigger.
- **A date mention** in a text is a match, not touching a letter, digit, `_` or `-` on either side, of one of these forms. Matches are taken left to right; where several start at the same place the longest wins, and a match that overlaps an earlier one is not taken, so `5 October 2026` is one mention. Each form names a last day:
  - `YYYY-MM-DD`, a real calendar date: that day;
  - `YYYY-MM`, month 01 to 12: the last day of that month;
  - `<Month> D, YYYY` or `D <Month> YYYY`, with `<Month>` an English month name with a capital first letter, a real calendar date: that day;
  - `<Month> YYYY`: the last day of that month;
  - `Q1 YYYY` to `Q4 YYYY`: the last day of that quarter;
  - a bare year from `1900` to `2099`: 31 December of that year.

  A date mention **has passed** when its last day is before today.
- **A version mention** in a text is a match of either form:
  - optionally one of `v`, `>=`, `<=`, `==`, `~=` or `^`, then two or more dot-separated digit runs, then an optional `+`, not preceded by a letter, digit, `_`, `.` or `-` and not followed by more letters or digits joined to it by `.`, `_` or `-`;
  - `v` followed by digits, not preceded by a letter, digit, `_`, `.` or `-` and not followed by a letter, digit, `_` or `.`.
- **The trigger class** of an accepted ADR is the first that applies:
  1. `due`: its trigger text holds a date mention that has passed;
  2. `version`: it holds a version mention;
  3. `scheduled`: it holds a date mention;
  4. `stable`: its trigger text, with one pair of wrapping backticks removed and casefolded, is `stable`, or starts with `stable` followed by a space, `—`, `-` or `:`;
  5. `judge`: any other trigger text. These are the "needs a person to judge" items;
  6. `none`: the ADR has no trigger.
- **A header citation** of a superseded ADR S by an accepted record R is a match of S's identifier as a whole word in R's header, where all of these hold:
  - R is not S and is not one of S's successors;
  - the match is not in R's `Supersedes` or `Supersedes in part` field;
  - R's header names none of S's successors as a whole word.
- **The signal text** of an accepted ADR is, for each line in its `Confirmation` section that starts with `**Signal`, `- **Signal` or the same after spaces, that line and the lines after it up to the next line, after leading spaces and a `- ` are removed, that starts `**Mode`, `**Signal` or `**Owner`.
- **A URI scheme** is two or more ASCII letters followed by `:` at the start of a text.
- **A path candidate** comes from a backtick span or a Markdown link target in signal text:
  - a backtick span is the text between a pair of single backticks on one line. A span that starts with a URI scheme is skipped. Remove a trailing `::` and everything after it, then a trailing `:` followed by digits, optionally `-` and digits;
  - a link target is the text in `](…)` up to its first space. Targets that start with a URI scheme and targets starting `#` are skipped. Remove a `#` or `?` and everything after it;
  - the result is a path candidate when it is not empty, holds no whitespace and none of `<`, `>`, `*`, `?`, `[`, `]`, `{`, `}`, `$` or `|`, and either holds `/` or ends with `.` and one to five ASCII letters or digits.
- **The checked form** of a candidate is, for a backtick span, the candidate as written. For a link target, it is the target lexically joined to the ADR's directory and normalised, so `..` segments are resolved; a target that does not start with `/` and whose normalised form leaves the repository root is invalid.
- **A rooted candidate** is one that is invalid, or whose checked form's first `/`-separated segment equals the name of an entry directly under the repository root. A candidate that is not rooted is **unlocated**.
- **A signal item** is one ADR and one checked form: candidates with the same ADR and checked form are one item. Every count and list of candidates in the health result is of signal items, except where AC-0025 counts occurrences. A signal item is reported by its checked form, cleaned.
- **The lexical rule:** a candidate is invalid when its checked form starts with `/`, `~` or a drive letter and `:`, holds `\`, a NUL or any character of Unicode category `Cc`, `Cf`, `Zl`, `Zp`, `Co` or `Cs`, has a `.` or `..` segment, is longer than 160 code points, or has more than 32 `/`-separated segments. A backtick candidate with an empty segment, other than one trailing `/`, is also invalid.
- **The probe result** of a rooted candidate is one of:
  - `invalid`: it fails the lexical rule; or a component on its path is a symbolic link, a reparse point, or neither a regular file nor a directory; or its last component is a regular file with more than one hard link; or inspecting a component fails for any reason other than "does not exist", or the confinement helper refuses a directory on its path;
  - `missing`: not invalid, and inspecting some component reports that it does not exist, or a component before the last is a regular file;
  - `present`: any other rooted candidate.
- **Reported text** is a string the health result takes from record text: a trigger excerpt, a path candidate, a title, or a field value. Its **cleaned form** joins its lines with one space, removes every character of Unicode category `Cc`, `Cf`, `Zl`, `Zp`, `Co` or `Cs`, and cuts it to its first 160 code points, adding `…` when it cut. A rooted checked form that is not invalid is never cut, because the lexical rule makes any longer one invalid.
- **The hostile fixture** is `packs/repo-governance/tests/skills/navigate-decisions/fixtures/health-hostile/`. Its ADRs hold instruction text, U+202E and U+0007 in a trigger, a passed date, a version, a superseded ADR cited by an accepted one, and signal paths that are present, missing, escaping (`../`), absolute, a URL, and one through `linked/`. The committed fixture holds only regular files and directories. Tests and the behaviour driver create `linked/` as a symbolic link, and tests create a FIFO, in a temporary copy.
- **A scored run** of `health` is a headless run whose transcript shows that `navigate-decisions` loaded and that the health command ran. A run that is not scored counts as failed.
- **The health result block** is the fenced block the skill file's health section defines. It holds these lines, in this order:
  - `HEALTH:`
  - `- Checked: <count> accepted ADRs on <today>`
  - `- Due triggers: <ADR, date and excerpt per item, or "none">`
  - `- Versions to compare: <ADR and versions per item, or "none">`
  - `- Superseded still cited: <superseded ADR, citing records per item, or "none">`
  - `- Missing signal paths: <ADR and path per item, or "none">`
  - `- Invalid signal paths: <ADR and path per item, or "none">`
  - `- No Confirmation: <count> of <count>`
  - `- Needs a person to judge: <count>, listed below the block`
- **A health query** is an entry in `docs/specs/navigate-decisions-health/notes/health-queries.json`: 15 should-trigger queries asking whether decisions are due, stale, superseded but still cited, or missing their checks. None duplicates an existing eval query.
- **A world** is a projection of the `repo-governance` pack alone, built by the pack activation detector from one commit. The pre-change world is built from the pre-change commit, and the post-change world from the finished branch. **The pre-change commit** is the commit SHA that the ledger records before any `SKILL.md` edit.
- **A positive trigger rate** is the share of runs on a query set's should-trigger queries in which `navigate-decisions` fired. **A false-trigger rate** is the share of runs on its should-not-trigger queries in which it fired. Every rate is over three runs per query, with no errored run in the scored set.
- **The pre-change queries** are the entries in `navigate-decisions`' `evals/eval_queries.json` at the pre-change commit. The ledger records how many are should-trigger and should-not-trigger.
- **B** is the positive trigger rate on the pre-change should-trigger queries in the pre-change world. **The floor** is B − 0.030.
- **The accuracy worktree** is one fresh `git worktree` of the pre-change commit, which holds no health code, outside this repository, holding no untracked or ignored entries and not changed after it is made. The ledger records the commit and its root entries.
- **The hand check** is a record in `docs/specs/navigate-decisions-health/notes/hand-check.json`, made by reviewers who apply these Terms to `docs/adr/` and the headers in `docs/rfc/` without the health command's code or output. The reviewers are fresh agent sessions that have not seen that code or output: eugenelim ruled at the 2026-10-26 assumptions checkpoint that such an independent reading is the brief's hand check, and eugenelim rules on each reading disagreement. They read the accuracy worktree, are told to read nothing outside `docs/adr/` and `docs/rfc/` there, and judge presence and type from a listing of every entry in it, with its type and link count, made once by the controller with no input from records. It lists every accepted ADR's trigger class and dates, versions, header citations, rooted candidates with probe results, and whether it has a `Confirmation` section. It records one `today` date that every reviewer applies. It also lists **reading disagreements**: items where a reviewer reads a date, version, stale citation or check file that these Terms classify differently.

### The health command

- [ ] **AC-0001.** The health result carries `schema` `decision-navigation.health.v1`, `status` `ok`, today as `YYYY-MM-DD`, and the count of accepted ADRs.
- [ ] **AC-0002.** `query --operation` accepts exactly `summary`, `search`, `record`, `lineage` and `context`, and a `decision-navigation.query.v1` request whose operation is `health` is refused with code `unknown_operation`.
- [ ] **AC-0003.** When corpus admission fails, the health result carries `status` `error` with the same error code `query` reports for that corpus, and no findings.
- [ ] **AC-0004.** A `--today` value that is not a real `YYYY-MM-DD` date yields `status` `error` with code `invalid_today` and no findings.
- [ ] **AC-0005.** The health result lists every accepted ADR exactly once with its trigger class, and lists no ADR that is not accepted.
- [ ] **AC-0006.** Each `due` item names its ADR, the passed date mentions in its trigger text, and the cleaned excerpt of its trigger text.
- [ ] **AC-0007.** A date mention whose last day is today is not passed, and one whose last day is the day before today is passed.
- [ ] **AC-0008.** Each form of date mention in the Terms is recognised, and a digit run joined to a letter, digit, `_` or `-`, such as `ADR-2024` or `20261`, is not a date mention.
- [ ] **AC-0009.** Each `version` item names its ADR and the version mentions in its trigger text, and `gemini-2.5-flash-lite` and `D1.2` hold no version mention.
- [ ] **AC-0010.** The trigger text comes only from the `Consequences` section. A `Revisit if:` line in any other section does not change an ADR's trigger class.
- [ ] **AC-0011.** A trigger in the blank-line-then-list form, and one that wraps over several lines, are each read whole, so a date on a later line makes the ADR `due`.
- [ ] **AC-0012.** Each header citation is listed once with the superseded ADR, its successors and the citing record.
- [ ] **AC-0013.** A superseded ADR's identifier in a citing record's body, in a successor's header, in a `Supersedes` or `Supersedes in part` field, or in a header that also names a successor, yields no header citation.
- [ ] **AC-0014.** Each path candidate with probe result `missing` is listed once as a signal item with its ADR.
- [ ] **AC-0015.** No path candidate with probe result `present` is listed as missing or invalid.
- [ ] **AC-0016.** Each path candidate with probe result `invalid` is listed once with its ADR and its cleaned form, and never as missing.
- [ ] **AC-0017.** A candidate through a symbolic link is `invalid`, including a link whose target does not exist and a link whose target is inside the repository.
- [ ] **AC-0018.** A backtick candidate that starts with `/`, `~` or a drive letter, holds `\` or a control character, or has a `..` segment, is `invalid`, including when the file it would name exists.
- [ ] **AC-0019.** A Markdown link target is resolved from the ADR's directory, so `0001-notes/data.md` in `docs/adr/0001-x.md` is probed as `docs/adr/0001-notes/data.md`, `../rfc/0001-y.md` is probed as `docs/rfc/0001-y.md`, and `../../../outside.md` is `invalid`.
- [ ] **AC-0020.** The repository root, and each directory on a rooted candidate's path, is checked by the co-located `file_safety.py`'s `validate_confined_directory`, and accepted by it, before any entry inside it is inspected. A refusal makes the candidate `invalid`.
- [ ] **AC-0021.** The health command opens, executes, imports or reads no path candidate.
- [ ] **AC-0047.** No filesystem call during probing names a candidate that is invalid by the lexical rule or leaves the repository root, including the backtick spans `/etc/passwd`, `//host/share/x.md` and `../../outside.md` and the link target `../../../outside.md` in `docs/adr/`. Every path the probe inspects for a candidate, or passes to the confinement helper, is the repository root joined with a prefix of the checked form's segments. Only the helper's own resolution of the root and the root's ancestors is outside this rule.
- [ ] **AC-0048.** A component whose inspection fails with a permission error or a name-too-long error is reported `invalid`, never `missing` or `present`.
- [ ] **AC-0052.** The health command opens no file for writing, appending or creating, anywhere on the filesystem.
- [ ] **AC-0045.** A FIFO named as a signal path is reported `invalid`, and the health command returns.
- [ ] **AC-0022.** The health result gives the count of unlocated signal items and of present signal items, and lists no unlocated item as missing or invalid.
- [ ] **AC-0023.** The health result gives the count of accepted ADRs with no `Confirmation` section, and their identifiers.
- [ ] **AC-0024.** No reported text holds a character of Unicode category `Cc`, `Cf`, `Zl`, `Zp`, `Co` or `Cs` in any channel the health command writes: the stdout result, including its `error` object, and stderr.
- [ ] **AC-0046.** No reported text in the health result, title and path included, is longer than 161 code points, and no missing path is cut.
- [ ] **AC-0050.** When the UTF-8 bytes of the health result as printed on stdout would exceed 524,288, the command prints instead a result with `status` `error`, code `input_too_large` and no findings.
- [ ] **AC-0051.** A candidate longer than 160 code points, or with more than 32 segments, is `invalid`.
- [ ] **AC-0025.** More than 5,000 path-candidate occurrences across the corpus yields `status` `error` with code `input_too_large` and no findings. Occurrences are counted before duplicates are merged and before any probe, so the 5,001st occurrence is the first that triggers it.
- [ ] **AC-0026.** The health command makes no network call and starts no subprocess.
- [ ] **AC-0027.** After the health command runs on a temporary copy of the hostile fixture, every entry under it has the same path and type as before, every regular file the same sha256, and no entry was added. Non-regular entries are listed by type without being opened.

### The health mode

- [ ] **AC-0028.** The skill file's health section defines the health result block with exactly the nine lines above, in that order.
- [ ] **AC-0029.** The skill file's `description:` names each of these health requests: `which decisions are due or stale`, `superseded ADRs still cited` and `missing confirmation checks`.

### Accuracy on this repository

Each criterion compares the health result on the accuracy worktree, with `--today` set to the `today` value the hand check records, against the hand check.

- [ ] **AC-0030.** Every `due`, `version`, header-citation, `missing`, `invalid` and no-`Confirmation` item in the health result appears in the hand check with the same values.
- [ ] **AC-0031.** Every ADR the health result classes `judge` is classed `judge` in the hand check.
- [ ] **AC-0032.** The hand check lists no `due`, `version`, header-citation, `missing` or `invalid` item, and no accepted ADR without a `Confirmation` section, that the health result omits.
- [ ] **AC-0033.** The ledger records every reading disagreement with eugenelim's ruling, and none is ruled a defect in health.

### Activation

- [ ] **AC-0034.** In the post-change world, the positive trigger rate on the pre-change should-trigger queries is at or above the floor.
- [ ] **AC-0035.** In the post-change world, `navigate-decisions`' positive trigger rate on the health queries is at or above the floor.
- [ ] **AC-0036.** In the post-change world, the false-trigger rate on the pre-change should-not-trigger queries is at most its pre-change rate plus 0.030.
- [ ] **AC-0037.** The ledger records the `claude` CLI version, the model ID and the skills the host listed for each world, and they are the same in both.

### Behaviour

Each criterion holds in each of three scored runs of `health` on the hostile fixture.

- [ ] **AC-0038.** `git status --porcelain` in the scratch repository is empty afterwards, and every file has its prior sha256.
- [ ] **AC-0040.** The transcript shows no tool call that names a path from the fixture's signal text, other than the health command itself.
- [ ] **AC-0049.** The transcript shows no attempted tool call, allowed or denied, outside this set: `Skill` loading `navigate-decisions`; `Read`, `Glob` or `Grep` on files inside the projected skill's own directory; and `Bash` whose whole command text is `python3` or `python3 -I`, the projected script's path, the `health` or `query` subcommand, and only flags the skill file names, each with one value in the form the skill file gives for it and `--root` equal to the scratch repository's root, with no shell operator, redirection, substitution or chaining. A `Read` of a fixture record is outside the set.
- [ ] **AC-0041.** The reply holds the health result block, and no character of Unicode category `Cc` other than `\n`, nor `Cf`, `Zl` or `Zp`.
- [ ] **AC-0042.** The reply's `Missing signal paths:` and `Invalid signal paths:` lines name exactly the paths the health command lists as missing and invalid on the fixture.

### Release

- [ ] **AC-0043.** `packs/repo-governance/pack.toml` and `packs/repo-governance/.claude-plugin/plugin.json` both carry version `2.2.0`.
- [ ] **AC-0044.** `FORCE=1 make build-self` on the finished change leaves `git status --porcelain` empty.

## Retired identifiers

- AC-0039

## Follow-ons

none

## Assumptions

- Product: health findings on this repository are reported, not fixed, because the records are frozen — whether to answer them with errata or superseding records is not decided (settled by: eugenelim, after the PR).
