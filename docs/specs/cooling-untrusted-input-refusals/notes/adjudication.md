# Adjudication — Wave 5 post-code review union, three unadjudicated Concerns

Adjudicator: `finding-adjudicator` (independent, Read/Grep only), 2026-08-28.
Target: `packs/core/.apm/skills/close-work/scripts/cooling.py` @ 97a0b6ad (Core 2.15.0).
Orchestrator supplied one measured observation for finding 3 (adjudicator cannot run code).

## Verdicts

| # | Claim | Verdict |
| --- | --- | --- |
| 1 | Success payload carries an absolute host path | **REFUTED** (observation accurate; authority does not reach it) |
| 2 | Issued write grant is never popped, so it is unlimited-use | **REFUTED** (observation accurate; no authority requires single use) |
| 3 | Over-long `timezone` escapes as `OSError` with path + errno | **SUSTAINED** |

## Finding 1 — REFUTED

Broken predicate: **authority**. Proposed mechanism: adequate.

The observation is accurate. `cooling.py:562` returns `mutated=(final_path,)`;
`final_path` is `destination / f"{delivery_id}.json"` (`:516`, `:443`) over the
`root`-joined destination (`:615`), so it is absolute whenever `root` is.
`update_record` propagates it (`:691`), `as_dict` calls itself "diagnostic-free"
(`:147-158`), and the repo-relative form is already computed one line later at
`:517`.

Contrary evidence: `docs/CONVENTIONS.md:1538` scopes the rule to committing "to
any file in this repo", and `:1550-1552` enumerates its reach as "all git
artifacts — code, comments, docs, specs, commit messages, PR titles, PR bodies,
and PR comments". A runtime return value is none of those. The path is never
persisted: `as_payload` (`:114-134`) emits only the repo-relative `locator` the
schema's `$defs/locator` pins. AC20 (`thirty-day-cooling-and-retirement/spec.md:214-216`) scopes its no-absolute-path
rule to "every refusal returned by the write seam", which the finding itself
concedes. `close_work.py:1797` is precedent, not a rule.

Independently verified by the orchestrator: `close-work/SKILL.md` references
`cooling.py` only as a seam (`:94`) and never emits `as_dict()` or `.mutated`
into a committed artifact; no consumer of `.mutated` exists outside
`tests/roster/test_thirty_day_cooling_and_retirement.py`.

Residual observation, not a defect: the `as_dict` docstring's "diagnostic-free"
claim is broader than what the success path delivers. Recorded, not repaired.

## Finding 2 — REFUTED

Broken predicate: **authority**. Proposed mechanism: over-broad.

The observation is accurate. The loop at `cooling.py:468-482` only reads
`_ISSUED_COORDINATION_AUTHORITIES` and never pops; the two Wave 4 pops
(`close_work.py:1780`, `:2017`) are both on the deletion path. No shipped test
drives two writes from one issued binding — `_binding`
(`tests/roster/test_thirty_day_cooling_and_retirement.py:340-365`) re-calls
`resolve_mutation_authority`, re-registering the fact, for every
`_enrol_kwargs` / `_update_kwargs` construction.

Contrary evidence: AC19 (`thirty-day-cooling-and-retirement/spec.md:207-213`) states the contract as a binding
"the shipped `_mutation_binding` returned for an issued authority fact" with a
matching `resource` — which `cooling.py:466-481` and `close_work.py:497-500`
satisfy exactly. It imposes no single-use rule. The more specific authority
scopes freshness elsewhere: RFC-0096 `:153-156` requires fresh confirmation
bound to locator and fingerprint for *every deletion*, and `thirty-day-cooling-and-retirement/spec.md:75-77`
forbids a prior review substituting for fresh confirmation — a rule `review`
honours by demanding a complete two-party attestation per call (`:750`).

Reach of a retained binding is already bounded by `resource` equality (`:466`),
the transition table (`:684`), and the compare-and-swap against persisted bytes
(`:540-544`), so it confers nothing beyond the one record the grant named.
The mechanism is over-broad on its own terms: issue digests are deterministic
over the grant payload (`close_work.py:464-470`), so popping invalidates a held
*binding object*, never a held *grant record* — a caller retaining the grant
re-mints the fact by calling `resolve_mutation_authority` again.

### Residual the adjudication did not examine: unbounded retention

Traced after round-2 security review, which framed the question as *what does
never-evicting cost?* rather than *may this actor act?*

- `_ISSUED_COORDINATION_AUTHORITIES` is a process-global dict declared at
  `close_work.py:46`.
- It is written on every successful `resolve_mutation_authority`
  (`close_work.py:470`), under a digest deterministic over the grant payload
  (`close_work.py:464-468`).
- It is popped **only** on the deletion path (`close_work.py:1780`, `:2017`).
  Nothing on the write path removes an entry.
- `_binding_is_issued` (`cooling.py:462-482`) iterates `authorities.values()`
  and calls `_mutation_binding` per entry; each call performs six
  `_bounded_text` normalisations that scan every character
  (`close_work.py:392-399`, `:487-494`) plus a regex match and two prefix checks.

