# Spec: bandit-nosec-form-lint

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (governance surface — it adds a gate to the `build-check`
  chain and edits `bandit.yaml`, which `Makefile`'s `SAST_CONFIG` names as the
  config governing the SAST gate. Same reading as the sibling
  `bandit-nosec-comment-hygiene` spec, which called the same two surfaces
  full-mode.)
- **Constrained by:**
[ADR-0084](../../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)
- **Contract:** none (a repo gate; no published interface)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md` with per-task `Tests:`. The two human approval gates it
sequences were **granted up front by the requester** as a standing instruction
to carry this through to merge.
Everything else full mode requires was run:
`adversarial-reviewer` (iterated), and `security-reviewer` (warranted — the
change adds a gate over a security control's audit trail and the linter itself
shells out). Both produced findings that are applied here.

**Why no `plan.md` is a judgement, not an omission.** A plan's per-task
`Tests:` and `Depends on:` exist to sequence multiple interdependent tasks;
this is a single task whose verification mode is named in § Testing Strategy
and whose gate is the self-test. There is no task ordering for a plan to carry.

**Status ownership.** Every AC below is met and both gates are granted, so the
spec is `Shipped`. It was held at `Implementing` until the grant rather than
flipped by the author.

## Objective

`tools/run-bandit-gate.py` fails `make sast` on any Bandit stderr, which catches
every malformed suppression Bandit *warns* about. One shape produces no warning
at all:

```python
x = eval(s)  # nosec           <- resolves to no test id
x = eval(s)  # nosec  # reason <- same, and the second `#` makes it look correct
```

Bandit's `core/tester.py` treats an empty resolved-id set as "nosec without test
number" and skips **every** test on that statement. Nothing reaches stderr, so
the gate stays green over it. Fail-open and silent — ADR-0084 recorded this as
the residue its stderr rule cannot reach and named a form lint as the closer.

Success: that shape fails `make build-check`, with a message that says which of
the two consequences applies and how to fix it.

## Why `build-check` and not `make sast`

Two reasons, both load-bearing:

1. **It needs no scanner.** Pure stdlib, offline, sub-second. Nothing about it
   belongs behind the ~76k-LOC scanner pass.
2. **`make sast` would not catch it anyway.** This is the reason that actually
   carries the decision. The blanket shape produces *no bandit output at all* —
   that is its whole nature — so running it behind the scanners would add
   nothing whether they are skipped or not.

   An earlier draft argued instead that `SKIP_SAST` leaves a window. That
   argument does not hold and is recorded here so it is not re-derived:
   `skip_sast` is true only when the diff touches nothing in
   `SAST_DIRS ∪ SAST_CONFIG`, and this linter's scope *is* `SAST_DIRS` — so any
   diff that can introduce an in-scope violation is by construction
   SAST-relevant. The `SKIP_SAST` point survives only for *pre-existing*
   violations, which a skipped run would leave unexamined.

## How it detects — parity with Bandit, not a grep

The linter reproduces Bandit's own detection rather than searching for the word
`nosec`. `core/manager.py` tokenises each file and hands every `COMMENT` token
to `_parse_nosec_comment`, which runs

```python
NOSEC_COMMENT = re.compile(r"#\s*nosec:?\s*(?P<tests>[^#]+)?#?")
```

as a `search`. Both halves are copied deliberately:

- **`tokenize`, not lines.** A `# nosec` inside a string literal or docstring is
  not a directive, and must not be reported. Line-based grepping cannot tell.
- **`search` with no word boundary.** `# noseclike` **is** a directive to
  Bandit: the pattern matches its prefix and captures `like` as the id list,
  which resolves to nothing — a blanket suppression nobody wrote. A linter that
  "helpfully" required a word boundary would be quieter than Bandit and miss it.

