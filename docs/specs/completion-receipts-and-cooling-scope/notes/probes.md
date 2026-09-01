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

## Probe 6 — a colon-bearing `delivery_id` is a confined repository-relative path

Round-1 review claimed a criterion's premise was false. It was.

| Value | `_is_repository_relative_path` | `_confined_artifact_path` |
| --- | --- | --- |
| `delivery:wave4` | `True` | resolves to a path |
| `runtime-coordination:workspace` | `True` | resolves to a path |
| `docs/specs/x/spec.md` | `True` | resolves to a path |
| `../escape/x.md` | `False` | `None` |
| `/abs/x.md` | `False` | `None` |
| `a\b.md` | `False` | `None` |

`_is_repository_relative_path` rejects only a leading `/`, a drive-letter
prefix, a backslash, a control character, and `.`/`..`/empty segments — a colon
is not among them. So `delivery:wave4` resolves to `<root>/delivery:wave4`: a
confined path that names no file. The criterion that called it "not a confined
repository-relative path" was a category error, now restated as AC17.

The same table settles a second question. `_confined_artifact_path` returns
`None` for a non-relative value *and* for an escaping one, so those two classes
are indistinguishable at that helper — but they are distinguishable one level
up, because `_is_repository_relative_path` separates them. AC18 therefore covers
both classes in one criterion rather than splitting them across two with
conflicting outcomes.

## Probe 7 — the refusal rule against the only real corpus

Taken **before approval**, so no criterion is provisional. `workspace.toml`
carries zero `[[completion_receipts]]` entries and `docs/lifecycle/` holds only
`README.md`, so the nearest real corpus is every literal the shipped writer's
own tests pass for a receipt field.

`scratchpad/probe7.py` applies this contract's rule — string, non-empty after
stripping, at most 512 characters, no character with ordinal below 32 or equal
to 127 — to each:

| Field | Value | Verdict |
| --- | --- | --- |
| `delivery_id` | `""` | reject: empty |
| `delivery_id` | `delivery:current` | accept |
| `delivery_id` | `delivery:wave4` | accept |
| `outcome` | `completed` | accept |
| `completion_event` | `event:shipped` | accept |
| `completion_event` | `work-loop:gates-clean` | accept |
| `evidence_ref` | `authority:resolved-policy` | accept |
| `evidence_ref` | `evidence:current` | accept |
| `evidence_ref` | `evidence:current-coordination` | accept |
| `evidence_ref` | `evidence:current-receipt` | accept |

**10 accepted, 1 rejected.** The single rejection is the shipped test's own
deliberate malformed case, which expects `receipt-evidence-required` from the
writer — so the reader refuses exactly what the writer refuses, and no shipped
writer value is refused. The rule needs no change and the criteria are final.

One correction to the measurement itself: the first run also reported
`outcome = "in-flight"` as accepted. That was a regex artifact — the pattern
`outcome="([^"]*)"` also matches `lifecycle_outcome="in-flight"`, which is a
`classify_disposition` argument and is the *invalid* case that test asserts
(`lifecycle-outcome-invalid`). It is not a receipt value. The receipt `outcome`
corpus is the single value `completed`, and the closeout vocabulary is fixed at
`close_work.py:986` as `{completed, abandoned, superseded}`.

## Probe 8 — three refusals follow the safety helper, not one

Probe 5's table was **incomplete as a statement about the receipt gate**, and
round-1 review caught it. `_dependency_metadata_safety_finding` returns five
findings, but `_dependency_is_satisfied` carries two more refusals *after* it:

```
2678:    if safety_finding is not None:
2679:        return False, safety_finding          # the five-return helper
2680:    if brief_scope_unknown:
2685:        return False, _finding(
2686:            "unsatisfied_dependency", dep.path, "brief child scope is unknown")
2691:    if _dependency_terminal_satisfied(dep.kind, status, metadata):
2692:        return True, None
2693:    return False, _finding("unsatisfied_dependency", dep.path, "dependency not terminal")
```

Reading the code changed one criterion's stated finding code. The comment at
`:2681-2684` records that `brief_scope_unknown` sits deliberately *below* the
safety check, "because a missing, unreadable or invalid-path brief has a
concrete cause". So a `brief` dependency whose artifact is absent already
returns `missing_dependency` today — it never reaches `brief_scope_unknown`.
AC24 first said such a dependency "stays blocked with `unsatisfied_dependency`",
which is the code it would carry only if the artifact existed. Corrected to
`missing_dependency`.

The substantive decision AC24 records is scope discipline rather than a
bypassed control: a completion receipt is admissible evidence about the brief in
principle, but `cooling-brief-child-scope` is deferred to Wave 7b, and letting a
receipt answer the unknown-child-scope case would decide that deferred question
implicitly. The receipt gate is therefore keyed on `missing_dependency` **in the
general arm only**, leaving the `defect` arm's own `missing_dependency` return
and both post-helper refusals untouched. AC24, AC25, and AC22 pin the three.

