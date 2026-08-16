# Spec: packages-governance-marker-sweep

**Status:** Shipped
**Mode:** light (no risk trigger fired)

## Objective

Strip this repo's internal governance provenance markers — `RFC-0NNN`, `ADR-0NNN`,
spec-relative acceptance-criterion citations (`AC7`, `AC22b`, `AC15(c)`), and repo-specific
`docs/specs/<slug>` paths — from **comments, docstrings, and user-visible message strings under
`packages/`**, on the same principle already applied to `packs/` by
`pack-governance-marker-removal`. This closes that spec's deferred AC12.

`packages/agentbundle` ships as an sdist that carries source, and the repo is public. An
adopter reading `install.py` has no `docs/rfc/`, no `docs/adr/`, and no spec of ours, so every
marker is a dangling reference that reads as a broken pointer. The *knowledge* each comment
carries stays; only the citation goes. `# RFC-0052 D8: v0.3 state is hard-refused` becomes
`# v0.3 state is hard-refused`; `the AC8 cost cap` becomes `the cost cap`.

**Discriminator.** Ours are zero-padded four-digit ordinals, matched by
`\b(RFC|ADR)-0[0-9]{3}\b`. IETF numbers never start with `0` — `RFC 9106` (Argon2, in
`credbroker/_vault.py`) and every other IETF citation must survive byte-identical. That one
property is why part of the sweep is safe to automate.

**Scale.** Roughly 2.7k marker occurrences across ~2.3k comment/docstring lines in ~290 Python
files, split about 70/30 between `tests/` and engine source, plus ~150 in non-Python shipped
files (mostly `agentbundle/_data/adapter.toml`, whose comments are read from inside the wheel).
Nearly every line is a distinct sentence, so this is tiered-automation-then-per-site work, not a
regex pass. The brief's advance estimate (~1k) counted the `RFC`/`ADR` ordinals; the AC-citation
class is the larger half.

## Acceptance Criteria

