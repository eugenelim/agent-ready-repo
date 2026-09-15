# Plan: review-recurrence-family-key

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`packs/AGENTS.md`](../../../packs/AGENTS.md),
  [`packs/core/AGENTS.md`](../../../packs/core/AGENTS.md),
  [`docs/architecture/loop-contract.md`](../../architecture/loop-contract.md)

## Approach

Compute a second digest where the first one is already computed, and put it on
the payloads that already carry the first. Two tasks: derive and expose, then
document and version.

The slice is deliberately storage-free. A first draft carried storage, rotation
and derived counts; review established that the record verb receives digests as
command-line arguments and never re-parses the report, so storage needs a new
input path and a decision about the recorded payload digest. Those travel
together in the follow-on unit the spec names.

## Constraints

- The out-of-bounds surfaces are the spec's *Never do*.
- `packs/AGENTS.md` owns the export boundary, the version-bump file set, and the
  self-host projection rule.

## Construction tests

All in `packs/core/tests/skills/work-loop/test_loop_cohort.py`, the suite that
already owns the finding parser and the classifier, and that carries the
existing `matches_previous_round` assertions this change must not move.

Run as `python3 -m pytest packs/core/tests/skills/work-loop/test_loop_cohort.py -q`.

## Durable-output map

| Spec durable output | Task | Evidence at closeout |
| --- | --- | --- |
| Interface compatibility — `finding-adjudication.md` | T2 | AC-0009 |
| Current architecture — `loop-contract.md` | T2 | AC-0010 |
| Release history — `changelog.md` | T2 | Entry present with the core version bump |
| Reusable learning | post-ship | `project-knowledge --capture` at the next semantic gate; not a task here |

## Design (LLD)

### Data & schema

This section is the canonical home for both preimage forms; the spec's criteria
and the reference doc cite it rather than restating it.

| Reviewer format | Fingerprint preimage (unchanged) | Family preimage |
| --- | --- | --- |
| Backtick-quoted citation | `<file>\|<line>\|<title>` | `<file>\|<stable-title>` |
| Unquoted `file:line` | `<file>\|<line>\|<title>` | `<file>\|<stable-title>` |
| `Where: <location>` | `<location>\|0\|<title>` | `<location>\|<stable-title>` |

The stable title is the captured title with the enclosing `**` removed, the
leading ordinal removed, and a leading bracketed severity tag removed if
present. Both digests are SHA-256 hex over UTF-8, matching the existing form.

No `state.json` key is added.

### Design decisions

**Two keys, not one changed key.** Replacing the fingerprint's preimage would
change within-round dedup — two findings sharing a location and a stable title
at different lines would collapse — which moves recorded counts and the recorded
payload digest. That digest refuses a differing value under a recorded operation
id, so changing it breaks replay.

**The family strips position, not content.** The spike below establishes which
parts of the captured title move. A reviewer-assigned finding id stays.

**JSON only.** The human-readable result line is a hand-written format naming
three fields; a list of digests is noise there. Adding the key to it would be a
separate edit, and the spec's Assumptions record that it is not made.

### Disconfirming spike (run 2026-09-14, not committed)

The load-bearing assumption was that a finding's title is stable across rounds.
It is not. Re-derive with:

```
python3 - <<'PY'
import re, pathlib
RE = re.compile(r"^(?P<title>\*\*\d+\.[^*]+\*\*)")
titles = [m.group("title")
          for p in pathlib.Path("packs/core/tests").rglob("*.py")
          for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
          if (m := RE.match(line.strip().lstrip('"\'')))]
sev = re.compile(r"^\*\*\d+\.\s*\[[^\]]+\]")
print(len(titles), sum(bool(sev.match(t)) for t in titles))
PY
```

At the time of the spike this returned 21 captured titles, of which 13 carried a
bracketed severity tag; the leading ordinal is in all of them because the
pattern requires it. Dropping only the line — the original scope — would have
failed on the renumbering a converging round produces by definition. The spike
moved the family preimage from location-plus-title to location-plus-stable-title
and added two criteria. The counts describe a mutable test corpus and are a
dated observation, not a contract.

