# Credential detector contract for legacy migration

This note is the stable AC7 contract for the minimum detector that runs before
an exact legacy TOML slice may enter `.workspace-migrations.json`.

## Input and normalization

- Scan only the exact raw UTF-8 legacy slice selected for the operation.
- Do not normalize Unicode, case, whitespace, or line endings before scanning.
- Apply the first three patterns case-insensitively; apply the remaining
  patterns exactly as written.

## Required pattern classes

- `\b(password|passwd|pwd|secret|client_secret|api_key|apikey|access_token|refresh_token|auth_token|bearer|private_key)\b\s*[:=]\s*[^\s#]+`
- `\bauthorization\s*[:=]\s*(basic|bearer)\s+\S+`
- `[?&](access_token|api_key|private_token|auth|token)=[^&#\s]+`
- `-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----`
- `gh[pousr]_[A-Za-z0-9_]{20,}`
- `xox[baprs]-[A-Za-z0-9-]{10,}`
- `(?:AKIA|ASIA)[A-Z0-9]{16}`

## Result policy

Any match, including a false positive, returns only
`sensitive_legacy_content`, performs no durable write, and requires the human to
sanitize the legacy source before replanning. There is no inline override. The
matcher never returns or logs the pattern, matching span, line, or source text.
A non-match still requires the selection's slice-digest-bound
`legacy_content_approved_for_ledger = true` privacy attestation.