- [x] AC1 — `grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bACs?\s*-?#?\s*[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' packages/ --exclude='AGENTS*.md' --exclude='CHANGELOG.md'` resolves entirely to the retained set enumerated in AC5 — no comment, no docstring, no message string.
- [x] AC1a — **The AC pattern matches the spaced and hashed forms too.** `\bAC-?[0-9]+[a-z]?\b` cannot match `AC #7`, `AC 4`, or `ACs 1-15`; 31 sites survived the first pass because of it. It is the second under-match of this kind — the precedent sweep's `\bAC-?[0-9]+\b` missed `AC6a` for the same reason, a `\b` that cannot follow a digit with a letter after it. The pattern is now `\bACs?\s*-?#?\s*[0-9]+[a-z]?(\([a-z]\))?\b` everywhere it appears: this spec's Verification block and `packages/AGENTS.local.md`.
- [x] AC2 — Every edited comment and docstring still states its rule. No dangling fragment, no orphaned `(`, no subject-less clause, no rule silently dropped, and no substitute pointer to a document the reader does not have ("the decision record carries the rationale" is a failure, not a fix).
- [x] AC3 — No mechanical artifact from the automated pass survives: doubled spaces, trailing whitespace, empty `#` comments, lower-cased sentence starts, or comment banners whose trailing dashes no longer align.
- [x] AC4 — Every IETF RFC reference under `packages/` survives byte-identical.
- [x] AC5 — **The retained set is exactly these classes, each retained for a stated reason:**
  - **Pinned runtime message strings, and only the assertions that pin them.** Each is asserted on verbatim, so the string and its assertion have to move in one commit — a separate change, not this one.
    - `commands/install.py` — **both** `pre-RFC-0012 dist-tree` strings (the `--force will REMOVE` warning and the `install:` refusal), plus the seven `assertIn`/`assertNotIn` in `tests/unit/test_install_inband_detection.py` that pin them. The token is the *name of a legacy on-disk layout*, not a citation, so it needs a rename decision first. Every other occurrence — comments and docstrings in `install.py` and across the test tree — **was** swept to "the legacy dist-tree layout"; the retained set is the two strings and their assertions, nothing more.
    - `config.py` — `"markers are repo-only per RFC-0004"`, pinned by `pytest.raises(ConfigError, match=...)` in `tests/unit/test_adapt_discovery_schema.py`.
    - `config.py` — the three `ConfigError` messages naming `docs/specs/adapt-to-project/spec.md`, pinned by `test_adapt_schema_migration.py`, `test_self_host_schema_migration.py`, and `test_discovery_schema_cross_consumer.py`.
    - `commands/install.py` — the `--emit-install-routes` refusal citing `RFC-0008`, and the one assertion that reads `"RFC-0008" in err or "emit-install-routes" in err.lower()`. The `or` is why these must move together: strip the marker on its own and the second branch silently carries the test. The assertion is therefore left exactly as-is here and simplified in the commit that renames the string. The surrounding docstring prose in `test_local_scope_t7_install_gates.py` **was** swept.
  - **Asserted-on substrings** in the test tree. `pytest.skip()` reasons and assert-*message* text are **not** in this class and were swept — a message argument renders only on failure, so editing it cannot affect any assertion.
  - Tests whose *subject* is one of our governance documents — `test_adapt_spec_shape.py`, `test_distribution_adapters_spec_shape.py`, `test_apm_spec_amendments.py`, `test_manual_qa_matrix_shape.py`: the spec paths and AC names are functional arguments (regex patterns, `_read()` paths, assert text naming which AC must exist), so their docstrings restate the same functional content and are retained with them. `test_credential_broker_contract_docs.py` is the exception: only its two content assertions are functional, so its docstrings **were** swept.
  - `templates/install-marker.py` and its `_data/` twin — **only** the `Specs:` docstring block, which `test_claude_plugins_install_route.py::test_writer_docstring_names_spec` asserts on. The rest of both files was swept. See Boundaries.
  - **The two `credbroker` README hyperlinks.** The precedent spec's AC11a (Shipped) recorded the decision that these "keep their working GitHub URLs and lose only the ordinal link text, so an adopter still reaches the design docs." The link *text* is ordinal-free here; the URLs stay. A sentinel decision with authority is not this sweep's to overturn.
  - **Generic placeholder paths in test data** — `docs/specs/example/notes/foo.md`, `docs/specs/feature/notes/sub/dir/bar.md`, and the `docs/specs/foo/…` pair AC10's test writes, all in `build/tests/test_self_host_check.py`, are arguments to the glob under test, not citations. The first was `docs/specs/self-hosting/...`; renaming the slug to a generic one removes an our-spec reference while exercising the identical `docs/specs/*/notes/**` pattern. That is a deliberate fixture-literal change, licensed here rather than left implicit under "no test logic".
  - `agentbundle/CHANGELOG.md` and `credbroker/CHANGELOG.md` — **decided, not deferred**: both were confirmed absent from the wheel, the sdist, and the catalogue init scaffold. They ship to nobody, and they are historical records; stripping them would rewrite history to remove a pointer no adopter can see. Permanently out of scope.
  - `AGENTS*.md` — insider context, not exported.
