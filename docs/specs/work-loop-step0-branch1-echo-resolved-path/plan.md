# Plan: work-loop-step0-branch1-echo-resolved-path

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

## Constraints

- Source file is `packs/core/.apm/skills/work-loop/SKILL.md`; projected copy is `.claude/skills/work-loop/SKILL.md`. Edit source; propagate via `make build-self FORCE=1`.
- `docs/specs/spec-C-workloop-argless-resume/spec.md` is a shipped spec — update it in-place; no new file needed.

## Risks

- `make build-self FORCE=1` may fail if source and projected copy are already out of sync from other in-progress changes. Mitigate: run `git status` before editing; if dirty, stash first.

## Tasks

### Task 1 — Edit SKILL.md source: Branch 1 bullet

**Mode:** Goal-based check
**Depends on:** none

In `packs/core/.apm/skills/work-loop/SKILL.md`, find the Active spec bullet block:

```
Exactly one → begin on that spec without asking.
```

Change to:

```
Exactly one → state the resolved spec path in the orientation block
(e.g., "Beginning on `docs/specs/<slug>/spec.md`") and begin on that spec.
```

**Done when:** `grep -n "state the resolved spec path" packs/core/.apm/skills/work-loop/SKILL.md` exits 0.

---

### Task 2 — Edit SKILL.md source: closing resolution paragraph

**Mode:** Goal-based check
**Depends on:** Task 1

In `packs/core/.apm/skills/work-loop/SKILL.md`, find the closing paragraph starting with:

```
if exactly one active item, strip the `spec/` prefix, then read
```

Update to include the echo instruction before "read":

```
if exactly one active item, state the resolved path (e.g.,
"Beginning on `docs/specs/<slug>/spec.md`") in the orientation block, strip
the `spec/` prefix, then read
```

**Done when:** The closing paragraph includes both "state the resolved path" and "then read" in the updated order.

---

### Task 3 — Edit spec-C AC2 Branch 1 clause

**Mode:** Goal-based check
**Depends on:** none

In `docs/specs/spec-C-workloop-argless-resume/spec.md`, find AC2 Branch 1:

```
begin the loop on that spec without asking.
```

Change to:

```
state the resolved path in the orientation block (e.g.,
"Beginning on `docs/specs/<slug>/spec.md`") before beginning.
```

**Done when:** `grep -n "state the resolved path" docs/specs/spec-C-workloop-argless-resume/spec.md` exits 0.

---

### Task 4 — Propagate source change

**Mode:** Goal-based check
**Depends on:** Tasks 1, 2

Run `make build-self FORCE=1`.

**Done when:** Command exits 0.

---

### Task 5 — Full gate

**Mode:** Goal-based check
**Depends on:** Tasks 3, 4

Run `make build-check`.

**Done when:** Command exits 0.
