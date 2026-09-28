# Verification ledger — intent renumber, reissue, and the tombstone

Measurements the spec's criteria rest on. This file is one of the two paths
AC-0001 excludes from the citation search by name, because it records vacated
paths as history.

## 2026-09-28 — a generated projection cites an intent, and it is tracked

Measured during the spec-mode adversarial review, when the citation sweep's
behaviour over a generated projection was found unstated.

`packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` cites
`docs/product/intents/FEAT-0001-intent-identity-and-registration.md`. Two
adapter-root projections of that file carry the same citation:

| Path | Role | Tracked | In `.gitignore` |
| --- | --- | --- | --- |
| `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` | source | yes | no |
| `.claude/skills/work-loop/scripts/lint-traceability.py` | projection | yes | no |
| `.agents/skills/work-loop/scripts/lint-traceability.py` | projection | yes | no |

What it bounds: a projection is inside AC-0001's derived set, so the citation
relation reaches it and the sweep cannot ignore it. What it does not bound: the
number of projections a rename touches, which grows with the self-host recipe's
projection roots and is not fixed by this measurement.

This is why the operation repoints the `.apm/` source and writes no projection,
and why AC-0001 folds the self-host step into "after a rename".

## 2026-09-28 — projection fidelity is owned by an existing gate, not by this slice

Measured while deciding whether AC-0018's conservation clause should reach a
projection. It should not: the rename never writes that file, so "no other
content in that file changes" over a projection is a property of the self-host
step. A version line, a header rewrite, or the `x.md` → `x.toml` extension
substitution would falsify it with the rename entirely correct.

The owning control, verified end to end:

| Link | Evidence |
| --- | --- |
| Diagnostic | `packages/agentbundle/agentbundle/catalogue_tooling/verify.py:1557-1581` — step 15 emits `CAT-V-015 self-host projection is out of date` |
| Chained into | `tools/repo/build_gate_chain.py:232-235` — `catalogue verify --root .` is the chain's first step |
| Target | `Makefile:161-166` — `make build-check` runs the chain |
| Trigger | `.github/workflows/build-check.yml` — runs on every pull request |
| Division of labour | `docs/architecture/agentbundle.md:291-292` — `CAT-V-015` owns source/projection drift, `CAT-V-014` owns `dist/` drift |

Checked rather than assumed: `_step_selfhost_drift` emits nothing when
`.adapt-discovery.toml` is absent (`verify.py:1564-1569`). That file exists at
the repository root, so the control fires here. The recorded blind spot in the
sibling gate — `CAT-V-014` returning `[]` when `dist/` is absent,
`docs/product/intents/gates-that-read-clean-while-gating-nothing.md:29` — is
about `dist/` output drift and does not reach `CAT-V-015`.

`tools/lint-generated-path-ownership.py:18-27` names duplicating this drift
gate as the thing not to do, and states that "content inside a present entry is
the drift gate's to answer".

What it bounds: AC-0018 excludes a generated projection, and nothing is left
unverified provided `CAT-V-015` stays in force. What it does not bound: whether
`CAT-V-015` remains chained into `build-check`. If that link is ever removed,
AC-0018's exclusion loses its cover and this decision needs revisiting.