- [x] AC5a — **Every user-visible message string outside that retained set is swept**: all argparse `help=` text in `cli.py`, `commands/pack_evals.py`, and `build/__init__.py`; the three `catalogue_tooling/lint.py` diagnostics; `commands/init_state.py`'s greenfield-migration message; `commands/install.py`'s once-per-`(root, pack_name)` short-circuit string; `config.py`'s no-legacy-migration note; `build/adapters/codex.py`'s migration-path note; and `safety.py`'s `_PACK_PRIMITIVE_TYPES` explanation. Each still states the thing; none leaves an empty `()` or a stranded dash.
- [x] AC6 — `python3 tools/lint-ruff.py` passes; `PYTHONUTF8=1 python3 -m pytest tests/ agentbundle/build/tests/ -q` passes from `packages/agentbundle`; `SKIP_SAST=1 make build-check` passes from the repo root.
- [x] AC6a — `python3 -m agentbundle --help`, `install --help`, `catalogue --help`, and `catalogue lint packs --help` were invoked and their output read: no empty `()`, no stranded dash, no half-sentence. Recorded under **Observed**.
- [x] AC7 — No version bumped in `version.py`, `pyproject.toml`, or any `pack.toml`. Comment/docstring-only change.
- [x] AC8 — `templates/install-marker.py` and `agentbundle/_data/install-marker.py` remain byte-identical to each other.
- [x] AC9 — `packages/credbroker/**` residue (`README.md`, `README-pypi.md`) swept; the projected pack copy under `packs/credential-brokers/.apm/user-libs/credbroker/` stays consistent after `make build-self`.
- [x] AC10 — **`_is_excluded` has a behavioural test, not just a glob test.** Reviewing the one fixture path this sweep touched surfaced that `ExcludedGlobTests` only exercises the glob→regex translation: it calls the predicate with synthetic strings and never touches disk, so it stays green if a caller drops the guard, passes an absolute path, or the pattern list empties. `ExclusionIsHonouredOnDiskTests` closes that for **one** of the three call sites — the unclassified-path enumeration's guard: it tracks a real file at `docs/specs/foo/notes/x.md` in a git working tree, runs `run_self_host`, and asserts the path is absent from that enumeration, with a control file in the same subtree so a silent stderr cannot pass. The guards at `self_host.py:353` and `:587` remain pinned only by the glob tests. **Verified by mutation:** replacing the caller's guard at `self_host.py` with `if False:` leaves all four `ExcludedGlobTests` passing and fails only the new test (`1 failed, 4 passed`). Scope note: this is a deliberate addition beyond "strip markers", made on explicit direction rather than deferred.

## Boundaries

**In scope:** comments, docstrings, and message text in every file under `packages/` — `agentbundle/**`,
`agentbundle/tests/**`, `agentbundle/build/tests/**`, `agentbundle/_data/**`,
`agentbundle/build/recipes/*.toml`, `templates/**`, test fixtures under `tests/fixtures/**`, and
the two `credbroker` READMEs.

**`agentbundle/build/tests/` ships inside the wheel** — 46 files land on disk on every
`pip install`. Its markers carry the same adopter-facing weight as engine source and get the
same review attention, not the lighter pass a test tree would otherwise earn. The top-level
`tests/` tree is sdist-only and lower priority, but still in scope.

**User-visible message strings are in scope — amended mid-change.** The brief opened with "any
marker inside a string literal is out of scope"; that was narrowed to the pinned strings AC5
enumerates, after an AST walk of every string literal in shipped code cross-referenced against
every marker appearing in a test literal. The finding that unlocked it: the `--help` tests assert
only on subcommand and flag *names*, never on help prose, and most apparent pins are markers in
the *message argument* of an assert — text shown only on failure, which editing shipped code
cannot affect. `--help` output is the highest-value surface in the corpus, so it is swept, and so
are skip reasons and assert-message text.

**Out of scope — phase 1.** Exactly the retained set AC5 enumerates, and nothing else. AC5 is the
single canonical statement of what stays; this section does not restate it. The operative rule
while editing: before touching any string literal, grep the test tree for a distinctive fragment
of it — a hit means carve-out, not rewrite.

**`templates/install-marker.py`'s `Specs:` block is the sharpest residue.** That block names two
of our spec paths, and the file is a shipped template written into the adopter's repo — the
highest-harm marker site in the corpus. It stays because
`tests/integration/test_claude_plugins_install_route.py::test_writer_docstring_names_spec` asserts
the spec path is present, so removing it means deleting a test whose stated requirement is that
the docstring name the spec — reversing a recorded decision this sweep has no mandate to
overturn. **The rest of both copies of the file was swept.** Recorded as its own backlog item
rather than done quietly.

