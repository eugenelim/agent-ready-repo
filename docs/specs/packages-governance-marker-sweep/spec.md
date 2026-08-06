# Spec: packages-governance-marker-sweep

**Status:** Implementing
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

## Acceptance criteria

- [ ] AC1 — `grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bAC-?[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' packages/ --exclude='AGENTS*.md' --exclude='CHANGELOG.md'` resolves entirely to the retained set enumerated in AC5 — no comment, no docstring.
- [ ] AC2 — Every edited comment and docstring still states its rule. No dangling fragment, no orphaned `(`, no subject-less clause, no rule silently dropped, and no substitute pointer to a document the reader does not have ("the decision record carries the rationale" is a failure, not a fix).
- [ ] AC3 — No mechanical artifact from the automated pass survives: doubled spaces, trailing whitespace, empty `#` comments, lower-cased sentence starts, or comment banners whose trailing dashes no longer align.
- [ ] AC4 — Every IETF RFC reference under `packages/` survives byte-identical.
- [ ] AC5 — **The retained set is exactly these classes, each retained for a stated reason:**
  - **The four pinned message strings** (below). Each is asserted on verbatim, so it needs a rename decision plus a matching assertion edit — a separate change, not this one.
    - `commands/install.py` — **both** `pre-RFC-0012 dist-tree` strings (the `--force will REMOVE` warning and the `install:` refusal). Seven `assertIn`/`assertNotIn` in `tests/unit/test_install_inband_detection.py` pin them, and the token is the *name of a legacy on-disk layout*, not a citation.
    - `config.py` — `"markers are repo-only per RFC-0004"`, pinned by `pytest.raises(ConfigError, match=...)` in `tests/unit/test_adapt_discovery_schema.py`.
    - `commands/install.py` — the `--emit-install-routes` refusal citing `RFC-0008`. Its test asserts `"RFC-0008" in err or "emit-install-routes" in err.lower()`; stripping the marker leaves the `or` branch load-bearing and the assertion misleading, so the assertion must be simplified in the same commit.
  - `pytest.skip()` reason strings, assertion messages, and asserted-on substrings inside the test tree.
  - Tests whose *subject* is one of our governance documents (`test_adapt_spec_shape.py`, `test_distribution_adapters_spec_shape.py`, `test_apm_spec_amendments.py`, `test_manual_qa_matrix_shape.py`, `test_credential_broker_contract_docs.py`): the spec paths and AC names are functional arguments to the test, not citations. Their own comments and docstrings are still in scope.
  - `templates/install-marker.py` and its `_data/` twin — see Boundaries.
  - `agentbundle/CHANGELOG.md` and `credbroker/CHANGELOG.md` — **decided, not deferred**: both were confirmed absent from the wheel, the sdist, and the catalogue init scaffold. They ship to nobody, and they are historical records; stripping them would rewrite history to remove a pointer no adopter can see. Permanently out of scope.
  - `AGENTS*.md` — insider context, not exported.
- [ ] AC5a — **Every user-visible message string outside that retained set is swept**: all argparse `help=` text in `cli.py`, `commands/pack_evals.py`, and `build/__init__.py`; the three `catalogue_tooling/lint.py` diagnostics; `commands/init_state.py`'s greenfield-migration message; `commands/install.py`'s once-per-`(root, pack_name)` short-circuit string; `config.py`'s no-legacy-migration note; `build/adapters/codex.py`'s migration-path note; and `safety.py`'s `_PACK_PRIMITIVE_TYPES` explanation. Each still states the thing; none leaves an empty `()` or a stranded dash.
- [ ] AC6 — `python3 tools/lint-ruff.py` passes; `PYTHONUTF8=1 python3 -m pytest tests/ agentbundle/build/tests/ -q` passes from `packages/agentbundle`; `SKIP_SAST=1 make build-check` passes from the repo root.
- [ ] AC6a — `python3 -m agentbundle --help`, `install --help`, `catalogue --help`, and `catalogue lint packs --help` were invoked and their output read: no empty `()`, no stranded dash, no half-sentence. Recorded under **Observed**.
- [ ] AC7 — No version bumped in `version.py`, `pyproject.toml`, or any `pack.toml`. Comment/docstring-only change.
- [ ] AC8 — `templates/install-marker.py` and `agentbundle/_data/install-marker.py` remain byte-identical to each other.
- [ ] AC9 — `packages/credbroker/**` residue (`README.md`, `README-pypi.md`) swept; the projected pack copy under `packs/credential-brokers/.apm/user-libs/credbroker/` stays consistent after `make build-self`.

## Boundaries

**In scope:** comments and docstrings in every file under `packages/` — `agentbundle/**`,
`agentbundle/tests/**`, `agentbundle/build/tests/**`, `agentbundle/_data/**`,
`agentbundle/build/recipes/*.toml`, `templates/**`, test fixtures under `tests/fixtures/**`, and
the two `credbroker` READMEs.

**`agentbundle/build/tests/` ships inside the wheel** — 46 files land on disk on every
`pip install`. Its markers carry the same adopter-facing weight as engine source and get the
same review attention, not the lighter pass a test tree would otherwise earn. The top-level
`tests/` tree is sdist-only and lower priority, but still in scope.

**User-visible message strings are in scope — amended mid-change.** The brief opened with "any
marker inside a string literal is out of scope"; that was narrowed to the four pinned strings in
AC5 after an AST walk of every string literal in shipped code cross-referenced against every
marker appearing in a test literal. The finding that unlocked it: the `--help` tests assert only
on subcommand and flag *names*, never on help prose, and most apparent pins are markers in the
*message argument* of an assert — text shown only on failure, which editing shipped code cannot
affect. `--help` output is the highest-value surface in the corpus, so it is swept.

**Out of scope — phase 1.** The four pinned strings enumerated in AC5, and the test-side literals
(skip reasons, assert messages, asserted substrings). Those need renaming in lockstep with the
assertions that pin them, which is a separate change with a different risk profile. Before
editing any string literal, grep the test tree for a distinctive fragment of it; a hit means
carve-out, not rewrite.

**`templates/install-marker.py` is left alone, and this is the sharpest residue.** Its module
docstring carries a `Specs:` block naming two of our spec paths, and the file is a shipped
template written into the adopter's repo — the highest-harm marker site in the corpus. It stays
because `tests/integration/test_claude_plugins_install_route.py::test_writer_docstring_names_spec`
asserts the spec path is present, so the docstring is an asserted-on string literal and falls
under the phase-1 carve-out by the letter of the rule. Removing it also means deleting a test
whose stated requirement is that the docstring name the spec — reversing a recorded decision,
which this sweep has no mandate to do. Recorded as its own backlog item rather than done quietly.

**No lint rule, no CI gate.** Explicitly deferred by the owner. The `packages/AGENTS.local.md`
grep carries the rule.

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

**Mode: goal-based check.** The change is prose; its correctness is "the grep resolves to the
retained set and each sentence still reads", which no unit test can assert. No test file added.

```bash
# Whole tree, no --include, no path narrowing. Pattern deliberately looser than the
# target — a \b-anchored AC pattern cannot match AC6a and under-reports as clean.
grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bAC-?[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' \
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

**Observed:** _(filled at close)_
