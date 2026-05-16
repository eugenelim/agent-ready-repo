#!/usr/bin/env bash
# Session-start hook: prints the knowledge-base entries from
# docs/knowledge/patterns.jsonl as a context block. Agents read the
# block at session open so accumulated patterns / gotchas / antipatterns
# are in working memory before any work begins.
#
# Optional argument: --scope <path-or-glob>
#   When set, only entries whose stored `scope` glob *covers* the
#   given path are printed (e.g. --scope packages/auth/server.ts
#   returns entries scoped to packages/auth/**, packages/**, and the
#   repo-wide *). Without --scope, every entry is printed.
#
# Output goes to stdout; missing or empty knowledge file produces no
# output and exits 0. Malformed lines are skipped with a one-line
# warning to stderr (so the rot is visible) and do not abort the hook.
# Runtime: bash + python3 (already required by the artifact linters
# and check-done.py). Wiring lives in each tool's hook surface
# (Claude Code: .claude/settings.json; see tools/hooks/README.md).
#
# Fixture mode: set KNOWLEDGE_FILE=<path> to read a different file.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
KNOWLEDGE_FILE="${KNOWLEDGE_FILE:-$REPO_ROOT/docs/knowledge/patterns.jsonl}"

scope_filter=""
while (( $# > 0 )); do
  case "$1" in
    --scope)
      shift
      if [[ -z "${1:-}" || "${1:-}" == -* ]]; then
        echo "session-start.sh: --scope requires a path or glob value" >&2
        exit 2
      fi
      scope_filter="$1"
      ;;
    --help|-h)
      sed -n '2,22p' "$0"
      exit 0
      ;;
    *)
      echo "session-start.sh: unknown argument $1" >&2
      exit 2
      ;;
  esac
  shift || true
done

if [[ ! -f "$KNOWLEDGE_FILE" ]]; then
  exit 0
fi

if [[ ! -s "$KNOWLEDGE_FILE" ]]; then
  exit 0
fi

python3 - "$KNOWLEDGE_FILE" "$scope_filter" <<'PY'
import fnmatch
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
scope_filter = sys.argv[2] if len(sys.argv) > 2 else ""

entries = []
malformed = 0
for line_no, line in enumerate(path.read_text().splitlines(), start=1):
    if not line.strip():
        continue
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        malformed += 1
        continue
    if scope_filter:
        # The caller passed a path or narrower glob; only emit entries
        # whose stored scope *covers* it. Python's fnmatch is greedy
        # across `/` (a `*` matches path separators too), so a stored
        # `packages/auth/**` correctly matches a caller path like
        # `packages/auth/server.ts`. Literal `/` in the stored scope
        # still acts as the package boundary — caller
        # `packages/auth-other/x.ts` does NOT match stored
        # `packages/auth/**` because the prefix doesn't line up.
        scope = entry.get("scope", "")
        if not fnmatch.fnmatch(scope_filter, scope):
            continue
    entries.append(entry)

if malformed:
    print(
        f"session-start: skipped {malformed} malformed line(s) — "
        f"run tools/lint-knowledge.sh",
        file=sys.stderr,
    )

if not entries:
    sys.exit(0)

print("=== knowledge ===")
for e in entries:
    print(f"[{e.get('id', '?')}] ({e.get('kind', '?')}, {e.get('scope', '?')}) "
          f"{e.get('title', '')}")
    body = e.get("body", "").strip()
    if body:
        for ln in body.splitlines():
            print(f"    {ln}")
    source = e.get("source", "")
    if source:
        print(f"    — {source}")
    print()
PY