**No lint rule, no CI gate.** Explicitly deferred by the owner. The `packages/AGENTS.local.md`
grep carries the rule.

**`contracts/adapter.toml` and `contracts/target-vocab.toml` move with the sweep even
though they sit outside `packages/`.** Both are asserted byte-identical to their
`agentbundle/_data/` twins by `tests/unit/test_contract_parity.py` and
`tools/catalogue/check_contract_parity.py`, so editing the packaged copy alone lands red.
Same coupled-file carve-out the precedent spec made for `docs/CONVENTIONS.md`.
`contracts/README.md` is *not* coupled and is left — recorded as
`contracts-readme-governance-markers` in `[backlog].open`.

**Bare feature slugs are not swept.** `pack-profiles`, `install-state-visibility`,
`copilot-full-parity` and friends double as the names of the features themselves, and the
verification grep does not match them. Unambiguous citation forms — `spec <slug>`,
`(spec <slug>)`, a slug alone in a parenthetical carrying nothing else — were rewritten as
ride-alongs; slugs used as ordinary feature names in prose stay.

Genuinely out of scope: `packs/`, `docs/`, `.github/`, `tools/`.

## Assumptions

- **Comments in `agentbundle/_data/adapter.toml` are adopter-visible.** The file is packaged
  into the wheel and read at runtime from inside it; an adopter inspecting adapter behaviour
  reads those comments.
- **No test pins a comment or docstring string this sweep edits**, beyond the enumerated
  retained set. Verified by an anchor-test sweep for `__doc__`, `inspect.getsource`, and
  `read_text()`-plus-substring assertions across both test roots before EXECUTE, and by the
  full suite after.
- **`credbroker/_sso.py` and the pack's projected copy stay in lockstep.** Already swept by the
  precedent change; re-verified after `make build-self`.

## Assumption trio

- **Touched:** comments, docstrings, and user-visible message strings in marker-bearing files
  under `packages/`, plus this spec, the `[backlog].open` entry, and the precedent spec's AC12
  checkbox. No code, no test logic, no assertions, no versions, no `packs/` sources.
- **Done when:** the AC1 grep resolves to the AC5 retained set only; every edited sentence still
  reads and still states its rule; ruff, the CI-exact pytest invocation, and `build-check` are
  green; `adversarial-reviewer` is clean.
- **Not changing:** version numbers, contract levels, the four pinned message strings,
  assertions, test logic, `CHANGELOG.md` files, IETF references, and everything outside
  `packages/`.

### Tempted and declined

- **A lint rule + CI gate to stop regression.** Declined on explicit direction. It is the
  follow-up that makes this durable, and it needs an allow-list for the IETF numbers and the
  phase-1 retained set or it fires false positives immediately.
- **A blind `sed` over the whole corpus.** Declined: ~2.3k lines resolve to ~2.2k distinct
  sentences. A token-deleting sweep leaves ungrammatical source across the engine. Tiered
  exact-string and regex rules for the formulaic classes only, then per-site rewrites.
- **Folding the four pinned strings in "while we're here."** Declined: each needs its assertion
  edited in the same commit, and `pre-RFC-0012` needs a naming decision for a legacy on-disk
  layout before it can be renamed at all. Different risk, different review, its own change.
- **Renaming `test_*_ac<n>_*` function names.** Declined: they are lower-case, invisible to the
  grep, and renaming them is churn in the test-selection surface for no adopter-facing gain.
- **Bumping the package version.** Declined — comment and docstring only, no observable
  behaviour change.
- **"Fixing" the tests that assert our docstrings name our specs.** Declined: those are recorded
  decisions with their own ACs. Named in AC5 and deferred, not overturned.

## Verification

**Mode: goal-based check, plus one behavioural test.** The sweep itself is prose; its correctness
is "the grep resolves to the retained set and each sentence still reads", which no unit test can
assert. One test *was* added — see AC10.