So N distinct resolved grants make each subsequent lifecycle write O(N), and the
dict grows unbounded for the process lifetime. The growth is driven by the same
in-process trusted caller that mints the grants, so this is resource hygiene
rather than an authorization weakness — but bounded retention, not single-use,
is the repair the per-write scan makes load-bearing.

Orchestrator note: making the write grant single-use remains a defensible
hardening with Wave 4 precedent, and it would shrink the blast radius of a
leaked binding object from unlimited legal transitions to one. It is not a
defect against any shipped authority, so it is recorded here rather than
repaired. If the owner wants it, it is a new spec with its own AC.

## Finding 3 — SUSTAINED

`except (ZoneInfoNotFoundError, ValueError)` at `cooling.py:281`, repeated at
`:328` (`compute_review_on`) and `:339` (`is_due`), cannot catch `OSError`:
`OSError` is neither a `ValueError` nor a `KeyError` (the base of
`ZoneInfoNotFoundError`).

Measured on CPython 3.13.13 in this worktree:

    >>> ZoneInfo("a" * 256)
    OSError(63, 'File name too long')
    e.errno == 63
    e.filename == '<abs host path>/site-packages/tzdata/zoneinfo/aaaa...'
    type(e).__mro__ == (OSError, Exception, BaseException, object)

For contrast `ZoneInfo("Not/A/Zone")` raises `ZoneInfoNotFoundError` and
`ZoneInfo("/etc/passwd")` raises `ValueError` — both already handled.

No length bound exists before the call. The schema declares
`"maxLength": 255` (`contracts/jsonschema/delivery-lifecycle-record.schema.json:22`)
but the module runs no schema validator, so the declared bound is unenforced —
a schema/validator divergence with nothing checking it.

Reachable through the public untrusted-input seam: `parse_record_bytes` calls
`validate_payload` at `:308`, outside its own `try` at `:299-305`. Also through
`is_due` as called unguarded by `review` (`:752`) and `review_exception`
(`:802`), and through `update_record`'s unguarded `_write_record` (`:689`).
Only `load_record` is covered, because its `except` at `:658` lists `OSError`.

Breaks AC5 (`thirty-day-cooling-and-retirement/spec.md:138-141`): a `timezone` `ZoneInfo` cannot resolve must
return `unknown-timezone`. The sole shipped AC5 input is `"Not/AZone"`
(`tests/...:141`), which produces the already-handled shape.

The module has already fixed this exact escape class once: the `_exceeds_depth`
docstring (`:179-198`) records that "`RecursionError` is not a `ValueError`, so
it escaped every refusal path and surfaced as a traceback carrying an absolute
path."

Adjudicator's note on mechanism: enforcing `maxLength: 255` alone is not
sufficient — it would need duplicating at three call sites and would still leave
other `OSError` shapes from the same call uncaught. The `OSError` arm is
required; the bound is the defence-in-depth half that also closes the
schema/validator divergence.

---

# Post-GATES disposition audit

Three reviewers over two rounds returned 39 findings against the implementation.
The orchestrator dispositioned each, then an independent adjudicator audited the
**dispositions** rather than the findings — the useful question once every repair
is already in the tree.

**Result: 30 dispositions correct, 5 sustained against, 4 indeterminate. All five
sustained were documentation; no code disposition was wrong.**

## The five that were sustained, and what they were

1. and 3. The spec's Follow-ons register still cited pre-change line numbers.
   Three of seven anchors named a different function than the prose did.
2. `plan.md` cited eight `cooling.py` lines that had all drifted.
4. The `_close_work()` follow-on asserted that `enrol` wraps the dependency. It
   does not: `_resolve_destination` is called at `:692` and `enrol`'s `try` opens
   at `:695`. **A false statement about shipped code in a shipped document** —
   the adjudicator's reason for ordering this first.
5. `_resolve_destination`'s own `_close_work()` reach is a fifth uncaught path,
   and the register denied it while enumerating four.

All five are fixed. The citation pass ran last so no later edit re-staled it, and
most anchors are now symbol names rather than line numbers, because this is the
third time in one spec that line citations went stale under an insertion.

## Dispositions the audit confirmed

- **Declining `REFUSAL_CODES` enforcement in `CoolingResult.__post_init__`** is
  correct: `enrolled`, `accepted`, `identity-verified`, and `deletion-permitted`
  are all returned as `code` from the same dataclass and none is in the
  frozenset, so the check would reject four live success paths.
- **Deferring the `OSError` narrowing** is correct: an errno allow-list would
  leave AC6a green while re-raising, and a multi-byte key inside the code-point
  bound can still reach `OSError` on a byte-limited filesystem.
- **The changelog does not over-claim.** The disputed clause is governed by its
  own four-item enumeration and scoped to "malformed lifecycle-record input", and
  all four classes do return a code. The unqualified claim that did survive was
  the *spec's* Objective, which the audit caught and which is now narrowed to
  record input, naming the dependency-fault escape it does not cover.

## Where the audit was inconclusive

Four findings could not be settled read-only: two needed a git revision query for
the merge base, one named "four facts" without identifying them, and one had no
disposition recorded at all. That last one — the stale coverage figures — was in
fact applied; the omission was the orchestrator's bookkeeping, not a gap in the
work.

