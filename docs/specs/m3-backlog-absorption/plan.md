# Plan: m3-backlog-absorption

- **Status:** Draft
- **Spec:** [`spec.md`](spec.md)

## Constraints

- Single PR. All tasks land atomically — the dual-source lint (T4b) lets the migration
  (T2) and tombstone reduction (T3) land in any order within the PR, but the PR must
  contain all changes before CI gates run.
- Canonical source for skills: `packs/core/.apm/`; for CONVENTIONS.md: `packs/core/seeds/`.
  Never edit projected paths (`.claude/`, `.agents/`, `docs/CONVENTIONS.md`).
- `make build-self` must run before gate check — it syncs all three lint copies AND
  regenerates `docs/CONVENTIONS.md` from the seed.

## Risks

- **Staleness gap**: cannot mechanically verify every backlog item without reading each
  referenced spec. The stale-drop rule is: never drop a slug that has a live `(deferred:)`
  marker; for others, Shipped/Archived → drop, uncertain → retain with `# ?stale`.
- **RFC-0007 broken anchor**: `adapt-to-project--shipped-ac4b-transcripts-deferred`
  doesn't exist in current `backlog.md`; must create it in the tombstone.
- **Python version**: `tomllib` requires Python 3.11+; always code the regex fallback
  first and test it directly. `backlog_open_slugs` must catch `TOMLDecodeError` and fall
  back to regex (not return empty set) on malformed TOML.
- **CONVENTIONS.md is a projected seed**: T5 edits `packs/core/seeds/docs/CONVENTIONS.md`.
  After `make build-self` (T10), `diff` confirms `docs/CONVENTIONS.md` matches.

## Task list

### T1: Add `[backlog]` stub to workspace.toml

**Verification mode:** goal-based  
**Depends on:** none

Add the `[backlog]` top-level section to `workspace.toml` with an empty `open = []`
array, a header comment explaining the schema and the distinction from
`[ini-NNN.shaping_queue].backlog` (per the workspace.toml legend). Include a note
that entries are `{slug, needs?, source?}` objects with cold-start-sufficient
preceding TOML comments.

**Done when:**
```
python3 -c "import tomllib; d=tomllib.loads(open('workspace.toml').read()); assert d['backlog']['open'] == []; print('ok')"
```

---

### T2: Migrate backlog items from docs/backlog.md to workspace.toml [backlog].open

**Verification mode:** goal-based  
**Depends on:** T1

For each `## ` and `### ` section in `docs/backlog.md` that represents a work item:

1. **Stale check — live-marker gate (hard)**: Does a live `(deferred: <slug>)` marker
   exist in any spec.md or plan.md? If yes, the item MUST be migrated (never dropped).
   Run: `grep -r "(deferred: <slug>)" docs/specs/ --include="*.md"` to check.

