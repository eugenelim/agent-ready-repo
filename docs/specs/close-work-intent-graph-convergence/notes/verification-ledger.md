# Verification ledger: close-work intent graph convergence

Execution observations for slice 2. The spec and plan hold the obligations;
this file holds what execution measured and where it departed from a task
row's literal method.

## Pre-execution

- 2026-10-10, engine run `5d8b90bf-799e-4328-9e64-0b96cbca8c8a`: spec and plan
  approved by eugenelim after three spec-mode shaping and adversarial review
  rounds; every sustained Blocker and Concern was resolved. One advisory Nit is
  deferred: `ClosureNotEligible.live_descendants` stays `(slug, status)`, so a
  same-slug intent and brief appear as two pairs with no kind.
- The 2026-10-10 parent-kind search behind round 1's indeterminate finding 6:
  no test or tool pinned the resolver's `_PARENT_INTENT_KINDS` to
  `intent_shape.OUTCOME_CO_OWNER_KINDS`, so T4 retargets the pin (AC-0016).

## T1–T4

- T1 `5fc638ade`, T2 `772ade01e`, T3 `df7d45c82`, T4 `faaa75c91`. Each was
  implemented by an `implementer` subagent and re-verified by the controller:
  `make lint-ruff lint-mypy` clean; the close-work, pack, navigate-intents and
  parity-tool suites green (T4: 824 passed); `tools/check_closure_terminality_parity.py`
  exits 0 and reports 4 parent-intent kinds agreeing with upstream.
- T2 departure: `_graph_module_path` is a keyword of the default provider
  `_run_intent_graph`, reached in tests through `functools.partial`, on the
  pattern of `_run_resolver`'s `_resolver_path`.
- T2 departure: the descendant queue carries the artifact kind, so the
  `children` arm acts only on intent entries.
- T4 departure: the parity tool's test hook is a `resolver_path` keyword on
  `main()`, not a command-line flag.

## T5 — real-corpus verdict comparison (AC-0015)

- Base commit (pre-change code and the one corpus): `aa5a5048e`, checked out
  detached at `/tmp/s2base`. Head commit (post-change code): `faaa75c91`.
  Both `close-work/scripts/` folders were copied out of git; byte equality with
  each commit was confirmed with `cmp`.
- Command: `python -I compare.py /tmp/s2old /tmp/s2new /tmp/s2base` (Python
  3.14.3). Exit code **0**; 0 unattributed differences.
- Compared: 735 artifacts (168 non-tombstone intents, 23 briefs, 544 specs;
  14 tombstones excluded) and 43 distinct ancestors.
- Chain differences: 119 — cause 1: 103; cause 3: 16; cause 2: 0.
- Descendant-set differences: 3 ancestors, every differing member cause 3
  (a brief or spec dropped because a descendant intent shares its slug):
  - `first-class-distribution-routes` gains `spec:portable-agent-plugin-projection` (Shipped).
  - `optional-code-intelligence-composition` gains four specs, one of them
    `native-provider-selection-validation` (Draft).
  - `repository-work-graph` gains `brief:intent-identity-and-registration` and
    `spec:intent-delivery-traceability` (both Shipped).
- Verdict differences: 0.
- Closeout timing, post-change module: `resolve_intent_ancestors` for
  `catalogue-search-verb` plus `check_ancestor_closure` on its 3 ancestors took
  0.32 s wall.
- Departure from the T5 row: the script runs one resolver snapshot for both
  modules, so neither pays the subprocess per call. A first draft tested a
  descendant member for tombstones before slug sharing and mislabelled one
  cause-3 member as cause 2; the recorded run checks slug sharing within the
  set first.

Script source:

