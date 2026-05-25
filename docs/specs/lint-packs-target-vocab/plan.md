# Plan: lint-packs-target-vocab

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three touch zones, all in PR scope:

1. **Vocab data** — new `docs/contracts/target-vocab.toml` with
   per-target tables for the four targets `adapter.toml` declares
   today. `description-max-length` and `name-pattern` carried by
   every target; `name-max-length` carried only where the target's
   documentation pins one (Kiro: 64). Each cap is preceded by a
   comment naming its upstream source URL and the date it was
   checked (AC1 audit requirement).
2. **Lint extension** — `packages/agentbundle/agentbundle/build/lint_packs.py`
   gains:
   - A module-level `_load_target_vocab(start)` helper. Path
     resolution walks up from `start` (the resolved `--packs-dir` in
     production, an explicit tmp tree in tests) to find
     `docs/contracts/target-vocab.toml`. Returns `(vocab, error)` so
     callers can surface AC11 failures. There is no fallback to the
     module file's ancestor — if the walk reaches filesystem root
     without finding the file, that's an AC11 failure.
   - A module-level `_strictest_constraints(vocab)` helper returning
     a `Constraints` namedtuple with `description_max` (int),
     `name_pattern` (compiled regex; loader has already verified all
     targets agree byte-equal, AC1), `name_max` (int), plus a
     `binding_targets: dict[str, list[str]]` keyed by constraint
     field name. The three entries are:
       - `"description_max"` → ASCII-sorted list of targets sharing
         the strictest description cap.
       - `"name_max"` → same for name length.
       - `"name_pattern"` → every declared target, ASCII-sorted
         (the byte-equal-agreement contract means every target
         binds the pattern). This entry exists so name-pattern
         findings can render `binding target: <all>` per spec
         AC2/AC5.
     Findings render binding targets as
     `", ".join(constraints.binding_targets[field])` to a single
     `binding target: a, b` token in the message.
   - `lint_pack(pack_dir, constraints=None)` extended to walk
     `.apm/skills/*/SKILL.md` and `.apm/agents/*.md` after the
     existing portability sweep. Each walk produces findings in the
     existing trailing-relpath shape, appended to the same list.
     The combined list is sorted by trailing relpath (split on the
     last `": "`) before return — preserves AC10.
   - `lint_all_packs(packs_dir, constraints=None)` extended to
     accept and thread `constraints` through to each
     `lint_pack(entry, constraints=constraints)` call. Without this
     thread, the vocab `cmd_lint_packs` loads never reaches the
     per-pack walks and AC2–AC6 silently never fire in production.
   - `cmd_lint_packs` loads vocab once at startup via
     `_load_target_vocab(packs_dir)`, then calls
     `lint_all_packs(packs_dir, constraints=loaded)`. Missing /
     malformed vocab is an immediate stderr error + exit 1, no
     per-pack walks (AC11).
   - A separate metadata walk (rather than threading into the
     existing `rglob("*")`) is the right structure: the portability
     sweep checks every entry's name and symlink status; the metadata
     checks need structured access (frontmatter parsing) for specific
     file kinds. Layering would mean type-dispatching mid-walk and
     mixing two concerns in one loop. Two walks read cleaner; the
     performance cost over `packs/` is negligible.
3. **Tests + fixtures** — extend
   `packages/agentbundle/agentbundle/build/tests/test_lint_packs.py`
   with new test methods. Build pack fixtures at runtime under
   `tempfile.TemporaryDirectory()` to match the existing test style;
   no new on-disk fixtures.

Order of operations: write the vocab file (data), write the failing
tests (red), extend `lint_packs.py` (green), run the gate against
real `packs/`, fix any real violations in a separate commit, run
full gates.

## Tasks

Task statuses: `pending`, `in_progress`, `done`. Each task lists
`Tests:` before `Approach:` per work-loop's TDD discipline.

### T1 — Add `docs/contracts/target-vocab.toml`

- **Status:** pending
- **Verification mode:** Goal-based.
- **Depends on:** none.
- **Done when:**
  - File exists at `docs/contracts/target-vocab.toml`.
  - `python -c "import tomllib; tomllib.loads(open('docs/contracts/target-vocab.toml').read())"` exits 0.
  - File declares `[target."claude-code"]`, `[target.kiro]`,
    `[target.copilot]`, `[target.codex]`. Each has
    `description-max-length` (int) and `name-pattern` (string).
    Kiro additionally has `name-max-length = 64`.
  - Each of `description-max-length`, `name-pattern`,
    `name-max-length` is preceded by a TOML comment carrying its
    upstream source URL and the date checked (AC1).
- **Tests:** Goal-based; no production test file.
- **Approach:** Write the file with a header comment explaining
  the split from `adapter.toml` and noting "no JSON schema; no
  follow-up planned". Source URLs cite agentskills.io (the
  cross-target description norm) and the per-target docs pages
  where they exist.

