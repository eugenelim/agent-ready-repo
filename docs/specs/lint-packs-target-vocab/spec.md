# Spec: lint-packs-target-vocab

- **Status:** Drafting
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0001 (base adapter contract; byte-equal projection invariant). The new gate **refuses** offending source content; it never rewrites at emit time. No `adapter.schema.json` or `adapter.toml` change here.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Pack authors editing `packs/<pack>/.apm/skills/<name>/SKILL.md` or
`packs/<pack>/.apm/agents/<name>.md` find out at `make build` time —
not at adopter install time — when a name or description exceeds the
strictest declared per-target constraint. Today a 2000-character
description in a skill or agent is silently accepted; downstream, the
Kiro agent-JSON projection writes the field through unchanged, and
Kiro / Codex either reject or ellipsis-truncate it at install. The
gate moves that failure forward to where the pack author can fix it.

The constraints come from a new sibling file `docs/contracts/target-vocab.toml`,
**not** from `adapter.toml`. Adding tables under `adapter.toml`'s target
blocks would change the contract grammar (require an `adapter.schema.json`
update) — that's RFC scope. Sibling-file scope is PR scope.

## Non-goals

Out of scope, *intentionally*:

- **Tool-name vocabulary gating.** Our adapters do not translate Claude
  tool names (`Bash`, `Read`, …) to Kiro / Droid vocab today; they
  pass through byte-equal. A source-side gate refusing Claude vocab
  would force pack authors to ship Kiro vocab, which would break
  Claude Code projection. Until either a per-target rewriter lands or
  the source format gains a canonical cross-target tool vocab, the
  gate has no workable shape.
- **Hook event vocabulary gating.** Same architectural shape: source
  `[[hooks.SessionStart]]` is Claude vocab; Kiro consumes the same
  TOML via `merge-into-agent-json` without translation. A source-side
  refusal would break Claude Code. Reachability is also low today
  (one hook-wiring TOML ships).
- **Per-target rewriting in adapters.** The gate refuses; it never
  rewrites.
- **Changes to `adapter.schema.json` or `adapter.toml`.** Sibling
  vocab file only.
- **Adding new adapter targets** (droid / gemini / opencode / pi).
  Each is its own RFC.
- **Changes to `tools/lint-agent-artifacts.py`.** It lints the projected
  layer; the new gate sits at the pack-source layer.
- **Fixing the projection-layer leak of Claude tool names and event
  names into Kiro JSON.** An adopter installing a Kiro-target pack
  today will see Claude tool names land in `.kiro/agents/<name>.json`;
  whether Kiro tolerates that is an open empirical question. If
  reachability rises (a Kiro consumer ships that exercises the
  hook-wiring path), revisit. Not addressed here.

## Boundaries

### Always do

- Edit `packs/<pack>/.apm/...` upstream and let projection flow; the
  gate runs over `.apm/skills/` and `.apm/agents/` source directories
  in every pack discovered under `packs/`.
- Keep findings in the form `{pack_name}: {message}: {relpath}` — the
  **relpath is the trailing `": "`-delimited segment**, matching the
  existing portability findings produced by `lint_pack()`'s
  `_PACK_SUBTREES` `rglob("*")` walk. This is load-bearing because
  `test_findings_are_sorted_by_relpath` splits on the last `": "`
  and the deterministic-ordering AC depends on every finding having
  a real relpath at the tail. Emit to stderr, exit non-zero, no
  stdout decoration.
- Compute the **strictest** constraint across all targets declared in
  `target-vocab.toml`. The gate's question is "would this source
  survive projection to **any** declared target", so the binding cap
  is `min(description-max-length)` and the binding length is
  `min(name-max-length)` across declared targets. Each finding names
  the binding target(s); when multiple targets tie on the strictest
  value, the rendering is `binding target: <comma-joined, sorted
  ASCII-order>` (e.g. `binding target: codex, kiro`). For
  `name-pattern` findings — where the configuration requires every
  declared target to agree byte-equal — the rendered list is *every*
  declared target, sorted ASCII-order (e.g. `binding target:
  claude-code, codex, copilot, kiro`).
- Refuse the configuration when targets disagree on `name-pattern`.
  Regex intersection is not well-defined, so the gate fails loud
  (AC11-shape) if two declared targets carry different
  `name-pattern` strings rather than silently picking one. Every
  declared target's `name-pattern` must be byte-equal to the others
  for the configuration to load.
- Record, per cap, its upstream source URL and the date it was
  checked, inside `target-vocab.toml` as comments above each table.
  Auditors a quarter from now must be able to verify a value without
  reading this conversation.
### Ask first

- Tightening the gate beyond the union of currently-declared per-target
  caps (e.g. introducing a stricter project-wide ceiling). This spec
  pins behavior to "would survive projection"; tighter ceilings are a
  separate policy decision.
- Extending the gate to primitives other than `skill` and `agent`.
  Commands, hook-body, and hook-wiring don't carry adopter-visible
  descriptions today; adding them would change the contract surface
  the gate covers.

### Never do