2. **Stale check — spec-status gate (soft)**: If no live marker, grep the referenced
   spec slug: `grep -l "Status.*Shipped\|Status.*Archived" docs/specs/<slug>/spec.md`.
   If Shipped/Archived → item is stale, drop (don't migrate). If unsure → migrate with
   `# ?stale — verify before closing` prefix on the comment.

3. **Rewrite for cold-start sufficiency**: Write a TOML comment above each entry:
   - Problem: what gap/follow-on this tracks
   - Fix: what needs to happen to close it
   - Affected: which file, skill, or spec
   - Unblocks when: (if blocked on something)

4. **Entry shape**: `{slug = "<slug>", ...}` where `<slug>` exactly matches the
   GitHub-anchor slug of the backlog.md heading (lowercase, non-`[\w\s-]` stripped,
   spaces→hyphens). Add `source = "spec/<name> ACn"` for deferred-AC items.

**All 11 required slugs must be present** (spec AC2). The slugs currently in
single-line `(deferred:)` markers in spec.md files are:
`apm-install-route-parity`, `apm-leak-lint-rfc`,
`architect-review-diagram-knowledge-surfaces`, `artifactory-first-publish-gesture`,
`atlassian-sso-cookie-live-dc-read-transcript`, `cdn-sri-mermaid`,
`convenient-install-defaults-followons`, `credbroker-frozen-pack-ref-sweep`,
`extraction-msg-realworld-sample`, `ml-saas-serverless-workload-class-lenses`,
`upgrade-orphan-removal-on-projection-shape-change`.

Also migrate `pack-evals-converters-gate-consolidation` (live marker in plan.md)
and multi-line-form slugs for completeness (`extraction-msg-to-markdown-python-contract`,
`architect-review-diagram-knowledge-surfaces` two-line form). Whether `credbroker-phase-2`
belongs in `.open` depends on the stale audit — it is marked "Resolved 2026-06-10"
in backlog.md; the tombstone heading suffices for lint resolution; include it only
if there is genuinely open work remaining.

**Done when:**
```
python3 -c "
import tomllib
d = tomllib.loads(open('workspace.toml').read())
slugs = {e['slug'] for e in d['backlog']['open'] if isinstance(e, dict)}
required = {
    'apm-install-route-parity', 'apm-leak-lint-rfc',
    'architect-review-diagram-knowledge-surfaces', 'artifactory-first-publish-gesture',
    'atlassian-sso-cookie-live-dc-read-transcript', 'cdn-sri-mermaid',
    'convenient-install-defaults-followons', 'credbroker-frozen-pack-ref-sweep',
    'extraction-msg-realworld-sample', 'ml-saas-serverless-workload-class-lenses',
    'upgrade-orphan-removal-on-projection-shape-change',
}
missing = required - slugs
assert not missing, f'missing slugs: {missing}'
print('ok — all 11 required slugs present')
"
```

---

### T3: Reduce docs/backlog.md to tombstone stub

**Verification mode:** goal-based  
**Depends on:** T2 (confirm all items are migrated first)

Replace `docs/backlog.md` with a ~15-line tombstone. The file must contain:
1. A file-level header explaining it is a tombstone
2. Exactly the four headings below (in this order for logical grouping), each with
   a one-line pointer to the corresponding `workspace.toml` entry or resolved status:

```markdown
# Backlog (tombstone)

> **This file is an anchor-tombstone stub.** All open work has migrated to
> `workspace.toml [backlog].open`. This stub exists only to preserve heading
> anchors that Frozen RFC documents cannot be edited to update.

## `iac-terraform`

Migrated to `workspace.toml [backlog].open` — slug `iac-terraform`. See also: RFC-0065.

## adapt-to-project — Shipped: AC4b transcripts deferred

Migrated to `workspace.toml [backlog].open`. See also: RFC-0007.

### credbroker-phase-2

**Resolved 2026-06-10.** `credbroker 0.1.0` published to PyPI. Retained as anchor for RFC-0023.

## `extraction-tier0-and-output-contract`

Migrated to `workspace.toml [backlog].open` — slug `extraction-tier0-and-output-contract`. See also: RFC-0058.
```

**Verify the four required slugs are present:**
```python
python3 -c "
import re

def slugify(h):
    t = h.strip().lower().replace('\`', '')
    t = re.sub(r'[^\w\s-]', '', t)
    return t.replace(' ', '-')

text = open('docs/backlog.md').read()
slugs = {slugify(m.group(1)) for m in re.finditer(r'^#{1,6}\s+(.*?)\s*#*\s*$', text, re.M)}
required = {
    'iac-terraform',
    'adapt-to-project--shipped-ac4b-transcripts-deferred',
    'credbroker-phase-2',
    'extraction-tier0-and-output-contract',
}
missing = required - slugs
assert not missing, f'tombstone missing: {missing}'
print('ok')
"
```

---

### T4a: Write red TDD stubs for lint invariant (iv) dual-source rewrite

**Verification mode:** TDD  
**Depends on:** none (can write before migration)

Create `packages/agentbundle/tests/unit/test_lint_spec_status_deferred.py`.

The test file imports functions from the lint script — some don't exist yet
(`backlog_open_slugs`, `_regex_backlog_slugs`), making those tests red. Test (a)
drives `check()` end-to-end and is red because `check()` doesn't yet read
workspace.toml — it will pass the slug-in-neither violation even for a slug that's
only in workspace.toml, not the tombstone.

**Tests:**

```python
"""TDD stubs for lint-spec-status.py invariant (iv) dual-source rewrite.

Tests:
  (a) workspace-only slug passes check() — red until T4b wires the union
  (b) tombstone heading slug resolves — passes via existing backlog_anchors()
  (c) slug-in-neither is a HARD violation
  (d) absent workspace.toml → backlog_open_slugs returns empty set
  (e) malformed TOML drives through backlog_open_slugs (not just _regex helper)
  (f) _regex_backlog_slugs directly resolves slugs from [backlog].open
"""
import importlib.util, types
from pathlib import Path

_REPO_ROOT = Path(__file__).parents[4]
_SCRIPT = _REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py"


def _load_lint_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("lint_spec_status", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_workspace_only_slug_passes_check(tmp_path):
    """(a) Slug present only in workspace.toml [backlog].open — check() has no HARD violation."""
    lint = _load_lint_module()
    workspace = tmp_path / "workspace.toml"
    workspace.write_text('[backlog]\nopen = [{slug = "my-ws-only-slug"}]\n', encoding="utf-8")
    backlog = tmp_path / "docs" / "backlog.md"
    backlog.parent.mkdir(parents=True)
    backlog.write_text("# tombstone\n", encoding="utf-8")  # no heading with that slug
    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: my-ws-only-slug)\n",
        encoding="utf-8",
    )
    hard, _warn = lint.check(tmp_path, base_ref=None)
    # No HARD violation — slug resolves via workspace.toml
    assert not any("my-ws-only-slug" in v for v in hard)


def test_tombstone_heading_slug_passes(tmp_path):
    """(b) Slug from a docs/backlog.md heading resolves (tombstone backward-compat)."""
    lint = _load_lint_module()
    backlog = tmp_path / "docs" / "backlog.md"
    backlog.parent.mkdir(parents=True)
    backlog.write_text("### credbroker-phase-2\n\nsome text\n", encoding="utf-8")
    workspace = tmp_path / "workspace.toml"
    workspace.write_text("[backlog]\nopen = []\n", encoding="utf-8")
    anchors = lint.backlog_anchors(backlog.read_text())
    assert "credbroker-phase-2" in anchors


def test_slug_in_neither_is_hard_violation(tmp_path):
    """(c) Slug absent from both workspace.toml and backlog.md → HARD violation."""
    lint = _load_lint_module()
    specs = tmp_path / "docs" / "specs" / "my-spec"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        "- **Status:** Approved\n\n## Acceptance Criteria\n\n"
        "- [ ] do thing (deferred: nonexistent-slug)\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "backlog.md").write_text("# tombstone\n", encoding="utf-8")
    (tmp_path / "workspace.toml").write_text("[backlog]\nopen = []\n", encoding="utf-8")
    hard, _warn = lint.check(tmp_path, base_ref=None)
    assert any("nonexistent-slug" in v for v in hard)


def test_absent_workspace_toml_returns_empty_slugs(tmp_path):
    """(d) workspace.toml absent → backlog_open_slugs returns empty set."""
    lint = _load_lint_module()
    slugs = lint.backlog_open_slugs(tmp_path / "workspace.toml")
    assert slugs == set()


def test_malformed_toml_falls_back_via_backlog_open_slugs(tmp_path):
    """(e) Malformed TOML — backlog_open_slugs catches parse error, falls back to regex."""
    lint = _load_lint_module()
    workspace = tmp_path / "workspace.toml"
    # Valid enough for regex but invalid TOML
    workspace.write_text(
        '[backlog]\nopen = [\n  {slug = "alpha"},\n  invalid syntax here\n]\n',
        encoding="utf-8",
    )
    slugs = lint.backlog_open_slugs(workspace)
    # Regex fallback still finds the well-formed slug line
    assert "alpha" in slugs


def test_regex_backlog_slugs_helper(tmp_path):
    """(f) _regex_backlog_slugs directly resolves slugs from [backlog].open."""
    lint = _load_lint_module()
    text = '[backlog]\nopen = [\n  {slug = "alpha"},\n  {slug = "beta"},\n]\n'
    slugs = lint._regex_backlog_slugs(text)
    assert "alpha" in slugs
    assert "beta" in slugs
```

**Done when:** `pytest packages/agentbundle/tests/unit/test_lint_spec_status_deferred.py`
— test (a) fails (workspace-only slug still triggers HARD violation — check() doesn't
read workspace.toml yet); tests (d), (e), (f) fail with `AttributeError: module ... has no
attribute 'backlog_open_slugs'`. Tests (b) and (c) may pass (they use only existing
functions). This is the correct red state.

---

### T4b: Rewrite lint invariant (iv) to dual-source union

**Verification mode:** TDD (T4a stubs turn green)  
**Depends on:** T4a (red stubs written)

Edit `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`:

1. **Add `_regex_backlog_slugs(workspace_text: str) -> set[str]`**:
   ```python
   def _regex_backlog_slugs(workspace_text: str) -> set[str]:
       """Regex fallback: extract slug = "..." values from [backlog].open section."""
       slugs: set[str] = set()
       in_backlog = False
       for line in workspace_text.splitlines():
           if re.match(r'^\s*\[backlog\]', line):
               in_backlog = True
           elif re.match(r'^\s*\[', line) and '[backlog]' not in line:
               in_backlog = False
           if in_backlog:
               m = re.search(r'\bslug\s*=\s*"([^"]+)"', line)
               if m:
                   slugs.add(m.group(1))
       return slugs
   ```

2. **Add `backlog_open_slugs(workspace_path: Path) -> set[str]`**:
   ```python
   def backlog_open_slugs(workspace_path: Path) -> set[str]:
       """Read workspace.toml [backlog].open slugs as valid deferral anchors."""
       if not workspace_path.is_file():
           return set()
       text = workspace_path.read_text(encoding="utf-8", errors="replace")
       try:
           try:
               import tomllib
           except ImportError:
               try:
                   import tomli as tomllib  # type: ignore[no-redef]
               except ImportError:
                   return _regex_backlog_slugs(text)
           data = tomllib.loads(text)
           return {
               e["slug"]
               for e in data.get("backlog", {}).get("open", [])
               if isinstance(e, dict) and "slug" in e
           }
       except ValueError:
           return _regex_backlog_slugs(text)
   ```
   Note: `TOMLDecodeError` subclasses `ValueError` in both `tomllib` and `tomli`,
   so `except ValueError` catches all TOML parse errors and falls back to regex
   without swallowing unrelated programming errors.

3. **In `check()`, change the `anchors` computation**:
   ```python
   # Before:
   backlog_path = root / "docs" / "backlog.md"
   anchors = (
       backlog_anchors(backlog_path.read_text(encoding="utf-8", errors="replace"))
       if backlog_path.is_file()
       else set()
   )

   # After:
   backlog_path = root / "docs" / "backlog.md"
   workspace_path = root / "workspace.toml"
   anchors = (
       backlog_anchors(backlog_path.read_text(encoding="utf-8", errors="replace"))
       if backlog_path.is_file()
       else set()
   ) | backlog_open_slugs(workspace_path)
   ```

4. **Update error message** from `"does not resolve to a heading in docs/backlog.md"`
   to `"does not resolve in workspace.toml [backlog].open or docs/backlog.md"`.

**Done when:** all 6 T4a tests pass; `lint-spec-status.py --root . 2>&1; echo $?` → exit 0.

---

### T5: Update CONVENTIONS.md seed

**Verification mode:** goal-based  
**Depends on:** none (doc change, independent)

Edit `packs/core/seeds/docs/CONVENTIONS.md` (the projected source; NOT `docs/CONVENTIONS.md`
which is a projected copy that `make build-self` regenerates).

Find the deferral token definition at line ~301:
```
`<anchor>` resolves to a heading in `docs/backlog.md`, the durable register of
open work.
```

Update to:
```
`<anchor>` resolves to a `slug` field in `workspace.toml [backlog].open`, the
durable register of open work. (`docs/backlog.md` heading anchors are also accepted
for the four tombstone headings retained for Frozen RFC inbound links.)
```

Also find any other reference to `docs/backlog.md` in CONVENTIONS.md and update or
remove it (replacing with `workspace.toml [backlog].open` where appropriate).

**Done when (run AFTER T10's `make build-self`):**
```
diff packs/core/seeds/docs/CONVENTIONS.md docs/CONVENTIONS.md  # exit 0
grep 'docs/backlog.md' docs/CONVENTIONS.md  # returns empty / only tombstone context
```

---

### T6: Update new-spec template deferral example

**Verification mode:** goal-based  
**Depends on:** none

Edit `packs/core/.apm/skills/new-spec/assets/spec.md`. Find the deferral example
referencing `docs/backlog.md`. Update to reference `workspace.toml [backlog].open`.

**Done when:**
```
grep 'backlog.md' packs/core/.apm/skills/new-spec/assets/spec.md  # returns empty
```

---

### T7: Update work-loop SKILL.md (all backlog.md references)

**Verification mode:** goal-based  
**Depends on:** none

Edit `packs/core/.apm/skills/work-loop/SKILL.md`. There are three `docs/backlog.md`
references in the file, all need updating:

1. **DECIDE phase** — replace references to "record under a heading in `docs/backlog.md`"
   with "add an entry to `workspace.toml [backlog].open`". Add an explicit
   **"is this deferral justified?"** prompt: before recording a deferral, the agent
   must state in one sentence WHY the AC cannot be delivered in this PR (scope,
   dependency, risk, or capacity). The justification becomes the TOML comment for
   the `[backlog].open` entry.
2. **Invariant (iv) description** (around line 581) — update "deferral anchors
   resolve in `docs/backlog.md`" to "deferral anchors resolve in
   `workspace.toml [backlog].open` or the `docs/backlog.md` tombstone".
3. **Externalized memory note** (around line 915) — update "`docs/backlog.md` are
   the externalized memory" to reference `workspace.toml` as the primary memory.

**Note (out of scope):** `packs/core/.apm/agents/adversarial-reviewer.md` line ~154
also says `(deferred:)` "points to a real heading in `docs/backlog.md`" — this will
actively mislead post-migration. Logged as a `[backlog].open` follow-on
(slug: `adversarial-reviewer-deferral-resolution-update`); address in the next available
PR that touches adversarial-reviewer.md.

**Done when:**
```
grep 'docs/backlog.md' packs/core/.apm/skills/work-loop/SKILL.md  # returns empty
```

---

### T8: Update workspace-status SKILL.md to render [backlog]

**Verification mode:** goal-based + manual QA  
**Depends on:** T2 (workspace.toml has real entries to render)

Edit `packs/core/.apm/skills/workspace-status/SKILL.md`. Add a procedure step to
render a **Backlog** section after the initiative sections. When `[backlog].open`
is non-empty, emit:

```
**Backlog** (N open items — repo-level, not scoped to any initiative):
- `<slug>` — <first line of the TOML comment above this entry>
- `<slug>` — ...
```

Omit the section entirely when `[backlog].open` is absent or empty.

**Done when:** manual QA in session shows the Backlog section renders with
workspace entries.

---

### T9: Enumerate and repoint all inbound backlog.md#<anchor> links

**Verification mode:** goal-based  
**Depends on:** T3 (tombstone in place, so retained links remain valid)

Find and repoint all `docs/backlog.md#<anchor>` links in editable files. The full
set from research:

| File | Anchor | Action |
|------|--------|--------|
| `docs/specs/credbroker/spec.md` | `#credbroker` | Update prose to reference `workspace.toml [backlog].open`; remove or repoint the anchor link |
| `docs/specs/credbroker/spec.md` | `#credbroker-phase-2` | Tombstone retained — link still resolves; update prose to note it's resolved |
| `docs/specs/traceability-lint/spec.md` | `#sidecar-drift-hard-fail` | Update prose to reference `workspace.toml [backlog].open`; remove anchor link |
| `docs/specs/discovery-producer-type-markers/spec.md` (×2) | `#discovery-loop-type-marker-producers` | Update prose; remove anchor links |
| `docs/specs/discovery-producer-type-markers/plan.md` | `#discovery-loop-type-marker-producers` | Update prose |
| `docs/specs/credbroker-user-scope/plan.md` | `#active-with-credbroker-pip` | Update prose |
| `docs/specs/pack-activation-evals/plan.md` | `#behavior-check-for-backend-skills` | Update prose |
| `docs/specs/llm-agent-agentic-boundary-extension/plan.md` | `#…` (ellipsis in prose) | Update the guidance prose; no anchor link to fix |
| `docs/guides/_shared/how-to/preview-install-or-upgrade.md` | `#install-dry-run-preview-governance-seeds` | Update the `backlog` link to reference workspace.toml |
| `CONTRIBUTING.md` | `#credbroker-phase-2` | Tombstone retained — link resolves; update prose if needed |
| `docs/specs/README.md` | `#credbroker-phase-2` | Tombstone retained — link resolves |
| `packs/core/.apm/skills/export-catalogue/SKILL.md` | any | Remove or update any `docs/backlog.md` reference |

**Done when:**
```bash
# Scan the full repo (not just docs/) for non-tombstone backlog.md#<anchor> links;
# exclude m3 spec/plan files (they discuss migration) and the tombstone slugs.
grep -rn 'backlog\.md#' . --include="*.md" \
  | grep -v '\.git\|docs/specs/m3-backlog-absorption\|docs/backlog\.md' \
  | grep -v '#iac-terraform\|#credbroker-phase-2\|#extraction-tier0-and-output-contract\|#adapt-to-project--shipped-ac4b-transcripts-deferred'
# should return no matches
```

---

### T10: make build-self + full verification

**Verification mode:** goal-based  
**Depends on:** T1, T2, T3, T4b, T5, T6, T7, T8, T9

1. `make build-self` — projects all three lint copies; regenerates `docs/CONVENTIONS.md`.
2. `diff packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py .claude/skills/work-loop/scripts/lint-spec-status.py` — clean (exit 0).
3. `diff packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py .agents/skills/work-loop/scripts/lint-spec-status.py` — clean (exit 0).
4. `diff packs/core/seeds/docs/CONVENTIONS.md docs/CONVENTIONS.md` — clean (exit 0).
5. `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root . 2>&1; echo $?` — exit 0, no HARD violations.
6. `pytest packages/agentbundle/tests/ packages/agentbundle/agentbundle/build/tests/ -q` — all green.
7. `make build-check` — all green.

**Done when:** all 7 checks pass.

## Design notes

### Dual-source union design

Invariant (iv) accepts slugs from the union of:
- `workspace.toml [backlog].open` — all migrated items
- `docs/backlog.md` headings — backward-compat for the 4 tombstone anchors

This eliminates the atomicity problem: within the PR, T2 (migration) can happen
before or after T3 (tombstone reduction) without breaking CI. The lint doesn't
care which source the slug comes from.

### Why regex fallback

`tomllib` is Python 3.11+. Some CI runners and adopter machines may still be on
3.10. Rather than add `tomli` as a hard dependency, a simple regex fallback reads
`[backlog].open` slug values reliably given workspace.toml's predictable structure.
The `except ValueError` catch in `backlog_open_slugs` means malformed TOML always
falls back to regex rather than returning an empty set — preserving correctness even
when the TOML is invalid.

### Per-item audit responsibility

Each backlog item requires a stale check before migration:
1. **Hard gate**: Never drop a slug with a live `(deferred:)` marker in any
   `docs/specs/*/spec.md` (the set `lint-spec-status.py` enforces).
2. **Soft gate**: If the item has no live spec.md marker and its parent spec is
   Shipped/Archived, drop it as stale. Plan.md markers don't gate CI — those items
   may be dropped by the stale-audit. If unsure, retain with a `# ?stale` prefix.
3. **Rewrite**: The TOML comment must be cold-start-sufficient — someone reading
   workspace.toml with no prior context must understand the problem, fix, and
   unblock condition.

### docs/backlog.md Manual path

`docs/backlog.md` is a **Manual** seed path (line 370 of `self_host.py`): it is
NOT overwritten by `make build-self`. The seed at `packs/core/seeds/docs/backlog.md`
is only delivered on a fresh `agentbundle install` for new adopter repos — it is
not updated in this PR (the `docs/backlog.md` format is being deprecated in favour
of `workspace.toml [backlog].open`). T3 edits `docs/backlog.md` directly.

### Test placement split

The new pytest suite at `packages/agentbundle/tests/unit/test_lint_spec_status_deferred.py`
is a standard Python unit test discovered by pytest in the normal run. The existing
lint has a separate shell-driven test at
`packs/core/.apm/skills/work-loop/scripts/test-lint-spec-status.py` run via the
build gate chain. Both test the same script; the new suite tests the dual-source
functions specifically and rides the standard `pytest packages/agentbundle/tests/`
invocation rather than the build gate chain.

## Changelog

- 2026-07-20: spec authored (full mode, risk triggers: governance + structural + destructive).
- 2026-07-20: plan authored; adversarial review 1 addressed (Blocker: T5 seed path; Major: inbound links, AC2 count, stale rule, malformed TOML, red-state stubs; Minor: tombstone pointer, multi-line slugs); adversarial review 2 addressed (Blocker: T9 grep; Concerns: stale gate scope, AC3 typo, T7 scope expanded to include SKILL.md:581/915, except ValueError, T9 table); T3b removed (seed deprecated); adversarial-reviewer.md update deferred to backlog.
