# Spec: converters-pack

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0007](../../rfc/0007-user-scope-converter-pack.md) (Accepted 2026-05-24); [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (user-scope dimension); [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (install-scope precedence)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Land the catalogue's first user-scope pack — `converters` — containing three file-format conversion skills (`file-to-markdown`, `markdown-to-html`, `msg-to-markdown`) imported as a one-shot vendored snapshot from the source catalogue. The pack installs at `default-scope = "user"` with `allowed-scopes = ["user", "repo"]`, ships no `seeds/`, no hooks, and no `<adapt:NAME>` markers, and passes RFC-0004's three user-scope refusal rails by construction. From an adopter's perspective: after `agentbundle install converters`, the three converter skills are reachable from any project they open (user scope) or scoped to a single project (`--scope repo` override), the runtime install commands work from each SKILL.md, and no adopter-visible artifact names the originating catalogue. The pack is one PR — spec and implementation in the same merge.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines. *Always do* applies without asking; *Ask first* requires human sign-off before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Scrub source-catalogue attribution at import time and pin the result with an automated grep — see [AC2](#acceptance-criteria) for the grammar.
- Carry every `evals/` directory present in the source verbatim into the imported skill; never drop one that exists.
- Validate each carried `evals.json` parses as JSON and contains the agentskills.io canonical top-level keys (`skill_name`, `evals`) — see [AC4a](#acceptance-criteria).
- Keep `markdown-to-html/package.json` verbatim (ecosystem-standard npm pin manifest); document `pip` and single-package `npm` deps in SKILL.md prose where no ecosystem manifest exists.
- Pin the source commit SHA in this spec's Changelog AND in `docs/specs/converters-pack/notes/source-sha.txt` at import time (the `.txt` file is the durable cross-task artifact; the Changelog entry is the human-readable governance record).
- Re-run RFC-0004 Rail C grep against every imported primitive before merging and again in CI.

### Ask first

- Adding any file beyond what RFC-0007 § Pack shape enumerates (e.g. a CONTRIBUTING.md, a per-skill LICENSE).
- Touching `packs/<other>/` or `packages/agentbundle/` source code in this PR beyond what's needed for the integration test under `packages/agentbundle/tests/integration/` and the new pytest CI job (per [AC6b](#acceptance-criteria)).
- Promoting the scrub grep to a repo-wide `conventions-check` lint (per RFC-0007 Unresolved Q2 — defer until a leak recurs outside `packs/converters/`).
- Running the carried evals' *prompts* against the imported scripts (an agentskills.io-compatible runner is not part of this repo's tooling; out-of-scope. The cheap-tier validation in [AC4a](#acceptance-criteria) — JSON parses + canonical keys — does land).

### Never do

- No `seeds/` directory anywhere in `packs/converters/` (RFC-0004 § *seeds rail* refuses user-scope packs with non-empty `seeds/`).
- No `.apm/hooks/` or `.apm/hook-wiring/` directories (RFC-0004 § *hook rail* refuses user-scope packs with hooks until RFC-0005 ships).
- No `<adapt:NAME>` markers in any primitive file under `packs/converters/.apm/skills/` (RFC-0004 § *marker rail*; both strict-uppercase and lowercase-hyphen grammars).
- No naming of the source catalogue ("dropkit") in any **adopter-visible artifact** — meaning: `packs/converters/**` (imported files, `pack.toml`, `.claude-plugin/plugin.json`, SKILL.md bodies, scripts), commit messages, the PR description, and any file projected by the build pipeline. **Carve-out for governance text:** the spec, plan, RFC, and this spec's Changelog entries *may* name the source as part of stating or executing the scrub rule (you cannot tell a grep what to find without naming it). The `Always do` scrub grep targets `packs/converters/` only — governance docs are out of its scope by construction.
- No contract or schema amendments (`pack.schema.json`, `adapter.schema.json`, `adapter.toml` stay untouched) — this spec consumes RFC-0004 by construction.
- No new top-level directory.
- No new module boundary or abstraction layer in `packages/agentbundle/`.
- No synthesised `evals/evals.json` for `msg-to-markdown` (the source has none; carry-over only, no fabrication).
- No git submodule, no upstream-sync automation. One-shot vendored import.

## Testing Strategy

This spec's verification mixes two modes from [`work-loop`](../../../.claude/skills/work-loop/SKILL.md):

- **Goal-based check** for the file-shape and content-shape ACs (AC1, AC2, AC3, AC4, AC4a, AC5, AC7, AC7a). Each AC closes when a one-liner — `agentbundle validate`, a grep, a file-presence check, an anchored text grep against this spec's Changelog — returns the expected exit code. CI-enforced via existing GitHub Actions workflow extensions.
- **TDD** for the install/uninstall state-machine AC (AC6a). A pytest test under `packages/agentbundle/tests/integration/` creates a temporary `$HOME`, runs `agentbundle install converters --scope user` against it, asserts the `~/.agent-ready/state.toml` shape, then runs `agentbundle uninstall converters --scope user` and asserts the state file is empty (or absent). The test's red is the file's non-existence before it's written; green is the first passing run.

Mode-per-AC mapping:

| AC | Mode | Why |
| --- | --- | --- |
| AC1 (pack.toml shape) | Goal-based | `agentbundle validate` is the one-liner; no logic to test. |
| AC2 (attribution scrub) | Goal-based | Inverted grep over `packs/converters/`; one-line gate. |
| AC3 (Rail C clean) | Goal-based | Same shape as AC2 with the marker grammar. |
| AC4 (evals carry-over) | Goal-based | File-presence checks; no state to exercise. |
| AC4a (evals JSON validity) | Goal-based | `python -m json.tool` + key-presence grep; one-liner per file. |
| AC5 (source SHA pinned) | Goal-based | Anchored Changelog grep + presence of `notes/source-sha.txt`. |
| AC6a (fixture-`$HOME` install/uninstall, local) | TDD | State machine (no install → installed → no install) with side effects — the integration test for the install contract. |
| AC6b (pytest CI invocation) | Goal-based | New GHA job runs and surfaces a check named in PR UI. |
| AC7 (runtime-dep disposition matches table) | Goal-based | File-presence + SKILL.md text greps. |
| AC7a (node_modules gitignore note) | Goal-based | Text grep against `markdown-to-html/SKILL.md`. |

## Acceptance Criteria

- [ ] **AC1 — `pack.toml` shape.** `packs/converters/pack.toml` declares `name = "converters"`, `version = "0.1.0"`, `[pack.adapter-contract] version = "0.2"`, `[pack.install] default-scope = "user"`, `allowed-scopes = ["user", "repo"]`. `agentbundle validate packs/converters/` exits zero.

- [ ] **AC2 — source-attribution scrub.** A scrub grep targeting `packs/converters/` returns zero hits both at the implementer's machine pre-merge and as a CI step. Concretely: `rg -i --hidden '\bdropkit\b' packs/converters/` exits non-zero (= zero hits). The four named hits enumerated in [RFC-0007 § Source-attribution scrub](../../rfc/0007-user-scope-converter-pack.md#source-attribution-scrub) are each addressed per disposition: 3 × `manifest.json` files dropped; `markdown-to-html/scripts/render.js:30` comment rewritten in path-neutral terms. (Grep idiom note: `--hidden` is required because the imported skills live under `.apm/`, which ripgrep treats as hidden by default; the `-E` flag from earlier drafts of this spec maps to `--encoding=NAME` in ripgrep 15+ and was removed — `\b` word-boundaries work in ripgrep's default regex mode without it.)

- [ ] **AC3 — Rail C clean.** `rg --hidden '<adapt:[A-Z_][A-Z0-9_]*>|<adapt:[a-z][a-z0-9-]*>' packs/converters/` exits non-zero (= zero hits) both pre-merge and in CI. (Same grep idiom note as AC2: `--hidden` to traverse `.apm/`; no `-E` because ripgrep 15+ treats it as `--encoding`.) Both strict-uppercase and canonical lowercase-hyphen grammars (per [ROADMAP.md § distribution-adapters](../../ROADMAP.md#distribution-adapters--shipped-v02-contract-bump-landed) AC21 carve-out) are covered by the alternation. **The AC treats any literal `<adapt:...>` sequence as a violation, including prose and fenced code blocks in SKILL.md or references.** Converter SKILL.md files do not document marker grammar, so the AC is non-firing in practice; if a future maintainer wants to discuss markers in pack-side prose, this AC has to be amended.

- [ ] **AC4 — `evals/` carry-over.** Per-skill: where the source has an `evals/evals.json`, the pack carries it verbatim under `packs/converters/.apm/skills/<skill>/evals/evals.json`. Where the source has no `evals/`, none is created. No `evals/` directory under `packs/converters/.apm/skills/msg-to-markdown/`. The per-skill carry-vs-validated disposition is recorded in **one canonical place — this spec's Changelog entry pinned by AC5**; this AC4 bullet is a presence-only check, not a duplicate-state risk.

- [ ] **AC4a — `evals/evals.json` JSON validity + canonical keys.** For each carried `evals.json`: `python -m json.tool < <path>` exits zero (valid JSON), AND a JSON-key check confirms top-level keys `skill_name` and `evals` are present. Implementation: a CI step in the same workflow that runs the scrub + Rail C greps. Note: this validates *shape*, not *behaviour* — running the eval prompts against the scripts is out of scope per `Ask first`.

- [ ] **AC5 — Source commit SHA pinned.** Two artifacts must agree:
  - `docs/specs/converters-pack/notes/source-sha.txt` exists, contains exactly one line of the form `<40-hex-char SHA>\n`, and is committed (not gitignored).
  - This spec's Changelog has a dated entry of the form `- YYYY-MM-DD: initial import from source commit <same 40-hex SHA>` (this is governance text per § Never-do carve-out; naming the source by its repo URL or catalogue name is not required and not added).
  - Anchored grep: `grep -E '^- [0-9]{4}-[0-9]{2}-[0-9]{2}: initial import from source commit [a-f0-9]{40}$' docs/specs/converters-pack/spec.md` returns the entry.

- [ ] **AC6a — fixture-`$HOME` install/uninstall test (local + per-PR pre-merge).** A test at `packages/agentbundle/tests/integration/test_install_converters_user_scope.py` matching the project's canonical sibling-test idiom (verified: `unittest.TestCase` + `unittest.mock.patch.dict(os.environ, {"HOME": str(tmp_home)})` + **in-process** `install.run(argparse.Namespace(...))` via `from agentbundle.commands import install` — *not* a subprocess shell-out; see `test_install_user_hooks.py` for the reference shape):
  - Sets up TestCase fixtures matching `test_install_user_hooks.py:_UserScopeInstallBase`: `self.tmp = Path(tempfile.mkdtemp())` (root, with `addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)`), `self.home = self.tmp / "home"`, `self.repo = self.tmp / "repo"`, `self.cat = self.tmp / "catalogue"` (the temporary catalogue, with a `packs/converters/` substructure populated via `shutil.copytree` from the repo-local `packs/converters/`).
  - Calls `install.run(argparse.Namespace(pack="converters", catalogue=str(self.cat), output=str(self.repo), scope="user", force=False, force_merge=False))` and asserts exit code 0.
  - **HOME-resolution guard:** asserts `(self.home / ".agent-ready").exists()` *before* any state-file shape assertions. If the CLI's HOME-resolution doesn't propagate (`Path.home()` caching, etc.), this assertion fires first and gives a clear error.
  - Asserts `self.home / ".agent-ready" / "state.toml"` schema-version equals whatever `agentbundle.config.STATE_SCHEMA_VERSION` currently exports — the constant is the contract; a hard-coded literal is a snapshot that rots when a future RFC bumps the schema. The `converters` entry is recorded with `scope = "user"` and `len(state.packs["converters"].files) > 0` (the install→state→uninstall data flow runs through this dict; uninstall reads it to know what to remove).
  - Asserts the projected primitives land under `self.home / ".claude" / "skills" / "file-to-markdown"`, `.../markdown-to-html/`, `.../msg-to-markdown/`.
  - Calls `uninstall.run(argparse.Namespace(pack="converters", root=str(self.repo), scope="user"))` — note the uninstall surface is narrower than install (no `catalogue`, no `output` — uses `root`, see `cli.py` uninstall subparser); asserts the projected primitives are gone AND a single boolean `not state_path.exists() or "converters" not in load_state(state_path).packs` (the looser form covers both empty-table and file-removed implementations; expressed as one `assertTrue` rather than a conditional that silently no-ops when the file is gone).
  - Test passes when invoked locally via `pytest packages/agentbundle/tests/integration/test_install_converters_user_scope.py`.

- [ ] **AC6b — pytest CI invocation.** A new GitHub Actions job (in `build-check.yml` or `docs.yml`) runs `pytest packages/agentbundle/tests/integration/test_install_converters_user_scope.py` on every PR targeting `main`. The job surfaces in the PR's checks list with a distinct name. This is a **new CI surface** — no `pytest` invocation exists in `.github/workflows/` today (verified). The new job's existence is itself an AC.

- [ ] **AC7 — runtime-dep disposition matches [RFC-0007 table](../../rfc/0007-user-scope-converter-pack.md#runtime-dependencies).**
  - `packs/converters/.apm/skills/markdown-to-html/package.json` exists and pins `marked` + `highlight.js`.
  - `packs/converters/.apm/skills/file-to-markdown/SKILL.md` contains the `pip install docling Pillow` command.
  - `packs/converters/.apm/skills/msg-to-markdown/SKILL.md` contains the `npm install @nicecode/msg-reader` command and the `msgreader` fallback.
  - No `package.json` in `file-to-markdown/` or `msg-to-markdown/` (source ships none).

- [ ] **AC7a — `node_modules/` gitignore recommendation in `markdown-to-html/SKILL.md`.** Per [RFC-0007 § Drawbacks (`node_modules/` install location)](../../rfc/0007-user-scope-converter-pack.md#drawbacks): the SKILL.md contains a one-line note recommending `.claude/skills/*/node_modules/` in `.gitignore` for repo-scope installs. Grep: `grep -F 'node_modules' packs/converters/.apm/skills/markdown-to-html/SKILL.md` returns the recommendation. The pack itself ships no `.gitignore` (would cross into seed territory).

## Changelog

<!-- Dated entries; the source commit SHA pin (AC5) lands here at import time. Per § Never-do carve-out, governance text in this Changelog may name the source as part of stating the scrub rule — but is not required to. -->

- 2026-05-24: initial import from source commit 95aff2587808259212603aa5628f82db5dbc5e1e