```python
"""Compare pre- and post-change close-work closure_index.py over one corpus (AC-0015).

usage: python3 -I compare.py <old_scripts_dir> <new_scripts_dir> <corpus_root>
"""
import importlib.util
import sys
import time
from collections import Counter
from pathlib import Path

OLD_DIR, NEW_DIR, ROOT = (Path(a).resolve() for a in sys.argv[1:4])


def load(name: str, d: Path):
    spec = importlib.util.spec_from_file_location(name, d / "closure_index.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


old = load("cmp_old_closure_index", OLD_DIR)
new = load("cmp_new_closure_index", NEW_DIR)
PREFIXES = ("capability:", "outcome:", "opportunity:")

# ---- enumerate artifacts from the base corpus files (independent of both modules)
intents_dir = ROOT / "docs/product/intents"
briefs_dir = ROOT / "docs/product/briefs"
specs_dir = ROOT / "docs/specs"
fields_of: dict[tuple[str, str], dict[str, str]] = {}
tomb_slugs: set[str] = set()
for p in sorted(intents_dir.glob("*.md")):
    f = old._preamble(p.read_text(encoding="utf-8"))
    if "Slug" not in f:
        continue
    if "Tombstone" in f:
        tomb_slugs.add(f["Slug"])
    else:
        fields_of[("intent", f["Slug"])] = f
for p in sorted(briefs_dir.glob("*.md")):
    f = old._preamble(p.read_text(encoding="utf-8"))
    if "Slug" in f:
        fields_of[("brief", f["Slug"])] = f
for p in sorted(specs_dir.glob("*/spec.md")):
    fields_of[("spec", p.parent.name)] = old._preamble(p.read_text(encoding="utf-8"))
artifacts = sorted(fields_of)
slug_kinds: dict[str, set[str]] = {}
for k, s in artifacts:
    slug_kinds.setdefault(s, set()).add(k)

# one resolver snapshot, shared, so neither side pays the subprocess per call
_snap = new._run_resolver(ROOT)
snap_provider = lambda root: _snap  # noqa: E731


def call(fn, *a, **kw):
    try:
        return ("ok", fn(*a, **kw))
    except Exception as exc:  # outcomes, not crashes
        return ("refused", f"{type(exc).__name__}: {getattr(exc, 'reason', None) or exc}")


def chain(mod, slug, kind):
    return call(mod.resolve_intent_ancestors, slug, kind, fields_of[(kind, slug)], ROOT,
                _snapshot_provider=snap_provider)


unattributed: list[str] = []
chain_causes: Counter = Counter()
desc_causes: Counter = Counter()
verdict_causes: Counter = Counter()
chain_diffs = desc_diffs = verdict_diffs = 0


def chain_cause(slug, kind, oc, nc) -> str | None:
    o = oc[1] if oc[0] == "ok" else None
    n = nc[1] if nc[0] == "ok" else None
    if o is None or n is None:
        return None  # a refusal on either side is not one of the three causes
    i = next((j for j in range(max(len(o), len(n)))
              if j >= len(o) or j >= len(n) or o[j] != n[j]), None)
    if i is None:
        return "same"
    walker = (o[i - 1][0] if i else slug)
    wkind = "intent" if i else kind
    val = fields_of.get((wkind, walker), {}).get("Parent intent", "")
    if val.startswith(PREFIXES):
        return "1"
    old_slug = o[i][0] if i < len(o) else None
    if old_slug is not None and old_slug in tomb_slugs:
        return "2"
    if wkind == "spec":  # first hop comes from the resolver snapshot, not a Parent intent value
        target = n[i][0] if i < len(n) else None
    else:
        target = val[len("intent:"):] if val.startswith("intent:") else None
    seen = {slug} | {h[0] for h in o[:i]}
    if target is not None and (target in seen or slug_kinds.get(target, set()) - {"intent"}):
        return "3"
    return None


for slug, kind in ((s, k) for k, s in artifacts):
    oc, nc = chain(old, slug, kind), chain(new, slug, kind)
    if oc != nc:
        chain_diffs += 1
        c = chain_cause(slug, kind, oc, nc)
        if c in ("1", "2", "3"):
            chain_causes[c] += 1
        else:
            unattributed.append(f"chain {kind}:{slug}\n    old={oc}\n    new={nc}")

# ---- distinct ancestors: union of both chains
ancestors: dict[str, tuple[str, str]] = {}
for slug, kind in ((s, k) for k, s in artifacts):
    for r in (chain(old, slug, kind), chain(new, slug, kind)):
        if r[0] == "ok":
            for a, st, term in r[1]:
                ancestors.setdefault(a, (st, term))

NEWKEY = lambda d: {k: (v.status, v.terminus) for k, v in d.items()}  # noqa: E731


def old_norm(d):
    return {(v.kind, v.slug): (v.status, v.terminus) for v in d.values()}


def verdict_sig(v):
    if isinstance(v, str):
        return v
    name = type(v).__name__
    return (name, getattr(v, "reason", None))


def member_cause(member, oset, nset):
    kind, slug = member
    members = set(oset) | set(nset)
    if any(s == slug and k != kind for k, s in members):
        return "3"
    if kind == "intent" and slug in tomb_slugs:
        return "2"
    return None


for anc, (st, term) in sorted(ancestors.items()):
    od = call(old._build_descendant_closure, anc, term, ROOT, _snapshot_provider=snap_provider)
    nd = call(new._build_descendant_closure, anc, term, ROOT, _snapshot_provider=snap_provider)
    dcause = None
    if od[0] == "ok" and nd[0] == "ok":
        os_, ns_ = old_norm(od[1]), NEWKEY(nd[1])
        if os_ != ns_:
            desc_diffs += 1
            diff = [m for m in set(os_) | set(ns_) if os_.get(m) != ns_.get(m)]
            cs = {member_cause(m, os_, ns_) for m in diff}
            print(f"  descendant diff {anc}: " + "; ".join(
                f"{k}:{sl} old={os_.get((k, sl))} new={ns_.get((k, sl))} cause={member_cause((k, sl), os_, ns_)}"
                for k, sl in sorted(diff)))
            if None in cs:
                unattributed.append(f"descendants {anc}: unexplained members "
                                    f"{sorted(m for m in diff if member_cause(m, os_, ns_) is None)}")
            else:
                dcause = sorted(cs)[0]
                for c in cs:
                    desc_causes[c] += 1
    elif od != nd:
        desc_diffs += 1
        unattributed.append(f"descendants {anc}: old={od[0]} new={nd[0]} "
                            f"{od[1] if od[0] != 'ok' else ''} / {nd[1] if nd[0] != 'ok' else ''}")
    ov = call(old.check_ancestor_closure, anc, st, term, ROOT,
              _freshness_checker=lambda: True, _snapshot_provider=snap_provider)
    nv = call(new.check_ancestor_closure, anc, st, term, ROOT,
              _freshness_checker=lambda: True, _snapshot_provider=snap_provider)
    so = (ov[0], verdict_sig(ov[1])) if ov[0] == "ok" else ov
    sn = (nv[0], verdict_sig(nv[1])) if nv[0] == "ok" else nv
    if so != sn:
        verdict_diffs += 1
        if dcause is not None:
            verdict_causes[dcause] += 1
        else:
            unattributed.append(f"verdict {anc}: old={so} new={sn}")

# ---- closeout timing, new module only
deep = max(((s, k) for k, s in artifacts if k == "intent"),
           key=lambda sk: len(chain(new, sk[0], sk[1])[1]) if chain(new, sk[0], sk[1])[0] == "ok" else -1)
t0 = time.perf_counter()
r = new.resolve_intent_ancestors(deep[0], "intent", fields_of[("intent", deep[0])], ROOT)
for a, st, term in r:
    new.check_ancestor_closure(a, st, term, ROOT, _freshness_checker=lambda: True)
elapsed = time.perf_counter() - t0

print(f"artifacts compared: {len(artifacts)} "
      f"(intents {sum(k == 'intent' for k, _ in artifacts)}, "
      f"briefs {sum(k == 'brief' for k, _ in artifacts)}, "
      f"specs {sum(k == 'spec' for k, _ in artifacts)}); tombstones {len(tomb_slugs)}")
print(f"distinct ancestors compared: {len(ancestors)}")
print(f"chain differences: {chain_diffs} by cause {dict(sorted(chain_causes.items()))}")
print(f"descendant-set differences: {desc_diffs} (member-level) by cause {dict(sorted(desc_causes.items()))}")
print(f"verdict differences: {verdict_diffs} by cause {dict(sorted(verdict_causes.items()))}")
print(f"closeout timing: intent {deep[0]}, {len(r)} ancestors, {elapsed:.2f}s wall")
print(f"unattributed: {len(unattributed)}")
for u in unattributed:
    print("  " + u)
sys.exit(1 if unattributed else 0)
```