### T2 — Extend `lint_packs.py` test file (RED)

- **Status:** pending
- **Verification mode:** TDD (red phase).
- **Depends on:** T1 — the vocab file must exist on disk so the
  non-AC11 tests in this batch don't trip the missing-vocab failure
  path when they go green in T3.
- **Done when:** Tests are written; running them surfaces an
  assertion-shaped failure in every new test method (no
  `ImportError` at module load — that means the test file is
  malformed). A pre-emptive scaffold in `lint_packs.py` lands
  alongside the tests:
    - `Constraints` namedtuple type (`description_max`,
      `name_pattern`, `name_max`, `binding_targets`).
    - `constraints=None` kwarg on `lint_pack` AND
      `lint_all_packs`. When the kwarg is supplied, both functions
      execute the existing portability walk only — they ignore the
      constraints object and produce no vocab findings.
  Outcome: every new test fails on a real assertion (`"expected 1
  finding, got 0"` for vocab-violation tests; sort-order assertion
  for the cross-subtree test) rather than on `NotImplementedError`
  or `TypeError`. The cross-subtree-ordering test in particular
  must reach the findings-list code path so its assertion is
  meaningful in RED; the scaffold lets that happen by accepting
  the kwarg without changing behavior. T3 replaces the ignore-kwarg
  body with the real logic; the namedtuple shape stays byte-equal
  between T2 and T3.
- **Tests (themselves the deliverable):**
  - `test_skill_dir_name_pattern_violation_detected` — dir
    `Bad_Name`; asserts a finding containing `skill/Bad_Name`,
    `name does not match`, and `binding target:`.
  - `test_skill_frontmatter_name_mismatch_pattern_detected` — dir
    `valid-name` but SKILL.md has `name: Bad_Name`; asserts a
    finding referring to the frontmatter name.
  - `test_skill_name_length_violation_detected` — 70-char kebab
    dir name; asserts a finding `name length exceeds 64 (got 70`.
  - `test_skill_description_length_violation_detected` —
    description 1100 chars; asserts a finding `description length
    exceeds 1024 (got 1100`.
  - `test_skill_description_singleline_required` — SKILL.md with
    `description: >\n  multi line value`; asserts a finding
    `description must be a single-line value`.
  - `test_agent_name_length_violation_detected` —
    `.apm/agents/<70-char-name>.md`; asserts `agent/<name>: name
    length exceeds 64`.
  - `test_agent_description_length_violation_detected` — agent .md
    description 1100 chars; asserts `agent/...` and `description
    length exceeds 1024 (got 1100`.
  - `test_agent_description_singleline_required` — multi-line
    description; asserts `description must be a single-line value`.
  - `test_clean_pack_with_skills_and_agents_has_no_vocab_findings`
    — kebab skill (50 chars), agent (50 chars), descriptions 100
    chars; asserts `[]`.
  - `test_findings_remain_sorted_when_vocab_and_portability_mix` —
    pack with `seeds/NUL.md` (portability) and `.apm/skills/Bad_Name/SKILL.md`
    (vocab); asserts the findings list is sorted by trailing
    relpath (the last `": "`-delimited segment).
  - `test_portability_findings_sort_across_subtrees_when_constraints_supplied`
    — pack with portability violations in **both** `seeds/` and
    `.apm/` (e.g. `seeds/NUL.md` and `.apm/agents/CON.md`); calls
    `lint_pack(pack, constraints=<loaded>)` and asserts findings
    interleave in trailing-relpath order. Protects against the
    silent cross-subtree reorder T3 introduces under
    `constraints is not None`.
  - `test_multi_target_tie_renders_comma_joined_binding` —
    pack with a description that exceeds the shared cap (e.g.
    1100 chars, when codex and kiro both declare 1024); asserts
    the finding contains `binding target: codex, kiro` (ASCII
    sort, comma-space separator).
  - `test_missing_vocab_file_fails_loud` — invoke `cmd_lint_packs`
    with a packs-dir tree whose ancestor lacks
    `docs/contracts/target-vocab.toml`; asserts exit 1 and stderr
    mentions `target-vocab.toml`.
  - `test_inconsistent_name_pattern_fails_loud` — invoke
    `cmd_lint_packs` with a tmp tree containing a `target-vocab.toml`
    where two targets carry different `name-pattern` strings;
    asserts exit 1 and stderr mentions the inconsistency.
- **Approach:** Each test builds the pack at runtime via
  `tempfile.TemporaryDirectory()`. `pack.toml` carries the same
  minimal `[pack]` block the existing tests use. For
  `test_missing_vocab_file_fails_loud`, the test uses a tmp dir as
  the packs-dir whose lookup walks find no `target-vocab.toml` — the
  loader's resolution must be testable without monkey-patching.