- **Edit `adapter.schema.json` or add tables under `adapter.toml`'s
  per-target blocks.** That's RFC scope, not PR scope.
- **Rewrite source content to make the gate pass.** The gate is
  fail-loud; pack authors fix the source.
- **Translate names or descriptions at projection time** to avoid the
  gate. Adapters stay byte-equal-passthrough.
- **Skip silently when the vocab file is missing or malformed.** The
  gate exits non-zero with a clear error naming the config file.
  Silently passing because the constraints could not be loaded would
  regress the whole point of the gate (see AC11).
- **Accept multi-line or YAML-folded descriptions in frontmatter.** A
  description using `>`, `|`, or a continuation-line shape is refused
  with a finding `description must be a single-line value`. Silent
  under-counting would tell the author the source is clean while
  projection still breaks at install — worse than no gate (see AC12).
- **Collapse the gate's findings into existing `lint-agent-artifacts.py`
  output.** The two lints sit at different layers (source vs.
  projected) and run from different `make` targets.

## Acceptance Criteria

1. **AC1 — Sibling vocab file exists and is auditable.**
   `docs/contracts/target-vocab.toml` declares per-target constraints
   for at least the four targets `adapter.toml` enumerates today
   (`claude-code`, `kiro`, `copilot`, `codex`). Each per-target table
   carries `description-max-length` (integer) and `name-pattern`
   (regex string); Kiro additionally carries `name-max-length = 64`.
   The file parses with stdlib `tomllib`. Each constraint key
   (`description-max-length`, `name-pattern`, `name-max-length`) is
   preceded by a TOML comment naming the upstream source
   (documentation URL or spec page) and the date it was checked.
   Every declared target's `name-pattern` in the shipped file is
   byte-equal to every other's. (The loader's refusal contract for
   inconsistent patterns lives in AC11; AC1 governs only the
   in-tree file's shape.) No JSON schema in this PR; no follow-up
   planned (cited as such in the file header).
2. **AC2 — Skill name pattern check.** A pack whose
   `.apm/skills/<name>/` directory name does not match the strictest
   `name-pattern` (today: `^[a-z][a-z0-9-]*$`) produces a finding
   shaped `{pack}: skill/{name}: name does not match {pattern}
   (got '{candidate}'; binding target: {target}): {relpath}`. The
   frontmatter `name:` field, when present, is also checked against
   the same pattern; a mismatch produces a separate finding with
   the same shape — `{name}` slot stays the dir name; `{candidate}`
   carries the frontmatter value. The two finding kinds
   (`candidate == name` vs. `candidate != name`) are
   distinguishable by inspection of `(got '...')` against the slot.
   A pack whose dir name matches the pattern and has no
   frontmatter `name:` mismatch passes. A multi-line / folded
   `name:` value in frontmatter is refused per AC12.
3. **AC3 — Skill name length check.** A pack whose skill directory
   name exceeds the strictest `name-max-length` (today: 64) produces
   a finding shaped `{pack}: skill/{name}: name length exceeds
   {limit} (got {n}; binding target: {target}): {relpath}`. A pack
   within the limit passes. The length check applies to the
   on-disk dir / file-stem name only; frontmatter-`name:` length
   does not get a separate length finding (the pattern check
   already gates frontmatter names; agentless length on a
   frontmatter-only `name:` is not a documented projection risk).
4. **AC4 — Skill description length check.** A SKILL.md whose
   frontmatter `description` exceeds the strictest
   `description-max-length` (today: 1024) produces a finding shaped
   `{pack}: skill/{name}: description length exceeds {limit} (got
   {n}; binding target: {target}): {relpath}`. A SKILL.md with no
   `description` field, or one within the limit, passes silently —
   name pattern and length still run.
5. **AC5 — Agent name pattern + length checks.** Same shape as AC2 +
   AC3, but for `.apm/agents/<name>.md` files, with the primitive
   slug `agent`. The "name" is the filename without `.md`; the
   frontmatter `name:` field, when present, is also checked.
6. **AC6 — Agent description length check.** Same shape as AC4 but
   for agent files, with primitive slug `agent`.
7. **AC7 — Gate is wired into the existing entry point.** Running
   `python -m agentbundle.build.lint_packs --packs-dir packs/` emits
   any new findings to stderr, contributes them to the total in the
   summary line, and exits 1 if any pack has at least one finding.
   Clean packs still exit 0.
8. **AC8 — Existing portability checks unaffected.** Every test
   method in `packages/agentbundle/agentbundle/build/tests/test_lint_packs.py`
   that existed before this PR continues to pass unchanged after
   the PR lands. The new checks compose; they do not replace.
9. **AC9 — packs/core passes after the PR merges.** After the PR
   merges, `python -m agentbundle.build.lint_packs --packs-dir packs/`
   exits 0 against the in-tree `packs/` directory. The Rollout
   section's two-commit recommendation is process guidance; AC9
   pins only the final-tree behavior.
