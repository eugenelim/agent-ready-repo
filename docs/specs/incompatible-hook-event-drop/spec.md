# Spec: incompatible-hook-event-drop

- **Status:** Shipped (T1–T8 landed 2026-05-26)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/dropped-primitives-coverage/spec.md`](../dropped-primitives-coverage/spec.md) (shipped 2026-05-26 — primitive-type-level warning rail; this spec extends it to per-file event-level drops, reusing the same helpers and formatter); [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (`merge-into-agent-json` + `agent-event-vocabulary` semantics whose refusal sites this spec swallows for the hook-wiring primitive). Modifies [`packages/agentbundle/agentbundle/commands/validate.py`](../../../packages/agentbundle/agentbundle/commands/validate.py) (rails 4c/4d swallow the per-file compatibility refusal for the hook-wiring primitive; symlink + TOML-parse refusals continue to fail loudly), [`packages/agentbundle/agentbundle/commands/install.py`](../../../packages/agentbundle/agentbundle/commands/install.py) (warning-rail enumeration + formatter extended for event-level), and [`packages/agentbundle/agentbundle/build/scope_rails.py`](../../../packages/agentbundle/agentbundle/build/scope_rails.py) (refactor only — extract the safe-load layer that today lives inside `check_kiro_wiring` so validate.py can call the security/correctness rails without dragging the compatibility refusal it now swallows).

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

> **Scope: one PR.** The validate.py swallow, the install-time event-level enumeration, the formatter extension, and the regression tests all land in a single PR. Splitting risks the validate exits 0 but install still refuses (or vice versa) — opposite signals reaching adopters from the same condition.

## Objective

Stop throwing the baby out with the bathwater when a pack's hook-wiring file uses an event the target IDE doesn't understand.

**Concrete:** the `core` pack ships a session-start hook wired to Claude Code's `SessionStart` event. Kiro has no equivalent — neither its CLI (`agentSpawn / userPromptSubmit / preToolUse / postToolUse / stop`) nor its IDE (`fileSave / promptSubmit / agentStop / ...`) supports a session-start trigger. **Today the tool refuses the entire `core` pack when projecting to Kiro because of this one incompatible file.** A Kiro user who wanted core's skills + agents + other primitives — all of which translate fine — gets nothing. The validate refusal fires upstream of any warning, so the install never even reaches the user-friendly degradation rail PR #156 (`dropped-primitives-coverage`) just shipped.

**The fix in two parts:**

1. **Drop the incompatible file, install everything else.** When a hook-wiring file uses an event the target adapter's `agent-event-vocabulary` doesn't list (or, for Kiro CLI specifically, the file lacks the required `attach-to-agent` field), skip just that file. The pack's other primitives install normally.
2. **Tell the user clearly what got dropped.** At install time, surface a warning naming the file and reason as part of the same per-scope warning line PR #156 emits — so the install is visibly partial instead of refused outright. At validate time, surface the same information as `info:` to **stdout** (exit 0), so an adopter running `agentbundle validate <pack>` still sees which files won't carry to which adapters without the tool refusing the pack.

Example install-time wording (Kiro adopter installing `core`; in production both reason categories fire because `core`'s `session-start.toml` lacks an `attach-to-agent` field — see AC4b):

```
warning: pack core ships 1 command that kiro projects as 'dropped'; these
primitives will not be installed. Additionally, the following hook-wiring
file(s) will be skipped (event not in adapter vocabulary + kiro requires
'attach-to-agent'): hook-wiring/session-start.toml. The compatible
primitives (agents, hook-bodies, hook-wirings, and skills) will proceed.
```

Example validate-time wording (same pack, same adapter heuristic):

```
$ agentbundle validate packs/core
info: pack core: the following hook-wiring file(s) will not project to kiro
(event not in adapter vocabulary): hook-wiring/session-start.toml.
$ echo $?
0
```

**Why PR #156 didn't cover this:** that PR's warning rail is whole-primitive-type-level only — handles "Kiro drops all commands" but not "Kiro accepts hook-wirings in general, except this one uses an event Kiro doesn't know". Coarse-grained vs fine-grained; only the coarse one shipped. This spec adds the fine-grained per-file walk and the matching validate-side swallow.

**Success for the Kiro adopter:** `agentbundle install --pack core --scope repo --adapter kiro <root>` proceeds, emits one warning naming the per-file drop, and projects core's skills + agents + other compatible hook-wirings into the kiro tree.

**Success for the catalogue:** `agentbundle validate packs/core` exits 0; CI runs that previously failed on this refusal pass.

**Success for the catalogue's correctness invariants:** a hook-wiring file that's a symlink (security rail) or fails to parse (correctness rail) still refuses with exit 1; only the per-file *compatibility* refusal is swallowed.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines. *Always do* applies without asking; *Ask first* requires human sign-off before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Reuse the warning-rail helpers PR #156 just shipped.** `_enumerate_dropped_primitives`, `_format_dropped_warning`, `_maybe_emit_dropped_warning`, `_DROPPED_WARNING_SEEN` at `packages/agentbundle/agentbundle/commands/install.py:1030-1304` are the substrate this spec extends. New helpers (`_enumerate_event_dropped_wirings`) sit alongside; the existing helpers gain optional parameters for the event-level clause but their single-clause behaviour stays byte-identical when no event drops are present.
- **Keep `build/scope_rails.py` helpers pure-function-shape.** `check_kiro_attach_to_agent`, `check_kiro_event_vocabulary`, `check_kiro_wiring` continue to return `None` on accept and a refusal string on refuse. The validate.py swallow happens at the **call site**, not inside the helper. This preserves the helpers' reusability from any future caller that wants strict-refusal semantics.
- **Refactor `check_kiro_wiring`'s safe-load layer into its own callable** so validate.py can run the security/correctness rails (symlink check + TOML parse) without invoking the compatibility rail (`check_kiro_attach_to_agent`) it now swallows. The refactor extracts the existing walk in `scope_rails.py:414-468` into a sibling function (suggested: `_load_pack_hook_wiring_safely(pack_path, pack_name)` returning either a `(wiring_tomls, agent_basenames)` tuple OR a refusal string for symlink/parse-fail). `check_kiro_wiring`'s outward signature stays unchanged — it composes the new loader with `check_kiro_attach_to_agent`.
- **Pin the validate exit-code behaviour change with a regression test that names the specific refusal substrings** (`does not declare 'attach-to-agent'`, `not in adapter ... agent-event-vocabulary`). The test asserts validate exits 0 in their presence; a sibling test asserts validate still exits 1 on a symlink-or-parse-fail refusal. Both substrings are stable per PR #156's docs and RFC-0005's pinned wording.
- **Use `info:` (lowercase prefix) for validate's stdout text.** Matches Unix convention for informational messages and visually distinguishes from `warning:` (the install-time stderr prefix, which is the same rail viewed from a different operational context).

### Ask first

- **Changing the install-time warning's pinned wording grammar.** PR #156's primitive-type clause is already pinned by tests (`packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py`); extending the formatter must not break those — the new three-clause grammar must degrade byte-identically to the existing single-clause wording when no event drops are present. If a tradeoff surfaces that *would* change the existing wording (e.g., the closing `compatible primitives` clause needs reordering), surface it.
- **Extending the per-file walk beyond hook-wiring.** Other primitives (skill, agent, command, hook-body, kiro-ide-hook) have their own compatibility paths that aren't shaped like `agent-event-vocabulary`. If a second consumer surfaces during EXECUTE (the 3× rule), surface it as a follow-on spec — don't generalise inside this one.
- **Touching the existing helper signatures in `build/scope_rails.py`.** The refactor extracts a sibling function from `check_kiro_wiring`'s body; the existing public functions (`check_kiro_wiring`, `check_kiro_attach_to_agent`, `check_kiro_event_vocabulary`) keep their signatures byte-identical. If a cleaner shape requires breaking one, surface it.

### Never do

- **Promote the per-file drop to a refusal under any condition.** The warning-not-refusal stance is the shipped policy from `dropped-primitives-coverage`; this spec extends it, not reverses it. No new CLI flag (`--strict-hook-events` or similar) introduces a refusal path.
- **Touch `architect`'s or `credential-brokers`'s pack version.** Both were intentional defers from PR #156; this spec doesn't re-litigate that call.
- **Swallow any refusal from `check_kiro_wiring` other than the attach-to-agent and event-vocabulary categories.** Symlink rejection (security rail at `scope_rails.py:431, 458`) and TOML parse failure (correctness rail at `:440-443`) must continue to refuse with exit 1. The validate.py swallow discriminates by **which helper produced the refusal**, not by parsing the refusal string — accomplished by the safe-load refactor.
- **Emit the validate-time `info:` line on stderr.** Stdout is the right stream for non-error informational output; stderr is reserved for the install-time `warning:` and for genuine refusals. The asymmetry is intentional.
- **Add a new pack manifest field, contract field, or schema entry.** The fix lives entirely in the install handler and the validate.py call sites; the contract (`agent-event-vocabulary`, `merge-into-agent-json` mode, etc.) is unchanged.
- **Skip the cross-caller survey.** Before merge, grep `tools/`, `.github/`, `docs/` (excluding the spec/RFC files that document the refusal wording) for `does not declare 'attach-to-agent'` and `not in adapter.*agent-event-vocabulary` to confirm no CI/script consumer depends on the substrings. Survey already done 2026-05-26 (only spec/RFC documentation hits, no behavioural consumers); the AC pins the re-run as a goal-based check at merge time so a future caller added between draft and merge doesn't silently break.
- **Unify install-time and validate-time parse-fail handling for hook-wiring TOMLs.** The asymmetry per AC6c is **intentional**: install enumerates a parse-fail as a drop entry (visible in the warning, install proceeds); validate refuses with exit 1 (correctness rail, fix the file). A future refactor that "tidies" the two paths into one behavior would break either AC4 (validate would tolerate parse failures, hiding broken packs from CI gates) or AC6c (install would refuse parse failures, reintroducing the all-or-nothing refusal this spec set out to dismantle). The split is the contract.

## Testing Strategy

Behaviours map to verification modes as follows. Each user-visible outcome from the Objective is paired with a mode and a one-sentence why.

| Behaviour from Objective | Verification mode | Why this mode |
| --- | --- | --- |
| `agentbundle install --pack core --scope repo --adapter kiro <root>` proceeds and projects skills + agents + other compatible hook-wirings | **TDD** — integration test against the install handler with a fixture root. Asserts (a) rc 0, (b) on-disk projection of skills + agents into `.kiro/`, (c) absence of any kiro projection derived from `session-start.toml`. | Three-way observable; pins the end-to-end claim. |
| The install emits one warning naming the per-file drop alongside any primitive-type drops | **TDD** — integration test asserts stderr contains the exact AC-pinned wording for the kiro+core case (primitive-type clause for `command` + event-level clause for `session-start.toml` + closing clause). | The warning's exact wording is the load-bearing contract surface; a substring match (not exact) would admit grammar drift. |
| `agentbundle validate packs/core` exits 0 (no refusal) | **TDD** — focused regression test: invoke the validate command against `packs/core` (or a fixture with the same shape); assert exit 0; assert no `validate:` refusal on stderr. | Exit-code contract; the previous behavior was exit 1 with stderr text — the swallow must be observable. |
| Validate's stdout names which files won't project to which adapters | **TDD** — same regression test asserts stdout contains the exact `info:` wording for the kiro+core case. | Visibility contract; silence would defeat the spec's "tell the user clearly" success criterion. |
| Symlink-under-hook-wiring and TOML-parse-failure refusals still exit 1 | **TDD** — two focused tests with fixture packs constructed to trip each rail; assert exit 1 and the expected refusal substring on stderr. | The "swallow only compatibility refusals" Boundary is hard to enforce by inspection; pin it with tests so a refactor doesn't silently broaden the swallow. |
| The pre-bump warning text (primitive-type-only case, e.g. copilot + core) is byte-identical post-spec | **TDD** — the existing tests in `test_install_dropped_primitives_warning.py` stay green byte-for-byte. | Regression safety net; the formatter grammar change is additive, the single-clause case must not drift. |
| `<reason-summary>` ordering when both reasons fire on the same file | **TDD** — unit test on the formatter: a single file with both vocabulary AND attach-to-agent violations produces `<reason-summary>` = `event not in adapter vocabulary + kiro requires 'attach-to-agent'` (vocabulary precedes attach-to-agent). | Order is a contract surface adopters read; a pinned test prevents accidental swap during refactor. |
| Cross-caller survey at merge time confirms no consumer depends on the swallowed refusal substrings | **Goal-based check** — `grep -rn -E "does not declare 'attach-to-agent'\|not in adapter.*agent-event-vocabulary" tools/ .github/ docs/` returns only spec/RFC documentation hits (no behavioural code/CI consumer). | Substring contract verified by a one-liner; running it as a CI step is overkill but pinning the expectation in the AC keeps the survey reproducible. |
| `make build-self FORCE=1` produces a clean working tree | **Goal-based check** — `make build-self FORCE=1 && git status --short` empty. | Build-pipeline gate. |
| `python3 tools/hooks/pre-pr.py` exits 0 | **Goal-based check** — aggregate enforcement. | Covered by CI. |

## Acceptance Criteria

The spec is closed when each of the following observable outcomes is verifiable in the merged PR.

### Validate-side behaviour

- **AC1.** `agentbundle validate packs/core` exits 0 on the merged tree. No `validate:` refusal substring on stderr.
- **AC2.** The same invocation prints, to **stdout**, an `info:` line whose exact wording is produced by a single shared formatter (see AC6b). The four enumerated cases are byte-pinned by unit tests:
  - **One file, one reason:** `info: pack core: the following hook-wiring file(s) will not project to kiro (event not in adapter vocabulary): hook-wiring/session-start.toml.`
  - **One file, two reasons (vocabulary + kiro attach-to-agent):** `info: pack core: the following hook-wiring file(s) will not project to kiro (event not in adapter vocabulary + kiro requires 'attach-to-agent'): hook-wiring/session-start.toml.` Reason categories joined with ` + ` in the pinned order (vocabulary first).
  - **Two files, one reason each:** `info: pack <name>: the following hook-wiring file(s) will not project to kiro (event not in adapter vocabulary): hook-wiring/first.toml, and hook-wiring/second.toml.` Files in lexicographic order, serial-comma-plus-`and`.
  - **Adapter-name substitution:** the literal `kiro` is replaced with the resolved adapter name for any other future adapter that triggers the rail; the rest of the wording is invariant.
  
  The validate-time formatter is the sibling helper `_format_drop_message(mode="validate_info", ...)` of the install-time formatter (AC7); both live in one new module to keep validate-side and install-side wordings in sync (AC6b).
- **AC3.** A fixture pack that ships a hook-wiring entry that's a **symlink** under `.apm/hook-wiring/` causes `agentbundle validate <fixture>` to exit 1 with the existing `pack <name>'s hook-wiring entry is a symlink (not a regular file)` refusal on stderr. The security rail is untouched.
- **AC3b.** A fixture pack that ships an agent entry that's a **symlink** under `.apm/agents/` causes `agentbundle validate <fixture>` to exit 1 with the existing `pack <name>'s agent entry is a symlink (not a regular file)` refusal on stderr. The agent-side security rail (also reachable through `check_kiro_wiring` per `scope_rails.py:457-460`) is untouched.
- **AC4.** A fixture pack whose hook-wiring TOML is **malformed** (unparseable) causes `agentbundle validate <fixture>` to exit 1 with the existing `failed to parse` refusal on stderr. The correctness rail is untouched.
- **AC4b.** A fixture pack whose hook-wiring TOML references an **unknown agent** via `attach-to-agent = "ghost-agent"` (no `agents/ghost-agent.md`) causes `agentbundle validate <fixture>` to exit 1 with a refusal whose stderr text matches the existing refusal substring `does not declare 'attach-to-agent' (or names an unknown agent); required for kiro projection`. **The swallow at AC1 specifically covers (a) missing `attach-to-agent` and (b) out-of-vocab event names; it does NOT cover unknown-agent references** — those continue to refuse, because an install of such a pack would silently project to a non-existent agent target and the missing target is itself a correctness bug that the validate rail catches today and must continue to catch. **Implementation note (load-bearing per round-2 review):** `check_kiro_attach_to_agent` at `scope_rails.py:302-338` returns a **single composed refusal string** ("does not declare 'attach-to-agent' (or names an unknown agent); required for kiro projection") regardless of whether the missing-field branch or the unknown-agent branch fired. **Substring inspection of the refusal text cannot discriminate the two subcases.** Therefore validate.py's swallow logic must discriminate from the **input data**, not the refusal string: with the safe-load helper (T1) returning `(wiring_tomls, agent_basenames)`, the validate.py call site re-implements the two-branch check inline — `attach is not None and isinstance(attach, str) and attach not in agent_basenames` → unknown-agent refusal (kept, exit 1); otherwise the missing-attach case flows into the install-time enumerator's compat-drop list. The helper's signature stays unchanged; validate.py doesn't call `check_kiro_attach_to_agent` at all anymore for the swallow path — the helper remains in use by `check_kiro_wiring` for any code path that wants strict-refusal semantics.
- **AC5.** The swallow at `validate.py`'s rails 4c (`check_kiro_wiring`) and 4d (`check_kiro_event_vocabulary`) is scoped to the **hook-wiring primitive's compatibility refusals only** (categories: `attach-to-agent missing`, `event not in vocabulary`). Refusals from the **security rails** (hook-wiring symlink, agent symlink), the **correctness rails** (TOML parse failure, unknown-agent reference), rails **4a / 4b / 4e** (other primitive types), and any **future rail** keep their exit-1 behaviour. A regression test constructs a fixture that trips an `allowed-adapters` validation error (rail 4b territory — schema-cross-field, present in PR #140's test fixtures) and asserts validate still exits 1. The "future rail" clause is unfalsifiable by construction (no test can pin behaviour for code that doesn't exist); it lives in the AC as discipline for reviewers of follow-on PRs, not as a testable claim.

### Install-side behaviour

- **AC6.** The install handler computes an `[(wiring_relpath, reason_category)]` list of per-file hook-wiring drops for the resolved adapter, via a new helper `enumerate_event_dropped_wirings(pack_dir, adapter, contract)` defined in a new module `packages/agentbundle/agentbundle/commands/_drop_warning.py` and imported by both `install.py` and `validate.py`. The walk:
  1. If the resolved adapter has `hook-wiring` at `mode = "dropped"` at the type level, returns `[]` (the existing primitive-type rail covers it; no double-warning).
  2. For each `<pack_dir>/.apm/hook-wiring/<name>.toml` (sorted by basename, malformed files silently skipped):
     - For each `[[hooks.<EventName>]]` entry, if the resolved adapter's `[adapter.<name>.projections.hook-wiring].agent-event-vocabulary` is declared and the event name isn't in it, append `("hook-wiring/<name>.toml", "event not in adapter vocabulary")`.
     - If the resolved adapter is `kiro` AND the TOML lacks a top-level `attach-to-agent` field, append `("hook-wiring/<name>.toml", "kiro requires 'attach-to-agent'")`. **Unknown-agent references (`attach-to-agent = "ghost-agent"` with no matching `agents/ghost-agent.md`) are NOT enumerated here** per AC4b — that's a correctness refusal that validate still catches with exit 1; install-time projection would surface as a downstream projection error if not caught.
     - If the TOML fails to parse, append `("hook-wiring/<name>.toml", "hook-wiring TOML failed to parse")` per AC6c. (Note: validate refuses with exit 1 on parse-fail per AC4; install proceeds with the same file enumerated as a per-file drop — the asymmetry is resolved at AC6c.)
  3. Returns the list. **One drop entry per `(file, reason_category)` pair** — never concatenated. The formatter dedups at the file level for `<file-list>` rendering.
- **AC6b.** The same `enumerate_event_dropped_wirings` helper is the single source of truth for both validate-time and install-time enumeration. `validate.py`'s rails 4c/4d call `enumerate_event_dropped_wirings(pack_path, "kiro", contract)` (kiro is the heuristic target adapter at validate time per the existing `_kiro_target_adapters` logic) and pass the result to `_format_drop_message(mode="validate_info", ...)`. The install handler calls the same enumerator per scope and passes the result to `_format_drop_message(mode="install_warning", ...)`. The shared module `_drop_warning.py` exports: the enumerator, the formatter with a `mode: Literal["install_warning", "validate_info"]` parameter, and any helper predicates (`_is_primitive_type_dropped`, `_adapter_agent_event_vocabulary`) the enumerator needs.
- **AC6c.** When a hook-wiring TOML fails to parse: validate-time refuses with exit 1 per AC4 (correctness rail); install-time emits the per-file drop entry with reason `hook-wiring TOML failed to parse`. The asymmetry is **intentional and documented** — validate is the development-time gate where parse failures are loud bugs; install is the adopter-time degradation rail where the parse failure becomes one more reason a file won't project. An adopter running install without validate still sees the broken file named in the install-time drop warning, so the parse failure isn't silent.
- **AC7.** `_format_dropped_warning` is extended to compose a **three-clause grammar**:
  - **Primitive-type clause** (fires when `dropped_counts` is non-empty): `pack <name> ships <count-list> that <adapter> projects as 'dropped'; these primitives will not be installed.` (Byte-identical to PR #156's wording.)
  - **Event-level clause** (fires when `event_drops` is non-empty): `the following hook-wiring file(s) will be skipped (<reason-summary>): <file-list>.` When the primitive-type clause is also present, prefixed with `Additionally, ` (capital `A`, comma-space after).
  - **Closing clause** (fires when either prior clause did): `The compatible primitives (<compatible-list>) will proceed.`
  
  The full line starts with `warning: ` and joins firing clauses with a single space. `<reason-summary>` is the **deduped set** of reason categories from `event_drops`, in pinned order: `event not in adapter vocabulary` precedes `kiro requires 'attach-to-agent'`. When both categories are present, joined with ` + ` (space-plus-space). `<file-list>` is the **lexicographically sorted, file-level-deduped** list of `hook-wiring/<name>.toml` paths, joined with serial-comma-plus-`and`.
- **AC8.** When `event_drops` is empty, the formatter output is **byte-identical** to PR #156's shipped wording. Pinned by an explicit byte-string assertion in a new test `test_format_warning_pre_amendment_wording_pinned` that quotes the shipped wording inline (not by reference to "what the existing tests pass") so an accidental edit of the existing tests in the same module is caught. The verbatim shipped wording (single-clause case) is:
  > `warning: pack core ships 1 command that codex projects as 'dropped'; these primitives will not be installed. The compatible primitives (agents, hook-bodies, hook-wirings, and skills) will proceed.`
  The test asserts this exact string for the `pack=core, adapter=codex, dropped_counts={"command": 1}, compatible_types=["skill","agent","hook-body","hook-wiring"], event_drops=[]` input. (`<compatible-list>` is pluralized + lexicographically sorted + serial-comma-plus-`and` joined — the PR #156 formatter grammar; the input is unsorted singular but the output is sorted plural.) Existing tests at `packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py` also stay green without modification — the new test is belt-and-suspenders, not duplicative, because it catches the case where someone edits *both* the existing tests *and* the formatter to match a drifted wording.
- **AC9.** `_maybe_emit_dropped_warning` is extended to call `_enumerate_event_dropped_wirings` and pass its result to the formatter. The short-circuit key (`(root, pack_name, adapter, scope)`) is unchanged — both drop kinds derive from the same inputs; one warning per scope per process covers both.
- **AC10.** Integration test: `agentbundle install --pack core --scope repo --adapter kiro <root>` on the merged tree exits 0; stderr contains the exact three-clause warning naming `hook-wiring/session-start.toml`; the on-disk projection writes each kiro agent JSON to `<root>/.kiro/agents/<attach-to-agent>.json` (per the contract `[adapter.kiro.projections.hook-wiring].target.repo = ".kiro/agents/<attach-to-agent>.json"` at `_data/adapter.toml`); no agent JSON's `hooks.SessionStart` key contains an entry derived from `session-start.toml`; skills land at `<root>/.kiro/skills/<skill>/SKILL.md`. **Positive control:** `--adapter claude-code` projection of the same pack writes the SessionStart hook entry into the claude-code projection target (per `[adapter."claude-code".projections.hook-wiring]` — typically `<root>/claude-plugins/core/.claude/settings.local.json`'s `hooks.SessionStart` key under RFC-0012 repo-scope dist-tree). The per-file drop is per-adapter, not blanket.

### Documentation surface

- **AC12.** `docs/specs/README.md` gains a row for `incompatible-hook-event-drop`.
- **AC13.** `docs/backlog.md` gains a section recording the spec → shipped milestone.

### Cross-caller integrity

- **AC14.** At merge time, the cross-caller survey command excludes the doc directories that legitimately reference the substrings as documentation:
  ```
  grep -rn -E "does not declare 'attach-to-agent'|not in adapter.*agent-event-vocabulary" \
    tools/ .github/ docs/guides/ docs/architecture/ docs/product/
  ```
  This is expected to return **empty**. (Spec / RFC / ADR directories — `docs/specs/`, `docs/rfc/`, `docs/adr/` — legitimately quote the refusal text as documentation per RFC-0005's pinned wording and the parent `dropped-primitives-coverage` spec; they're excluded from the survey because their citations don't constitute behavioural consumption.) Initial survey was run 2026-05-26 and returned empty for the whitelisted directories. The AC pins re-running the same command at merge time so a caller added between draft and merge can't slip past.

### Gates

- **AC15.** `pytest packages/agentbundle/` exits 0.
- **AC16.** `make build-self FORCE=1 && git status --short` produces no output.
- **AC17.** `python3 tools/hooks/pre-pr.py` exits 0.

## Assumptions

- Technical: today's refusal point is `agentbundle validate packs/core` exiting 1 at `validate.py:196-199` (`check_kiro_wiring`) and `:209-217` (`check_kiro_event_vocabulary`) (source: read `packages/agentbundle/agentbundle/commands/validate.py` 2026-05-26).
- Technical: `check_kiro_wiring` composes four distinct refusal categories — `hook-wiring entry is a symlink` (security), `agent entry is a symlink` (security), `failed to parse` (correctness), `does not declare 'attach-to-agent'` (compatibility) (source: read `packages/agentbundle/agentbundle/build/scope_rails.py:414-468` 2026-05-26). The compatibility refusal is the only one this spec swallows.
- Technical: PR #156 (`dropped-primitives-coverage`, merged 2026-05-26) ships `_enumerate_dropped_primitives`, `_format_dropped_warning`, `_maybe_emit_dropped_warning`, `_DROPPED_WARNING_SEEN` in `packages/agentbundle/agentbundle/commands/install.py:1030-1304` — the reuse substrate this spec extends (source: read `install.py` 2026-05-26).
- Technical: Kiro's `agent-event-vocabulary` is `["agentSpawn", "userPromptSubmit", "preToolUse", "postToolUse", "stop"]` — `SessionStart` is not in it (source: `_data/adapter.toml [adapter.kiro.projections.hook-wiring]`).
- Technical: `packs/core/.apm/hook-wiring/session-start.toml` declares `[[hooks.SessionStart]]` — confirms the load-bearing case is real (source: read `packs/core/.apm/hook-wiring/session-start.toml`).
- Technical: cross-caller survey found no CI/tool consumer of the refusal substrings — only RFC-0005 and spec documentation hits (source: `grep -rn` 2026-05-26).
- Process: shipped specs are frozen per `docs/CONVENTIONS.md:80` — a new spec is required for follow-ons rather than amending `dropped-primitives-coverage` in place (source: `docs/CONVENTIONS.md:80`).
- Product: warning-not-refusal — extending PR #156's stance, no flag introduces refusal path (source: user confirmation 2026-05-26).
- Product: install-time three-clause formatter grammar is option (A) — extend the existing single formatter, degrade byte-identically when event list is empty (source: user confirmation 2026-05-26).
- Product: validate-time output is `info:` to **stdout**, exit 0 (source: user confirmation 2026-05-26).
- Product: `<reason-summary>` order is vocabulary-then-attach-to-agent; drop entries are `(file, reason-category)` tuples, never concatenated (source: user confirmation 2026-05-26).
- Product: spec lifecycle Draft → Implementing → Shipped via single-PR atomicity precedent (source: user confirmation 2026-05-26).