The consequence cuts both ways, and this change hit it: prose *quoting* the
required form inside a Python comment is itself a directive. The comment
introduced in `tools/repo/build_gate_chain.py` to explain this gate spelled the
form out, and Bandit's parser read it as an id-less suppression of that very
line. Confirmed by construction — `_parse_nosec_comment` on that text returns
`set()`. The linter caught it on its first real run. The comment now names
`bandit.yaml` instead of quoting the form.

## The two gates caught each other

Worth recording, because it is the argument for having both. This change was
caught twice by the machinery it extends:

1. **The new linter caught its own explanatory comment.** The note added to
   `build_gate_chain.py` spelled out the directive form, and bandit's parser
   read it as an id-less suppression of that line. Confirmed by construction:
   `_parse_nosec_comment` on that text returns `set()`.
2. **The existing stderr gate caught the new self-test.** An early draft drove
   `git` through the real repo's index and carried `# nosec B603` on those
   calls. The calls also trip B607 (partial executable path), and at the gate's
   medium severity floor neither finding survives, so both suppressions were
   unused — `run-bandit-gate.py` failed the build on
   `nosec encountered … but no failed test`. The fix was not to add ids: it was
   to stop mutating the real repo at all. The self-test now runs the linter
   inside a throwaway git repo carrying its own `Makefile` and copy of the
   script, so `REPO_ROOT` resolves there. That removed the subprocess calls,
   removed the suppressions, and made the case exercise Makefile parsing too.

A test that writes to the real index would also have left it dirty had it
crashed between setup and teardown. The gate found a correctness problem by
complaining about a comment.

## Deliberate narrowing, and one optional import

Bandit accepts a test *name* (`assert_used`) as well as an id (`B101`).
ADR-0084 and `bandit.yaml` require the numeric ID, so only `B<digits>` is
accepted here.

`classify` resolves stray tokens **before** consulting any registry, and that
ordering is why the `not-an-id` message stays hedged: at that point the linter
genuinely cannot tell whether `assert_used` names a real test, so it states the
form violation as fact and both consequences — silent widening, or
full-statement suppression — conditionally. A test pins that phrasing.

**Deviation from AGENTS.md's pure-stdlib rule, named rather than buried.**
`id_checker()` imports `bandit.core.extension_loader` when it is available, to
catch a well-formed id that does not exist (`# nosec B999`). The base path is
still pure stdlib — the import is optional, guarded, and its failure degrades
the scan rather than breaking it (any exception, not just `ImportError`:
importing builds the plugin registry from entry points). `check_id` and not
`plugins_by_id`: the B3xx range is bandit's *blacklist* registry, so a
plugins-only lookup reports every `# nosec B310` in this repo as unknown.

## Scope

Git-tracked `*.py` under the Makefile's `SAST_DIRS`, **read from the Makefile at
runtime rather than copied**. `Makefile:185` exists so consumers read that
variable "instead of hard-coding the lists, so the workflow predicate can't
drift from them and silently skip the scan on a newly-added scannable dir"; a
second copy in this script would be that exact drift. Parsed rather than shelled
out to `make`, because this chain is deliberately make-free for Windows.

**Wider than bandit's own scan, deliberately.** `bandit.yaml` excludes
`*/tests/*`; this gate does not. A malformed suppression in a test tree is
still a malformed suppression, and `exclude_dirs` is configuration that can
change — a directive that is inert today becomes live the moment a tree stops
being excluded. The cost is a possible red build over a directive bandit never
evaluates; the repo's one such site
(`packs/converters/tests/skills/file-to-markdown/test_tier3.py:40`) is
well-formed, so nothing is red today. If that trade ever bites, honour
`exclude_dirs` here rather than deleting the suppression.

Tracked-only because `packages/agentbundle/build/lib/` holds gitignored copies
of tracked modules. Bandit *does* read them when they exist (`bandit -r
packages` walks the filesystem, and `bandit.yaml` excludes only `*/tests/*`), so
the reason is not "no scanner reads it" — it is that a report there duplicates
one already raised against the real file.

## Acceptance Criteria