10. **AC10 — Findings sort deterministically by trailing relpath.**
    The new findings interleave with the existing portability
    findings in sorted-by-relpath order — same algorithm as the
    existing `test_findings_are_sorted_by_relpath`: split on the
    last `": "` and sort. AC10 holds because every new-finding shape
    pinned in AC2–AC6 places a real relpath as the trailing segment.
11. **AC11 — Missing or malformed vocab file fails loud.** If
    `docs/contracts/target-vocab.toml` cannot be found, is malformed,
    parses to a structure without per-target tables, or declares
    inconsistent `name-pattern` values across targets,
    `cmd_lint_packs` exits non-zero with a stderr line naming the
    config file and the failure reason (no per-pack findings; the
    failure is pre-walk). The vocab file is located by walking up
    from the resolved `--packs-dir`; if that walk fails the loader
    falls back to walking up from `lint_packs.py`'s own ancestor
    chain (so a `--packs-dir` outside the repo still picks up the
    in-tree vocab during normal operation). The gate exits non-zero
    only when **both** walks fail. The legacy pre-PR tests in
    `LintPackTests` rely on the module-ancestor fallback (their tmp
    `packs-dir` is under `/var/folders/...`); the new
    `test_missing_vocab_file_fails_loud` test exercises the
    both-walks-fail path by patching the module's `_VOCAB_RELPATH`
    to a sentinel that exists nowhere.
12. **AC12 — Multi-line frontmatter values are refused.** A
    SKILL.md or agent .md whose `description:` or `name:` value
    uses YAML folding (`>`, `|`, or continuation lines following
    an empty scalar) produces a finding `{primitive}/{name}:
    description must be a single-line value` or `{primitive}/{name}:
    name must be a single-line value` respectively (shape:
    `{pack}: {primitive}/{name}: {field} must be a single-line
    value: {relpath}`). The frontmatter parser is intentionally
    minimal; multi-line shapes are refused rather than mis-parsed.
    The rule covers `name:` as well as `description:` because the
    same rationale applies — silent under-counting would leave a
    folded `name:` projecting to Kiro JSON in a broken shape.

## Testing Strategy

Three modes, mapped to the spec's outcomes:

- **TDD (logic — the new checks).** Construction tests under
  `packages/agentbundle/agentbundle/build/tests/test_lint_packs.py`,
  one positive + one or more negative fixtures per check (AC2–AC6,
  AC11, AC12). Fixtures build in `tempfile.TemporaryDirectory()`
  mirroring the existing test style — no on-disk fixture under
  `tests/fixtures/lint_packs/` beyond the existing `clean/`
  baseline. Each negative test asserts (a) the expected number of
  findings, (b) the finding string contains the primitive slug, the
  name, the violating dimension (`name`, `description`), the
  binding limit, and the binding target. Each positive test asserts
  the lint returns `[]` for an equivalent clean fixture.
- **Goal-based check (AC1, AC7, AC9, AC11).** `python -c "import
  tomllib; tomllib.loads(open('docs/contracts/target-vocab.toml').read())"`
  passes. `python -m agentbundle.build.lint_packs --packs-dir packs/`
  exits 0 in the final tree. A vocab-file-missing temp-dir test
  asserts AC11.
- **Regression sweep (AC8, AC10).** Every pre-existing test method
  in `test_lint_packs.py` still passes; a new combining test
  asserts vocab and portability findings interleave in sorted
  order.

## Drawbacks

- **Two configuration sources for what "a pack must look like."**
  `adapter.toml` describes projection rules; `target-vocab.toml`
  describes pack-source caps. Adopters reading the contracts need
  to consult both. Mitigation: the `target-vocab.toml` file header
  cross-references `adapter.toml` and explains the split.
- **The strictest-cap collapse keeps the finding format flat.**
  When two targets tie on a cap, the finding names both (`binding
  target: codex, kiro`); when one is the sole binding floor, only
  that one. A future tightening of a different target's cap will
  silently change which target is named — the constraint is loaded
  fresh each run, so the finding tracks `target-vocab.toml` rather
  than a baked-in default.
- **Items 3 and 4 stay broken at projection time.** Kiro continues
  to receive Claude tool names and Claude hook event names through
  byte-equal passthrough. An adopter installing a Kiro-target pack
  today will see Claude tool names land in `.kiro/agents/<name>.json`;
  whether Kiro tolerates that is an open empirical question. If
  reachability rises (a Kiro consumer ships that exercises the
  hook-wiring path), revisit — either a rewriter RFC or a canonical
  cross-source-vocab RFC.

## Rollout

Two commits in one PR (process recommendation; AC9 pins only the
final tree):

1. **Gate introduction (mechanical).** Adds
   `docs/contracts/target-vocab.toml`, extends `lint_packs.py`, adds
   tests. After this commit, `make build` over `packs/` may fail if
   real violations exist.
2. **Real-pack fixes (mechanical).** Shortens any over-cap
   descriptions in `packs/core/.apm/{skills,agents}/` so the gate
   passes against the in-tree packs. No semantic content change
   beyond trimming.

The split is for reviewer ergonomics. A squash-merge would lose it,
but AC9 doesn't require the split to survive merge.
