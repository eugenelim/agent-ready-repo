# injection — untrusted input into an interpreter or deserializer

> **Loaded when:** the change builds SQL, shell/OS commands, LDAP filters,
> template strings, HTML, or NoSQL queries from input, **or** deserializes
> untrusted data.
> **Standards:** OWASP Top 10:2025 A05 (Injection) + A08 (Software & Data
> Integrity — unsafe deserialization) · ASVS 5.0 V5 (Validation, Sanitization
> & Encoding) · CWE Top 25 (CWE-89 SQLi, CWE-78 OS command, CWE-79 XSS,
> CWE-502 deserialization).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is "parameterize at the boundary, encode at the
sink" — the spec should commit to parameterized queries / safe loaders rather
than leaving sanitization to be retrofitted. Where a feature accepts a
structured payload, name the expected schema as a criterion (ASVS 5.0 V5;
Proactive Controls 2024 C3 Validate-all-Inputs / C4 Encode-and-Escape).

## Implementation checks

- `hybrid` **SQL / NoSQL.** Taint analysis finds input reaching a query; you
  judge whether it is *parameterized* (`$1`, bound params) versus
  string-concatenated. Flag any `fmt.Sprintf`/f-string/`+` building a query
  with input.
- `hybrid` **OS command / shell.** Prefer argument-vector exec over a shell
  string; flag `shell=True`-equivalent with interpolated input. Scanner finds
  the call; you judge whether the input is constrained.
- `hybrid` **Template / SSTI & HTML / XSS.** Output into HTML or a template
  engine must be contextually escaped; flag autoescape disabled or `raw`/
  `dangerouslySetInnerHTML` over untrusted content.
- `reason` **Unsafe deserialization (A08).** `pickle`, Java native
  serialization, `yaml.load` (vs `safe_load`), PHP `unserialize` on untrusted
  bytes is remote code execution. Confirm a safe loader or a signed/typed
  format. This is reviewer-only judgment — a scanner may not know the source
  is untrusted.
- `tool` **Known-vulnerable parser/driver.** If the injection risk is a
  CVE in the query driver or parser, that is SCA's job — confirm `pip-audit` /
  `npm audit` / `govulncheck` is wired; if no scanner is detected, flag
  `degraded: no scanner` rather than asserting the dependency is clean.

## Established-helper bypass

Resolve the repo's sanctioned query builder / ORM, its output-encoding helper,
and its safe-deserialization wrapper. Flag code that drops to raw string
concatenation or a raw `eval`/`load` when the blessed parameterizing or
safe-loading path exists.
