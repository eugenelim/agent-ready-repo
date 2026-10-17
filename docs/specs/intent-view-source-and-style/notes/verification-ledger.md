# Verification ledger: intent view source parts and refined style

## Base commit

- Base commit: `f07d39b534b32a8b71c0f1572d1567f72ca76104`, the merge-base of `eugenelim/navigate-decisions` with `origin/main` on 2026-10-16. Every criterion and proof that names the base commit uses this id.

## Transformation proof (T1)

The joined script is byte-identical to the base commit's `view.js` with lines 2-10 moved to follow line 11. Base commit: `f07d39b534b32a8b71c0f1572d1567f72ca76104`. Run before `view_assets/view.js` was deleted.

Command (the joined script is the builder's prologue, the 14 parts in the builder's part list order, and the epilogue, written to `/tmp/t1_joined.js`):

```
git show f07d39b534b32a8b71c0f1572d1567f72ca76104:packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.js > /tmp/t1_base.js
{ sed -n '1p' /tmp/t1_base.js; sed -n '11p' /tmp/t1_base.js; sed -n '2,10p' /tmp/t1_base.js; sed -n '12,$p' /tmp/t1_base.js; } > /tmp/t1_expected.js
cmp /tmp/t1_joined.js /tmp/t1_expected.js
```

Result: `cmp` printed nothing and exited 0 (identical). The working-tree `view_assets/view.js` also `cmp`-equalled the base file before deletion.

Largest part: `list-bodies.js`, 310 lines (limit 400). The parts total 1705 lines, which is the base file's 1708 less the 3 prologue and epilogue lines.

SHA-256 of each part:

| Part | SHA-256 |
| --- | --- |
| `escape.js` | `b85d3aeb8f8d732a59547e97f21e93100a0a455b182c71eeb730d38372e0e9d1` |
| `labels.js` | `32f6309a25b791dd20639ff0f65066d858b438ba4fc64528a0889b02ada08bc7` |
| `utilities.js` | `fb122d46c885d02f11823b571ea2c06b8d6ad3e0c7259e61538d51635973ab34` |
| `data.js` | `d7dd712308bf8c2d3a220a032f97147a24b3444e1db95d23d78cb4e8dba1f496` |
| `lists.js` | `0043fbb2e113d249e62d24095a93139ae526ab60174f36b48acd87d6849641d3` |
| `routing.js` | `cee6a0454e74d45dd90e12a4d0718389d295e396436fc24e676e9c89dba9802c` |
| `small-parts.js` | `8052383bf679535cc3738631d35f6a65d4f70c28e991d4257c0dcfa27ec1ca26` |
| `rows.js` | `7ac319eec898556bd32ecdda3ff4394b18d7a969d1ca6724a41af8a8e2f98aa7` |
| `list-bodies.js` | `fa8097b759b592fd7deeed67ab35c710679ed107e702acc92052c49ac9318c85` |
| `detail.js` | `32ce1a75d9b0848e7cdfb5346d1a320bec52727eaf2852867ea7b76d3a6bb673` |
| `dependencies.js` | `9d6e2beb378739a387eb62769cd185c137b9f81e73eddf8a8effb0b8421a4379` |
| `detail-parts.js` | `7ee32743b999db90ad3f21d6ebaab23073d9329b40f4717e37c77e3ee2c3dfee` |
| `detail-render.js` | `fb2f58b385c10aa059147a9b5e324b5f2663d6f35f8a8e797c1ab15b9c9d7623` |
| `chrome.js` | `d6d0fa91fb476d76daa4f33f42e81ccf51f708e9fa855404e6f70b48f5d3e87f` |

## Dispatch notes

- T1 was implemented by an `implementer` subagent and verified by the controller: `test_export_html.py` 16 passed in 7.8s; `make lint-ruff lint-mypy` clean; the implementer's full run of `packs/core/tests/skills/navigate-intents` was 507 passed, 4 skipped.
- T2 was written by the controller, not an implementer, because its records carry the owner's 2026-10-16 decisions and the owner's Approver signature on the RFC-0108 errata. The receipt vocabulary offers only `no-implementer-installed` and `human-directed`; it is recorded as `human-directed`, the closer of the two. Checks: `tools/validate_guides.py` exit 0; `lint-spec-status.py --root .` clean; `workspace.toml` parses.
