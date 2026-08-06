# Suite parity, runner coverage, and fixture review

Evidence for AC5a, AC6 and AC6c of
[`../spec.md`](../spec.md). Filled in as each relocation task lands.

Environment: macOS, Python 3.13.13, pytest 9.0.3, node v26.4.0. Every optional
Python dependency the moving suites need is installed locally — `credbroker`,
`httpx`, `cryptography`, `argon2`, `pypdf`, `olefile`, `python-docx`,
`openpyxl`, `python-pptx`, `Pillow`, `docxtpl` — as is the Mermaid CLI (`mmdc`).
`npm install` was run in `packs/converters/.apm/skills/render-proof/` (126
packages; `node_modules/` is gitignored and not committed). **Every relocated
suite therefore has a real before/after run** — the plan had predicted the
JavaScript trio and the `mmdc`-dependent architect suite would be recorded
not-run, and neither turned out to be necessary.

Before-state for the JavaScript trio was measured by restoring the pre-move files
from `HEAD` into their original directory, running them there, and deleting the
copies — the moves had already landed when the dependencies were installed.

## 1 — Suite parity (AC6)

One row per relocated suite. Row shape follows the suite's kind: pytest modules
record `collected / passed`; the standalone harnesses — those carrying an
`if __name__ == "__main__":` entry point and invoked as `python <file>` — record
`exit code / assertions`; JavaScript suites record `exit code`.

| Suite | Kind | Before | After |
|---|---|---|---|
| `converters/file-to-markdown` (8 files) | pytest | 175 passed | 175 passed |
| `converters/markdown-to-docx/test_render.py` | pytest | 14 passed | 14 passed |
| `converters/markdown-to-pptx/test_render.py` | pytest | 11 passed | 11 passed |
| `converters/markdown-to-xlsx/test_render.py` | pytest | 14 passed | 14 passed |
| `converters/msg-to-markdown` (4 files) | pytest | 53 passed | 53 passed |
| `converters/render-proof/pipeline.test.js` | node | exit 0 | exit 0 |
| `converters/render-proof/renderer.test.js` | node | exit 0 | exit 0 |
| `converters/render-proof/security.test.js` | node | exit 0 | exit 0 |

## 2 — Runner coverage (AC6c)

One row per destination directory naming the runner that executes it, plus a
per-suite row for any suite that runner does not name. A row may name more than
one runner; a runner that cannot detect a total skip carries `(unprobed)`.
Permitted values: one or more runner names, `none (pre-existing)`, or
`deps absent in CI: <names>`.

| Destination directory or suite | Runner |
|---|---|
| `packs/converters/tests/skills/file-to-markdown/` | `build-check.yml` "pytest file-to-markdown extraction" (probed: `docx, openpyxl, pptx, PIL.Image`) — names 4 of its 8 suites |
| ↳ `test_rasterize_pdf.py` | none (pre-existing) |
| ↳ `test_split_image.py` | none (pre-existing) |
| ↳ `test_text_crosscheck.py` | none (pre-existing) |
| ↳ `test_tier3.py` | none (pre-existing) |
| `packs/converters/tests/skills/markdown-to-docx/` | `build-check.yml` "pytest markdown-to-docx renderer" |
| `packs/converters/tests/skills/markdown-to-pptx/` | `build-check.yml` "pytest markdown-to-pptx renderer" |
| `packs/converters/tests/skills/markdown-to-xlsx/` | `build-check.yml` "pytest markdown-to-xlsx renderer" |
| `packs/converters/tests/skills/msg-to-markdown/` | `build-check.yml` "pytest msg-to-markdown extraction" |
| `packs/converters/tests/skills/render-proof/` | none (pre-existing) — no workflow has ever run these; enabling them needs an `npm install` step and a lockfile, which is a scope decision, not a repoint |

## 3 — Fixture review (AC5a)

One line per fixture file or directory this change moves into the archived test
tree. Reviewed for credentials, secrets, and real personal data. Fabricated
addresses at registered domains are noted, not rewritten — that is the deferred
`test-fixture-domain-normalisation`.

| Fixture | Finding |
|---|---|
| `converters/msg-to-markdown/msg_fixtures.py` | No credential, secret, or real personal data — the corpus is generated in-process from fabricated names. Uses `corp.com` / `x.com`, registered domains rather than RFC 2606 reserved ones; not rewritten (deferred `test-fixture-domain-normalisation`) because the same strings are byte-compared against `testdata/msgreader_baseline.json`. |
| `converters/msg-to-markdown/testdata/msgreader_baseline.json` | Independent-reader oracle output. Same fabricated addresses; no secrets. Coupled to the file above. |
| `converters/msg-to-markdown/testdata/regen_msgreader_baseline.py` | Generator script; no data of its own. |
| `converters/render-proof/renderer.test.js` | XSS payloads target `evil.com`. Synthetic attack strings inside sanitizer assertions, not data — left as written. |