### Failure, edge cases & resilience

The `invalid` return is a distinct code path from the classified return and is
the one most likely to be missed; AC-0007 names it explicitly and contracts its
value. A report that parses to zero findings yields an empty family list by the
same path as an empty fingerprint list.

## Tasks

### T1: Derive the family and put it on the classification payloads

**Depends on:** none

**Tests:**
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0005 as one table over the
  stable-title normaliser — the
  three same-family cases and the two different-family cases, so a normaliser
  that strips too much also reds.
- AC-0006 — one case per reviewer format, asserting a family wherever there is a
  fingerprint. The `Where:` case exercises the location branch.
- One case fixing that a reviewer-assigned finding id survives normalisation, so
  a later widening has to move an assertion.
- AC-0007 — one case per named payload, including the `invalid` return and its
  contracted empty list.
- AC-0008 — the raw-classify field set compared against its current members.
- AC-0011 — the existing `matches_previous_round` assertions run unchanged.

**Approach:**
- Normalise the captured title once, where the three finding patterns already
  agree on the `title` group, rather than at each call site.
- Emit both digests from the same parse; the components are in hand before the
  existing hash is computed.
- Add the key to the `invalid` return in the same edit, not as a follow-up.

**Done when:** the new cases are green and no existing assertion changed.

### T2: Document and version

**Depends on:** T1

**Tests:**
- AC-0009 and AC-0010 — presence assertions against the required wording, not
  against the topic. AC-0009's "nothing consumes it yet" clause is the part
  worth asserting literally: it is what stops a later reader treating the key as
  a live signal.

**Approach:**
- `finding-adjudication.md`: name the key and cite this plan's *Data & schema*
  for the preimage. Do not attach it to the stasis row, whose disposition is
  "do not start another round".
- `loop-contract.md`: identity within a round is keyed with position; recurrence
  across rounds is keyed without it.
- Bump both pack manifests by one patch above whatever they hold at execution
  time — this branch already carries an unreleased bump from another change, so
  a literal target fixed now would be a no-op — and add the changelog entry in
  the same commit.
- Run `FORCE=1 make build-self` last.

**Done when:** `make lint-ruff lint-mypy` is clean, the work-loop suites are
green, and `agentbundle catalogue verify --root .` returns ok.

## Rollout

- **Delivery:** big bang within the pack. The key is emitted and unread, so there
  is no behavior to flag. Reversible by reverting the commit; no migration,
  because no state is written.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** self-host runs after the version bump, not before.

## Risks

- **Semantic rewording is unmeasured.** The spike measured structural title
  instability. Whether reviewers reword titles between rounds was not
  measurable: no corpus of real multi-round reports was reachable. Consequence
  lands entirely in the follow-on unit, which is the first thing to compare
  families; this slice emits a key whose usefulness is untested by construction,
  and the spec's Testing Strategy says so.
- **Family collision.** Two genuinely distinct findings sharing a location and a
  stable title collide into one family. Harmless while nothing consumes the key;
  the follow-on has to state whether it is accepted.
- **The key acquires a consumer before the follow-on lands.** The spec's *Never
  do* forbids it and AC-0009's "nothing consumes it yet" wording is the shipped
  warning. Neither is a mechanical guard, and the spec's Testing Strategy states
  that plainly rather than implying a sweep protects it.

## Changelog

- 2026-09-14 — Drafted, then reduced. The first draft carried storage, rotation
  and derived counts. Adversarial review established that the record verb
  receives digests as command-line arguments and never re-parses the report, so
  the counts could only ever be zero and every criterion still passed. Rather
  than add an input path and a replay-digest decision, the unit was cut to
  derivation and exposure, and the rest is named as a follow-on. That also
  removed a criterion whose absence sweep would have red on the compliant
  document it required.