## Implementation review

- Reviewers: `adversarial-reviewer`, `security-reviewer`, `quality-engineer`,
  and `experience-reviewer`, each adjudicated by `finding-adjudicator`. Reports
  under `.context/reviews/5d8b90bf-799e-4328-9e64-0b96cbca8c8a/`.
- Round 1 sustained 6 Concerns and 9 Nits; security was clean. Fixed in
  `a045eabc5`:
  - AC-0003's scan now flags any `Parent intent` key read in `closure_index.py`; it reds on the base file at three lines.
  - Eval case 20 describes a `kind_mismatch` child intent.
  - The dead directory-listing seam is removed, and vacuous `accessed_dirs` assertions are replaced by a counting-provider check.
  - The guide lists every `intent-graph-unavailable` code and where a broken parent link can be.
- Rounds 2 to 4 sustained wording and test-name fixes only, applied by the
  controller in `57b210213`, `8b36f9ce4`, and `b8b9e04c4` (recorded as
  `human-directed` declines, the nearest receipt reason). Final round: all four
  reviewers clean.
- Deferred Nits:
  - `_own_terminus` reports a failed ancestor re-read as `no-decomposed`. The verdict still refuses, and the path is reachable only when a file changes mid-run.
  - The `graph_provider_from_files` test helper resolves a parent by slug without a kind check. Every current fixture uses `intent:` parents, and the contract tests run the real copy.
  - `ClosureNotEligible.live_descendants` stays `(slug, status)` with no kind.
- Local gates on `b8b9e04c4`: lint and mypy clean; 1,079 passed, 4 skipped
  (close-work, navigate-intents, pack, parity tool, roster supersession); guide
  lints and the changelog projection test green.

## Version amendment — owner decision 2026-10-10

- Dispatched `test-corpus` run 38074666815 and `test-roster` run 38074668675
  failed on `c5bf03185`. Two of the three failures were wiring, fixed in
  `62c5edb1f`: the registration sat under `ini-007`, and the new roster test
  lacked its prune-manifest entry and named CI step.
- The third, `test_pack_delivery_contract_is_complete_and_version_increased`,
  measures `core` against `origin/main` (3.0.1). It requires exactly one bump
  there: 3.1.0, which slice 1 set on `feature/intent-navigation`. The plan's T6
  bumped to 3.1.1.
- Owner decision, eugenelim, 2026-10-10: fold slice 2 into `core` 3.1.0. Revert
  the version to 3.1.0, merge this slice's changelog lines into the
  `[core][3.1.0]` entry, and amend the plan through the controlled-amendment
  path with a new task, T7.
