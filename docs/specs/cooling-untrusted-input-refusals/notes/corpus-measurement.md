# Measured: what the shipped validator actually does with malformed input

A 32-case malformed corpus was run against both public untrusted-input seams —
`validate_payload` and `parse_record_bytes` — on the shipped module at merge base
`8fc40040`, CPython 3.13.13, darwin/APFS. 64 seam-cases total.

**12 of 64 raise an uncaught exception. The other 52 refuse correctly with a
published code.**

Two corrections to that headline, both found by round-2 review and confirmed
before being written down:

1. **The scope is two seams, not the module.** `validate_payload` and
   `parse_record_bytes` are the two public entry points sampled here. The
   caller-facing `review()` and `review_exception()` were not, and defect B below
   reaches both — 20 of 80 seam-cases once they are counted. Nothing in this
   note supports a whole-module claim.
2. **Defect A's count is environment-contingent.** With the optional `tzdata`
   wheel blocked, the two timezone rows refuse cleanly and the figure is 8 of 64.
   Defect B's count is not contingent — it is plain dict access.

## The 12 failures

| Case | `timezone` / `exception` value | Both seams raise |
| --- | --- | --- |
| `tz-256` | `"a" * 256` | `OSError: [Errno 63] File name too long: <absolute host path>` |
| `tz-multibyte-300` | `"é" * 300` | `OSError: [Errno 63] File name too long: <absolute host path>` |
| `exc-no-review_on` | `{reason, owner_role, evidence_ref}` | `KeyError: 'review_on'` |
| `exc-no-owner_role` | `{reason, review_on, evidence_ref}` | `KeyError: 'owner_role'` |
| `exc-no-reason` | `{owner_role, review_on, evidence_ref}` | `KeyError: 'reason'` |
| `exc-only-evidence` | `{evidence_ref}` | `KeyError: 'reason'` |

Two distinct defects, both the same class: a hand-written validator weaker than
the published contract, failing by exception rather than by refusal code.

### Defect A — the timezone lookup

`except (ZoneInfoNotFoundError, ValueError)` at `cooling.py:281`, `:328`, `:339`
cannot catch `OSError`. This is the sustained Wave 5 finding.

### Defect B — the exception envelope

`_exception_is_valid` (`cooling.py:214-232`) gates on

```python
if set(value) < {"reason", "owner_role", "review_on"}:
    return False
```

`<` is a **proper subset** test. Any envelope carrying `evidence_ref` is not a
subset of the required three, so the test is false and execution falls through to
`value["reason"]`, `value["owner_role"]`, and `value["review_on"]` — raising
`KeyError` for whichever required key is absent.

Found by the security reviewer on one shape (`exc-no-review_on`). The corpus
showed four. Full enumeration later showed **seven**: of the sixteen envelope
shapes, eight carry `evidence_ref` and so fall through the old gate, and seven of
those omit a required key. The corpus under-counted because it sampled shapes
rather than enumerating them — the same mistake, one level down, that made it
miss the membership-test class entirely. The published contract rejects all seven
cleanly (`$defs/exception` `required: ["reason", "owner_role", "review_on"]`).

The correct predicate is a superset test — reject when the required set is not
fully present — which is what the neighbouring `validate_payload` already does
at `cooling.py:240` (`not set(payload) >= _REQUIRED`).

## The 26 cases that already refuse correctly

No further defect class was found **in this two-seam sample**. That is a
statement about what was measured, not about the module. Round-2 review
subsequently found two more residuals by reading rather than by corpus — the
`delivery_id` `str()` coercion at `cooling.py:246` and the unwrapped
`_close_work()` resolution at `:345`/`:390`/`:520`/`:689` — both recorded as
spec follow-ons.

A later pass found one more class the corpus missed: a **container** where a
scalar belongs. Every case below used a scalar for the enum fields, so none
tripped `value in {set of strings}`, which raises `TypeError` for an unhashable
list or dict. AC23 to AC29 now enumerate that space instead of sampling it, across three
further classes review found by asking the same question: containers where a
scalar belongs, `str()` coercion of unbounded numbers, and duck-typed candidate
elements.

These all return a published refusal code from both sampled seams:

`tz-int`, `tz-none`, `tz-list`, `tz-empty`, `exc-empty`, `exc-notadict`,
`loc-1001`, `loc-empty`, `loc-abs`, `loc-dotdot`, `loc-int`, `aliases-17`,
`aliases-str`, `aliases-int-item`, `id-empty`, `fp-bad`, `auth-empty`,
`auth-write-str`, `auth-notadict`, `date-bad`, `review_on-int`, `evref-bad`,
`proof-none`, `disp-unknown`, `result-int`, `schema-wrong`.

Note `tz-int`, `tz-none`, and `tz-list` pass **only** because
`validate_payload:280` currently coerces with `str(payload["timezone"])`. Removing
that coercion without a type guard would raise `TypeError` — measured:
`ZoneInfo(123)`, `ZoneInfo(b"UTC")`, `ZoneInfo(None)`, and `ZoneInfo(["UTC"])` all
raise `TypeError`, which is in none of the three `except` tuples. That is why the
type guard needs its own criterion rather than being a design note.

## Code points versus bytes

Measured on darwin/APFS:

| Key | Characters | UTF-8 bytes | Result |
| --- | --- | --- | --- |
| `"a" * 256` | 256 | 256 | `OSError(ENAMETOOLONG)` |
| `"é" * 200` | 200 | 400 | `ZoneInfoNotFoundError` |
| `"é" * 300` | 300 | 600 | `OSError(ENAMETOOLONG)` |

APFS bounds the component at 255 **code points**, so the 400-byte / 200-character
key is inside the limit and resolves normally to "not found". ext4 bounds it at
255 **bytes**, so the same key is over the limit there — inferred from
`NAME_MAX` semantics, not measured on ext4, and contingent on `tzdata` being
importable exactly as the ASCII rows are. JSON Schema `maxLength`
and Python `len()` both count code points.

Consequence for the design: `MAX_TIMEZONE_LENGTH = 255` eliminates
`ENAMETOOLONG` for the whole schema-valid space on darwin, but **not** on a
byte-limited filesystem, where a multi-byte key inside the published bound can
still exceed `NAME_MAX`. The `OSError` arm — not the bound — is the control for
that residue, and it is why the arm must exist at all three seams rather than
only where the bound happens to fire.