- [x] **AC1 — the id-less shapes fail.** A bare `# nosec` and an id-less
      `# nosec  # reason` are each reported, with the message stating plainly
      that they suppress every test on the statement and that Bandit reports
      nothing.

- [x] **AC2 — the reversed form still fails here.** `# nosec B307 — reason`,
      `# nosec B307 - reason`, and bare prose after the id are reported. Bandit
      warns about these and the stderr gate already catches them; this catches
      them without a scan, on diffs where `SKIP_SAST` is set.

- [x] **AC3 — Bandit parity, both directions.** `# noseclike` is reported
      (Bandit treats it as an id-less directive). A `# nosec` inside a string
      literal or docstring, and prose merely containing the word `nosec`
      mid-sentence, are **not** reported — the last is real text from
      `packs/converters/.apm/skills/file-to-markdown/scripts/tier3.py:43`, which
      a word-grep linter would fire on.

- [x] **AC4 — no overclaiming on the name form.** `# nosec assert_used` is
      reported, and its message does not assert that the statement is fully
      suppressed. A test pins that phrasing, so a future "simplification" of the
      message into a flat claim fails.

- [x] **AC4b — two more shapes that read as correct are rejected.** Both were
      found by review, and both resolve to a blanket suppression in bandit:
      - `# nosec B404,B603` — a comma with no following space. Bandit's
        `NOSEC_COMMENT_TESTS` keeps only the last capture of a comma run, so it
        suppresses `B603` alone. Measured on 1.9.4; `# nosec B404, B603`
        resolves to both and stays silent.
      - `# nosec B999` — an ID that does not exist. It has an ID's shape, so it
        reads as correct, but resolves to nothing. A one-character typo is the
        likeliest real instance of this gate's whole failure class. Requires
        bandit's registry (`extension_loader.MANAGER.check_id`, which covers the
        blacklist B3xx range that `plugins_by_id` alone misses), so it is
        skipped with a printed notice where bandit is absent. **Its CI reach is
        currently nil, stated plainly:** `build-check.yml` installs
        `requirements-sast.txt` only when `skip_sast != 'true'`, so on a
        SKIP_SAST PR bandit is absent and this check no-ops; where bandit *is*
        installed, `make sast` also runs and `run-bandit-gate.py` already fails
        on bandit's own `Test in comment: B999 …` stderr. So it earns its place
        locally and as defence-in-depth, not as new CI coverage. Making the
        bandit install unconditional would change that, and is recorded as
        `build-check-installs-bandit-unconditionally`.

- [x] **AC5b — the gate cannot be neutered silently.** Two mutations were run
      against the real tree and both now fail the self-test: (a) `main` unable
      to return 1, and (b) the scan scope collapsed to a root matching nothing.
      Before review both passed with every case green, which is what made the
      original AC7 claim false. A scan matching no files now exits 2 — a silent
      no-op is not a pass.

- [x] **AC5 — silent on the tree it lands in.** `python3
      tools/lint-nosec-form.py` exits 0 across every git-tracked file in
      `SAST_DIRS`, and says how many it read.

- [x] **AC6 — wired into `make build-check`.** `tools/lint-nosec-form.py` and
      its self-test are steps in `tools/repo/build_gate_chain.py`'s `build-check`
      chain, self-test first, matching the surrounding `_script_step` pairs. It
      is reachable with `SKIP_SAST=1`.

- [x] **AC7 — the gate has a self-test that fails if the gate is removed.**
      `tools/test-lint-nosec-form.py`, in the shape
      `tools/test-sast-stderr-gate.py` and `tools/test-audit-requirements.py`
      set. Its firing cases assert the *kind* of violation reported, not merely
      a non-zero exit, so a linter simplified into something that never fires
      still fails it.

- [x] **AC8 — ADR-0084's `Revisit if` is mechanical.** A case asserts the
      linter's `NOSEC_COMMENT` is byte-identical to Bandit's, so a Bandit
      upgrade that changes the pattern turns the build red instead of silently
      un-syncing the two. Skipped with a printed notice when Bandit is absent.

