# Tier 3 — managed-API OCR (the egress boundary)

Tier 3 sends a document to an **adopter-approved managed OCR / extraction
vendor**. It is the one tier that crosses a **data-egress boundary**, so it is
gated harder than any other: **off by default, explicit-only, and never reached
by automatic degradation or upgrade.** Configuring a vendor does not select it —
only an explicit `--tier3` invocation does.

**This skill makes no network call.** It ships no HTTP client, no vendor SDK, and
no socket. Tier 3 here is an *interface*: you run the vendor through **your own
provisioned transport** (its SDK / CLI / an MCP server / a curl in your harness),
save the returned OCR text to a file, and hand that file plus an **egress
declaration** to the skill, which validates the declaration, stamps the unified
contract, and records the destination in provenance. The actual bytes-on-the-wire
never leave through this skill.

```bash
# You run the vendor yourself and save its OCR text, then:
python scripts/convert.py --tier3 \
  --ocr-text vendor_output.txt \
  --endpoint ocr.your-approved-vendor.example \
  --residency eu-west-1 \
  "source-document.pdf"
```

Output: `<source-stem>.md` next to the OCR-text file, carrying
`tier: "3-managed-api"`, a fixed `extraction-confidence: "low"`, and
`requires-review: true` — because the skill neither performed nor verified the
vendor's read, it never claims `high` for output it did not produce. When the
`--source` name has no usable suffix the `content-type` falls back to the sentinel
`managed-ocr`.

## The egress declaration

Enabling Tier 3 requires a declaration whose key set is **exactly** two keys:

| Key | Meaning |
|---|---|
| `endpoint-allowlist` | the vendor host(s) egress is permitted to — a non-empty list |
| `residency-region` | the data-residency / region the vendor processes in |

The validator refuses (fail-closed — **no output is stamped**) on: a missing or
non-mapping declaration; **any unknown field** (the key set must equal exactly the
two keys above — no auth material, tokens, or credentials are ever accepted here);
an empty endpoint list; a wildcard / scheme-less catch-all (`*`, `.`, empty,
`0.0.0.0`, `::`); a CIDR; a loopback / link-local / private / metadata IP (IPv4,
IPv6, and IPv4-mapped IPv6 alike); a metadata/loopback hostname (`localhost`,
`metadata.google.internal`, `*.internal`, …); or an empty residency.

> **The endpoint validation is a footgun-reducer, not the egress control.** The
> skill opens no socket and never resolves a hostname, so a hostname that
> *resolves* to an internal address still passes the string check. The real
> "egress only to the named destination" guarantee is the transport-binding
> obligation below — the string checks only stop the obvious mistake.

## Adopter controls you must record and configure

The skill ships the *doctrine*; you own the controls a transport-free skill
cannot enforce at the socket. Before routing anything to Tier 3:

1. **Vendor data-retention & no-training-on-input.** Verify and **record** the
   vendor's data-retention window and its no-training-on-your-input terms as part
   of "vendor approval." The pack never ships any vendor's terms as fact — you
   establish and record them for your environment.

2. **Transport-binding — egress only to the declared destination.** Configure
   **your transport** (egress proxy / firewall / SDK endpoint config) so it can
   egress **only** to the declared `endpoint-allowlist` and **only** in the
   declared `residency-region`. This is the adopter-side control that carries the
   governing RFC's "egress occurs only to the named destination" requirement,
   which this transport-free skill cannot enforce at the socket. The declaration
   is echoed into the output's provenance so the intended destination is
   auditable against what your transport actually allowed.

3. **Redaction is your document-classification responsibility.** Documents are
   sent to the vendor **unmodified** — the skill builds **no pre-egress redaction
   or PII-scrubbing hook** (redaction is out of scope for this tier). Gate what is
   allowed to reach a managed vendor at **your** classification layer, before you
   invoke the vendor.

## No bundled vendor, model, or data

No managed-OCR endpoint, vendor SDK, per-vendor config, or per-vendor knowledge
base ships with this pack. The pack ships the tier **interface** and this
doctrine; you supply the approved vendor and its transport.
