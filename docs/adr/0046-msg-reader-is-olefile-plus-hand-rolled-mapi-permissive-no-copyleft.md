# ADR-0046: The `.msg` reader is `olefile` + hand-rolled MAPI parsing — permissive, no copyleft, no Python-2-broken dependency

- **Status:** Accepted
- **Date:** 2026-07-01
- **Decision-makers:** eugenelim
- **Related:** [RFC-0058](../rfc/0058-capability-tiered-document-extraction.md) (capability-tiered extraction, Open-Q2: `msg-to-markdown` adopts the unified contract); [ADR-0045](0045-capability-tiered-document-extraction.md) (names "the shared output contract `msg-to-markdown` adopts"); [ADR-0034](0034-infra-grounding-toolchain-oracle-doctrine-not-tooling-vendor-data-or-agent.md) (ship no bundled per-vendor data / models — the `.msg` reader stays pip-on-demand); [RFC-0007](../rfc/0007-user-scope-converter-pack.md) (the user-scope `converters` pack); [spec `extraction-msg-to-markdown-python-contract`](../specs/extraction-msg-to-markdown-python-contract/spec.md) (the Python-port slice this dependency serves)

## Decision summary

- **Decision:** The Python port of `msg-to-markdown` reads Outlook `.msg` files with **`olefile`** (BSD-2-Clause, pip-on-demand, pinned `>=0.47`) for OLE2/CFBF container access, plus **first-party hand-rolled MAPI-property decoding** in the skill. It replaces the Node runtime and the `@nicecode/msg-reader` / `msgreader` npm packages.
- **Because:** it is the only permissive, pure-Python, Python-3-correct option. The stated-default `msg-parser` is Python-2-broken; `extract-msg` is GPL (copyleft); `olefile` is the maintained BSD container reader and hand-rolling the (small, well-documented) MAPI property layer on top of it is more robust than depending on a stale wrapper.
- **Applies to:** the `converters` pack's `msg-to-markdown` skill only.
- **Tradeoff accepted:** the MAPI/CFBF/RTF parsing is now first-party untrusted-input code (its resource-bounding + malformed-input robustness are the skill's responsibility — spec AC9/AC10), and `olefile` is pip-on-demand, so it is invisible to the repo's SCA (accepted risk, compensating control below).
- **Revisit if:** a permissive, maintained, Python-3-correct `.msg` *library* reaches the ecosystem (collapsing the hand-rolled layer), or `olefile` is abandoned / yanked / ships a new major (re-review trigger).

## Context

The pre-existing `msg-to-markdown` was a Node.js skill: `scripts/convert.js` +
`scripts/extract-attachments.js`, reading `.msg` through `@nicecode/msg-reader`
(preferred) or `msgreader` (fallback). RFC-0058 (Open-Q2) directs the skill to
adopt the unified Tier-0 output contract that `file-to-markdown` emits, which
requires re-hosting the skill on Python so it can share the contract builder.
That makes the `.msg` reader a **new Python dependency** — and the `converters`
pack has no `AGENTS.md`, so per `AGENTS.md § Check before acting` a new dependency
is recorded in an ADR. The pack license is `Apache-2.0 OR MIT`; a prior decision
already rejected copyleft (AGPL) dependencies for this pack.

Two findings surfaced at EXECUTE-time grounding (2026-07-01) reshaped the choice:

1. **`msg-parser` (1.2.0, the stated default) is Python-3-broken.** Its
   `DataModel` is Python-2-only: `PtypInteger32` does
   `int(data_value.encode("hex"), 32)` (`bytes` has no `.encode`), and the
   boolean/time decoders do `data_value[0]` unpack expecting a 1-char `str`.
   Every real `.msg` carries integer properties (Importance `0x0017`,
   RecipientType `0x0C15`, AttachMethod `0x3705`), so `msg-parser` raises
   `AttributeError` on the first one — it cannot parse a real message on
   Python 3. Its last release was December 2019.
2. **`@nicecode/msg-reader` does not exist on npm** (404). The shipped Node skill's
   "preferred" reader was never installable; only the `msgreader` fallback ever
   worked. This weakens any "match the current reader" argument.

## Decision

Read `.msg` with **`olefile`** for the OLE2/CFBF container and **hand-roll the
MAPI property layer** (`scripts/mapi.py`) in the skill:

- `olefile` (BSD-2-Clause, actively maintained, 0.47, pure-Python, no Windows
  dependency) opens the compound file and exposes named streams.
- The skill reads the `__substg1.0_<id><type>` property streams it needs directly
  and decodes them itself: PtypString (`001F`, UTF-16LE), PtypString8 (`001E`,
  codepage), integers (`0003`), FILETIME (`0040`), binary (`0102`/`000D`). This
  is a small, MS-OXPROPS/MS-OXMSG-documented surface, and owning it means reliable
  `RecipientType` (so recipients are classified by kind — to/cc/bcc, incl. BCC — which
  the Node reader does not do) and no dependence on a stale wrapper's bugs.

Rejected alternatives:

- **`msg-parser`** — Python-3-broken (above); depending on it would require
  monkey-patching its `DataModel`, i.e. re-implementing the decode layer anyway.
- **`extract-msg`** — GPL (copyleft); fails the pack's `Apache-2.0 OR MIT` bar.
  Excluded on license regardless of technical merit.
- **A bundled/vendored `.msg` library** — violates ADR-0034 (no bundled
  per-vendor data); the reader stays pip-on-demand.

## Consequences

- **Pip-on-demand, `--check` gated.** `olefile` is resolved on demand via the
  skill's `--check` verb (exit 0 present / 2 absent) whose `PIP_INSTALL` hint pins
  `olefile>=0.47`; it is never auto-installed. This mirrors `file-to-markdown`'s
  optional-library pattern.
- **First-party untrusted-input parsing.** Because the MAPI/CFBF/RTF handling is
  now the skill's own code, resource-bounding and malformed-input robustness are
  the skill's responsibility (spec AC9/AC10): bounded per-stream reads that distrust
  the CFBF-declared size, an OLE2 stream/storage-count cap checked before
  materialization, a cumulative-output budget threaded through the embedded-message
  recursion, non-raising decode (`errors="replace"`), and **no LZFu decompressor**
  (RTF-only degrades to a surfaced note after reading — but not expanding — the LZFu
  header's declared raw-size). This is the same untrusted-input discipline the
  vendored `safe_io.py` embodies for zips, re-derived for OLE2 (whose zip-bomb
  guards do not apply).
- **SCA-invisibility (accepted risk + compensating control).** As a pip-on-demand
  dependency in the *user's* environment, `olefile` is outside the repo lockfile and
  its SCA/Dependabot scanning. The AC10 resource wrap is the load-bearing
  compensating control **for resource exhaustion only** — it does **not** compensate
  for malicious code in a future `olefile` release. Because the `--check` hint pins a
  *minimum* version, an unreviewed future release can resolve on the user's machine;
  the **re-review trigger** is a new `olefile` major version or a yanked release,
  at which point the pin is re-evaluated.
- **Abandonment exit.** If `olefile` itself is later abandoned, the container-access
  surface it provides (CFBF sector/FAT/MiniFAT walking) is itself documented and
  hand-rollable; the exit is to vendor or re-implement that thin layer, keeping the
  MAPI decode already owned by the skill.
- **Testing.** No permissive `.msg` *writer* exists on PyPI, so fixtures are
  generated by a committed pure-Python CFBF writer and cross-checked by the Node
  `msgreader` package (the independent-reader oracle); the absolute-fidelity
  real-world sample is deferred (backlog: `extraction-msg-realworld-sample`).