### T3 — Implement vocab-driven checks in `lint_packs.py` (GREEN)

- **Status:** pending
- **Verification mode:** TDD (green phase).
- **Depends on:** T1, T2.
- **Done when:**
  - All tests from T2 pass.
  - The T2 test methods are present **without modification** in
    the GREEN diff. `git diff <T2-commit>..<T3-commit> --
    packages/agentbundle/agentbundle/build/tests/test_lint_packs.py`
    shows additions only — no deletions or edits inside the methods
    landed in T2.
  - All pre-existing tests in `test_lint_packs.py` still pass.
  - `lint_all_packs(packs_dir, constraints=...)` threads
    constraints to each `lint_pack(entry, constraints=...)` call
    (closes the gap that would otherwise leave AC2–AC6 silently
    inert in production).
  - `python -m agentbundle.build.lint_packs --packs-dir
    packages/agentbundle/tests/fixtures/lint_packs/` exits 0
    against the existing clean fixture (when the in-tree
    `docs/contracts/target-vocab.toml` is reachable from that
    packs-dir's ancestor chain).
- **Tests:** Those defined in T2.
- **Approach:**
  - Add `_load_target_vocab(start)` and `_strictest_constraints(vocab)`
    module-level helpers. The loader returns `(vocab_or_None,
    error_message_or_None)`. `_strictest_constraints` returns a
    `Constraints` namedtuple (or dict) with `description_max`,
    `name_pattern` (compiled), `name_max`, plus a `binding_targets:
    dict[str, list[str]]` keyed by the constraint field.
  - Add `_check_skill_metadata(pack_dir, constraints)` and
    `_check_agent_metadata(pack_dir, constraints)`.
  - Extend `lint_pack()` to take an optional `constraints` argument;
    when present, call both metadata checks after the portability
    sweep, append findings, and sort the combined list by trailing
    relpath. When absent, behave exactly as today (so callers that
    don't load vocab still work — used by tests that pre-date this
    PR).
  - `cmd_lint_packs` loads vocab via `_load_target_vocab(packs_dir)`.
    On error, write the error to stderr and return 1 without
    walking packs (AC11).
  - Frontmatter parsing: an inline `_extract_frontmatter_fields(text,
    keys)` returns a dict of `{key: value}` for requested keys.
    Recognises only single-line scalar values (`key: value` with
    balanced surrounding quotes stripped). When a requested key's
    value position is `>`, `|`, or empty (signaling a folded /
    nested block), the function returns a sentinel `MULTILINE` for
    that key. Metadata checks then translate the sentinel into the
    AC12 finding. This keeps the parser predictable; multi-line
    description shapes are refused, not mis-parsed.

### T4 — Run the gate against real `packs/`, fix violations

- **Status:** pending
- **Verification mode:** Goal-based.
- **Depends on:** T3.
- **Done when:**
  - `python -m agentbundle.build.lint_packs --packs-dir packs/`
    exits 0.
  - Any prose changes (over-cap descriptions trimmed; folded
    descriptions un-folded) land in a separate commit from the
    gate-introduction commit (process recommendation per Rollout).
- **Tests:** Goal-based.
- **Approach:** Run the command, read findings, trim or re-format
  offending source files in `packs/<pack>/.apm/{skills,agents}/...`
  to fit. Verify `make build-self` still passes.

### T5 — Full gates + reviewer pass

- **Status:** pending
- **Verification mode:** Goal-based + adversarial review.
- **Depends on:** T4.
- **Done when:**
  - Project's lint/typecheck/test commands exit 0.
  - `adversarial-reviewer` returns `Clean — ready to commit.` on
    the diff.
  - `quality-engineer` returns `Clean — ready to commit.`
- **Tests:** Goal-based.
- **Approach:** Standard work-loop REVIEW phase. Re-fire on
  findings, fingerprint via `loop-cohort.py review record`.

## Risks

- **`packs/core/.apm/agents/quality-engineer.md` description is ~830
  chars.** Comfortable margin under 1024. If T4 surfaces a violation
  there, trimming is a one-line edit. If it lands in a long-form skill
  description, more thought goes into what to cut.
- **The frontmatter parser refuses multi-line descriptions outright
  (AC12).** That's a contract, not a limitation: silent under-counting
  would defeat the gate's purpose. If a pack author has a genuine need
  for a long, structured description, they fold it themselves into a
  single line — which is also how the description survives projection
  to Codex / Kiro JSON.
- **The vocab loader's path resolution.** `_load_target_vocab(start)`
  walks up from `start` looking for `docs/contracts/target-vocab.toml`.
  When `cmd_lint_packs` is invoked with a `--packs-dir` outside the
  repo (e.g. a `dist-test/` tree under tmp), the walk must terminate
  at filesystem root with the missing-file error path (AC11). The
  implementation must not silently fall back to the module file's
  ancestor when the explicit start has no match.

## Changelog

- 2026-05-25 — Initial draft. Two-commit rollout (gate + fixes).
- 2026-05-25 — Revision after pre-EXECUTE review (1). Added AC11
  (missing-vocab fails loud), AC12 (multi-line descriptions
  refused), frontmatter-name pattern check on AC2/AC5, binding-
  target naming in every finding, trailing-relpath finding shape
  (fixes the sort-key collision the reviewer flagged), RFC-0001
  citation, T3 byte-equal-tests gate, audit-comment requirement on
  vocab caps.
- 2026-05-25 — Revision after pre-EXECUTE review (2). Defined the
  `name-pattern` collapse rule (all targets must agree byte-equal;
  loader refuses otherwise — folded into AC1 + AC11). Pinned the
  multi-target tie rendering as `", ".join(sorted(targets))` in
  Boundaries and exercised it with a new T2 test. Added a T2 test
  for cross-subtree portability ordering under
  `constraints is not None`. Fixed T2's dependency-on-T1 rationale.
  Replaced the line-range citation in Boundaries with a
  symbol-anchored reference.
- 2026-05-25 — Revision after pre-EXECUTE review (3). Added
  `lint_all_packs(constraints=...)` threading to T3 done-when
  (without it, vocab loads but never reaches the per-pack walks
  and the new checks silently never fire). Replaced T2's
  error-type pinning with a pre-emptive scaffold strategy (land
  the `Constraints` namedtuple + `lint_pack` kwarg in T2 with
  `NotImplementedError` body, fill in T3). Enumerated all three
  constraint keys in T1's audit-comment requirement to match AC1.
  Split AC1's file-shape requirement from AC11's loader-behavior
  requirement.
- 2026-05-25 — Revision after pre-EXECUTE review (4). Defined the
  `binding_targets["name_pattern"]` rendering (every declared
  target, ASCII-sorted) so AC2/AC5's `binding target:` token has a
  defined value for name-pattern findings. Changed T2 scaffold
  semantics: `lint_pack(constraints=<not None>)` now executes the
  portability-only walk and ignores constraints (instead of
  raising `NotImplementedError`) so the cross-subtree-ordering
  test reaches the findings-list code path and fails on a real
  assertion in RED. Dropped the disclaimed `Always do` Boundary
  bullet for the two-commit rollout (was already in Rollout —
  removing the duplicate keeps Boundaries as load-bearing rails
  only).
- 2026-05-25 — Mid-EXECUTE amendment. The strict "walk up from
  `--packs-dir`, no fallback" rule in AC11 collided with the
  pre-existing `LintPackTests` (their tmp `packs-dir` is under
  `/var/folders/...` with no vocab anywhere on the ancestor chain).
  AC8 wins — those tests must pass unchanged — so AC11 now allows
  the loader to fall back to walking up from `lint_packs.py`'s
  ancestor chain when the explicit packs-dir walk fails. The
  `test_missing_vocab_file_fails_loud` test exercises the
  both-walks-fail path by patching `_VOCAB_RELPATH`. Side-effect
  worth flagging: pre-existing `cmd_lint_packs` tests
  (`test_cmd_lint_packs_exits_one_on_violation`,
  `test_cmd_lint_packs_exits_zero_on_clean_packs_dir`) now load the
  in-tree vocab transitively and run the new metadata gate over
  their tmp fixtures; they still pass because the fixtures contain
  no vocab violations.
- 2026-05-25 — Post-review revision. Reviewer found:
  (a) third-party catalogue attribution in `target-vocab.toml`
  (memory hook violation) → removed.
  (b) finding-shape drift across spec / changelog / code → spec
  AC2 now formally includes `(got '<candidate>'; binding target:
  ...)` in the pattern finding; both dir-name and fm-name produce
  the same shape, distinguishable by whether `candidate` equals
  the slot.
  (c) `, value '<candidate>'` segment in length finding diverged
  from spec → removed; the length finding now reads exactly
  `name length exceeds N (got M; binding target: ...)` per AC3.
  (d) multi-line `name:` in frontmatter was silently dropped →
  AC12 extended to cover `name:` as well as `description:`; impl
  now refuses both with `{field} must be a single-line value`.
  (e) AC11 success-path (module-ancestor fallback finds the
  in-tree vocab) was untested → new
  `test_loader_module_ancestor_fallback_succeeds`.
  (f) Frontmatter-name length check (not in spec) dropped from
  impl; length check now applies only to the on-disk dir / file
  stem.
  Plus minor cleanups: doubled `read_text` removed from the skill
  path, error message wording tightened.
