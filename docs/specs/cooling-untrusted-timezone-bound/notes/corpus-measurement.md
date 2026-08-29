# Measured: what the shipped validator actually does with malformed input

A 32-case malformed corpus was run against both public untrusted-input seams —
`validate_payload` and `parse_record_bytes` — on the shipped module at merge base
`8fc40040`, CPython 3.13.13, darwin/APFS. 64 seam-cases total.

**12 of 64 raise an uncaught exception. The other 52 refuse correctly with a
published code.**

This is the evidence the acceptance criteria are built on. It replaces two
reviewers' partially-correct reasoning with one measurement.

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
shows it is **four** shapes: every envelope that carries `evidence_ref` and omits
any one of the three required keys. The published contract rejects all four
cleanly (`$defs/exception` `required: ["reason", "owner_role", "review_on"]`).

The correct predicate is a superset test — reject when the required set is not
fully present — which is what the neighbouring `validate_payload` already does
at `cooling.py:240` (`not set(payload) >= _REQUIRED`).

## The 26 cases that already refuse correctly

No further defect class was found. These all return a published refusal code
from both seams:

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
255 **bytes**, so the same key is over the limit there. JSON Schema `maxLength`
and Python `len()` both count code points.

Consequence for the design: `MAX_TIMEZONE_LENGTH = 255` eliminates
`ENAMETOOLONG` for the whole schema-valid space on darwin, but **not** on a
byte-limited filesystem, where a multi-byte key inside the published bound can
still exceed `NAME_MAX`. The `OSError` arm — not the bound — is the control for
that residue, and it is why the arm must exist at all three seams rather than
only where the bound happens to fire.