- [x] **AC9 — `bandit.yaml` names its enforcer.** Its header comment already
      states the form and that the ID is mandatory; it gains a pointer to the
      linter, so the file that carries the instruction also says what checks it.

- [x] **AC10 — the register is dispositioned.** `bandit-nosec-form-lint` is
      removed from `workspace.toml [backlog].open`, and the
      `compare-bandit-suppressions` decision below is recorded there.

- [x] **AC11 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, `make sast` (unskipped, so the new gate
      and the scanners are both proven on this diff), and `python3 -m pytest
      tools/test_build_gate_chain.py` — named explicitly because the chain's
      ordered `EXPECTED_SCRIPT_STEPS` manifest is not run by `make build-check`,
      only by `make test` and `build-check.yml`. Omitting it is how this PR
      first shipped two red CI jobs while `make build-check` reported green.

## Boundaries

### Always do

- Always derive the scanned file set from the Makefile's `SAST_DIRS`. A widened
  `SAST_DIRS` must widen this gate in the same commit, with no edit here.
- Always keep the self-test's firing cases asserting the *kind* of violation and
  the process exit code, not merely "something was reported".

### Ask first

- Ask before widening the accepted id grammar beyond `B<digits>` — accepting
  bandit's test-*name* form would re-open the narrowing § Deliberate narrowing
  argues for.
- Ask before adding any exemption mechanism (a pragma, an allowlist). The gate's
  value is that it has none, exactly as bandit has none.

### Never do

- Never add an escape hatch for prose that quotes the form. Bandit has none —
  an exemption here would make the linter quieter than the tool it models, which
  is the one failure mode it cannot afford.
- Never widen it to a word-boundary or line-based match to reduce noise. Parity
  with `NOSEC_COMMENT` is the whole design.
- Never change any existing suppression. This change adds a gate; it moves no
  suppression's coverage. The tree is already clean under it.

## Testing Strategy

Goal-based, and verified against real fixtures both ways:

- **Silent half, real tree:** `python3 tools/lint-nosec-form.py` → exit 0 over
  all git-tracked `*.py` in `SAST_DIRS`.
- **Firing half:** `python3 tools/test-lint-nosec-form.py` → every case passes,
  covering the bad shapes and the silent ones, plus the process-level exit contract.
- **End-to-end through the chain:** the linter and its self-test appear in
  `SKIP_SAST=1 make build-check` output and block it on failure. Demonstrated
  live, not reasoned about: the `build_gate_chain.py` comment described above
  made the chain red until it was fixed.
- **Independent confirmation of the hazard:** Bandit's own
  `_parse_nosec_comment`, run against that comment's text, returns `set()`.

## Assumptions

- Bandit's `NOSEC_COMMENT` and the tokenize-driven `COMMENT` walk are stable
  across the 1.9.x line pinned in `tools/requirements-sast.txt`. AC8 converts
  this from an assumption into a gate.

## Declined

- **A `compare-bandit-suppressions` tool in this PR.** It earns being a
  tool: the four traps in `bandit-nosec-comment-hygiene`'s § Testing Strategy
  are durable knowledge, and their current carrier is prose inside a **Frozen**
  spec — so when the procedure improves, the record cannot. That is a real
  defect, not a style preference. But it is a different concern from this gate
  (a manual before/after harness, not a build-check step), it would roughly
  double this diff, and this PR changes no suppression, so it would ship
  unexercised. Recorded as `compare-bandit-suppressions-tool`.
- **Scanning untracked files.** `git ls-files` is the file set on purpose; see
  § Scope.
- **Accepting Bandit's test-name form.** See § Deliberate narrowing.
- **Adding the self-test to `tools/test-all.py`'s `TESTS`.** That umbrella is a
  curated hand-run list; this gate runs in `build-check`, so an entry there
  would be a second, weaker copy of an enforcement that already blocks.
