# Verification ledger: registry comparison

Execution observations for `docs/specs/registry-comparison/`. The spec and plan stay pinned; this file records what the build found.

## T1 — the comparison tool

- **Bytecode check scope.** The AC-0014 prefix check ignores cache files whose mirrored path contains `/site-packages/`. The local gate venv lives at `.context/venv`, under the repository root, and its `_distutils_hack` `.pth` startup hook caches a file before any tool code runs. That write is the interpreter's, not the tool's. The control run that loads `closure_terminality.py` without the flag is still flagged on both the resolved and as-invoked roots.
- **Non-UTF-8 typed file.** AC-0010's non-UTF-8 case is tested through `classify`. A non-UTF-8 spec in a fixture tree makes the navigator itself refuse (`delivery_incomplete`), so the CLI reaches AC-0019's navigator refusal first.
- **Envelope item type.** The envelope check also refuses an item whose `type` is not `intent`, `brief`, or `spec`. That is a refusal (exit 2), so it fails closed.
- **Typed-file read bound.** A typed-file target is read with a 64 MiB cap. A larger file is `unclassified`.
- **Refusal input names.** `workspace.toml`, `navigator`, `graph`, `captured-items`, `arguments`, and `internal`.
