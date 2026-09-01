# Probes taken before the contract was written

Recorded during PLAN, 2026-09-01, against merge base `a06fb2e6c` (core 2.18.2).
Each probe is side-effect-free and was run from the repository root.

## Probe 1 — an unknown top-level `workspace.toml` key is silently ignored

The question the contract rests on: does adding a `completion_receipts` array to
`workspace.toml` produce a finding today? If it did, the collection could not be
introduced without an engine change landing first, and a repository that adopted
it before upgrading would see its whole workspace refused.

```python
# scratchpad/probe1.py
import importlib.util, pathlib, sys
p = "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
spec = importlib.util.spec_from_file_location("eng", p)
eng = importlib.util.module_from_spec(spec)
sys.modules["eng"] = eng          # dataclasses resolves fields via sys.modules
spec.loader.exec_module(eng)

base = {"backlog": {"open": [], "closed": []}}
extra = dict(base, completion_receipts=[
    {"delivery_id": "alpha", "outcome": "completed",
     "completion_event": "merge", "evidence_ref": "pr:1"}])
for label, ws in (("control (no receipts key)", base), ("with completion_receipts", extra)):
    r = eng.run_canonical_reconciliation(ws, pathlib.Path("."))
    print(f"{label}: findings={[(f.code, f.path) for f in r.findings]} "
          f"legacy={len(r.legacy_memberships)}")
```

```
control (no receipts key): findings=[] legacy=0
with completion_receipts: findings=[] legacy=0
```

Two consequences the contract carries:

1. The collection is **additive** — a `workspace.toml` carrying receipts is
   valid to every shipped consumer, so the reader can be introduced without a
   coordinated migration.
2. The collection is **inert until read**, and a malformed receipt is currently
   dropped in silence. Silence is the wrong default for an assertion that
   satisfies a dependency gate, which is why AC3 through AC5 and AC12 refuse
   rather than ignore.

## Probe 2 — the review-artifact path is ignored

`git check-ignore -v .context/reviews/x.md` → `.gitignore:88 .context/`.
The finding-adjudication protocol's persisted reports therefore cannot be
committed by accident.

## Probe 3 — the asserted contract digest is current

`shasum -a 256 contracts/jsonschema/delivery-lifecycle-record.schema.json` →
`557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878`, equal to
the value Wave 6's spec pinned. AC40 restates it rather than inheriting it,
because a digest that is only stated in a frozen spec cannot be re-verified
without reading that spec.

## Probe 4 — the release surface's two version files

`packs/core/pack.toml` declares `2.18.2` and
`packs/core/.claude-plugin/plugin.json` declares `2.18.2`. There is no
`packs/core/plugin.json`; AC41 names the `.claude-plugin/` path because the
other does not exist.

`origin/main` was at core `2.18.2` when this was written and had moved twice
during discovery. The number is re-derived from `origin/main:packs/core/pack.toml`
immediately before the release surface is committed, not here.

## Probe 5 — the disconfirming spike, and what it changed

The plan first carried a **phase-shaped** rule: consult the receipt "after the
ordinary path established no status". One fixture disconfirmed it.

`scratchpad/probe5.py` builds a dependant that is `Approved` with an `Approved`
plan on disk — so its only possible refusal is its dependency — and points its
`needs` at a `spec` path with no membership and no file:

```
absent dependency target:
  dispatchable: False
  findings: [('missing_dependency', 'docs/specs/absent-target/spec.md',
              'dependency target missing')]
```

An absent target **never reaches** the terminal-status test.
`_dependency_metadata_safety_finding` refuses it first, and that helper returns
exactly one of five findings in a fixed order:

| Order | Condition | Code | May a receipt answer it? |
| --- | --- | --- | --- |
| 1 | `metadata.invalid_path` | `invalid_artifact_path` | No |
| 2 | `metadata is None or not metadata.exists` | `missing_dependency` | **Yes** |
| 3 | `not metadata.readable` | `unreadable_artifact` | No |
| 4 | invalid provenance parent | `invalid_artifact_path` | No |
| 5 | `metadata.refresh_conflict` | `refresh_conflict` | No |

The rule became **code-shaped**: consult the receipt when and only when that
helper returns `missing_dependency`. This is strictly better than the phase-
shaped rule in two ways. It is decidable at one point instead of requiring a
claim about everything that did not happen earlier; and it makes the spec's
non-override rails structural — with the gate on one code, there is no branch
where a receipt can replace an existing verdict, so AC15 pins a property the
implementation cannot violate without moving the gate.

The spike also produced AC15's member list. Rows 1, 3, 4, and 5 are the four
refusals a receipt may not answer, spanning three distinct codes; AC15
enumerates those three. Without the spike, AC15 would have pinned only
`invalid_artifact_path` and left `unreadable_artifact` and `refresh_conflict`
uncovered — two silent bypasses of a trust-boundary control.

Not committed: the spike script stays in the session scratchpad.