```bash
# Whole tree, no --include, no path narrowing. Pattern deliberately looser than
# the target on BOTH axes: `\b`-anchored cannot match `AC6a`, and `AC-?[0-9]`
# cannot match `AC #7` / `AC 4` / `ACs 1-15`. Both under-report as clean.
grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bACs?\s*-?#?\s*[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' \
  packages/ --exclude='AGENTS*.md' --exclude='CHANGELOG.md'
python3 tools/lint-ruff.py
cd packages/agentbundle && PYTHONUTF8=1 python3 -m pytest tests/ agentbundle/build/tests/ -q
SKIP_SAST=1 make build-check   # from repo root
make build-self                # projection parity for the credbroker user-lib

# Real-surface check — a green suite does not prove help text still reads.
python3 -m agentbundle --help
python3 -m agentbundle install --help
python3 -m agentbundle catalogue --help
python3 -m agentbundle catalogue lint packs --help
```

**Verification-scoping note.** The precedent sweep reported clean four times and was wrong each
time: a grep narrowed by `--include`; a `\b`-anchored AC pattern that cannot match `AC6a`;
sub-paths (`pyproject.toml`, `README*`, `_data/**`, `tests/**`) never scanned; and
`git diff origin/main...HEAD` used to inspect uncommitted work, which excludes exactly the edits
under review. All four are pre-empted above — and the working-tree diff is read with
`git diff origin/main`, two dots.

**Observed.**

- **AC1 grep** (widened pattern, whole tree, no `--include`): residue resolves entirely to the
  AC5 classes — the four governance-subject tests (84), `test_install_inband_detection.py`'s
  seven pinned assertions, `config.py` (4), `install.py` (3), the two `install-marker.py` copies'
  `Specs:` block (2 each), the two `credbroker` README hyperlinks (2 each), the placeholder
  fixture paths in `test_self_host_check.py` (4), and six single pinned sites. Nothing else.
- `python3 tools/lint-ruff.py` → `All checks passed!`
- `PYTHONUTF8=1 python3 -m pytest tests/ agentbundle/build/tests/ -q` from `packages/agentbundle`
  → 3,543 passed, 58 skipped, 0 failed (exit 0), re-run after the final fix pass.
- `SKIP_SAST=1 make build-check` → `68 passed, 0 failed`; `Ran 96 tests OK`; `pre-pr: all checks passed`.
- `python3 -m agentbundle catalogue self-host --write --force` → zero changes; projections consistent.
- `tools/catalogue/check_contract_parity.py` → 11 contract files byte-identical.
- **AC6a — `--help` surfaces invoked and read**, zero marker or artifact hits and zero argparse
  errors in each: root (57 lines), `install` (62), `upgrade` (48), `uninstall` (24), `catalogue`
  (17), `catalogue lint` (11), `init-state` (10), `reconcile` (4), `diff` (16). An earlier pass at
  this evidence was invalid — a zsh loop left `$c` unquoted, so multi-word subcommands ran as a
  single argument and returned a 2-line usage error that trivially contained no markers. The
  numbers above come from explicit per-subcommand invocations.
- **AC7** — an AST-skeleton diff against `origin/main` shows no Python code changed, and all 16
  changed `.toml` files parse to identical values. No version bumped.
- **AC2/AC3** — two adversarial review rounds (25 then 27 findings, all resolved) plus a
  purpose-built cross-line detector (`.context/marker-sweep/detect_orphans.py`) that compares each
  comment/docstring block's prose-integrity signature against `origin/main` and reports only
  regressions. It took the introduced-damage count from 34 to 1 (a doubled word), now fixed; the
  12 remaining signals are proper-noun line wraps, checked individually.
- **AC10** — new test passes; its own file is green at 73 tests; deterministic over three runs;
  mutation of the caller guard gives `1 failed, 4 passed`.
