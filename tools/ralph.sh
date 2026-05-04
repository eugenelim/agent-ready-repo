#!/usr/bin/env bash
# Ralph — an AFK iterative loop around Claude Code.
#
# Each iteration is a FRESH Claude Code session. State lives in:
#   - the repo (git history)
#   - PROMPT.md (the task — keep it stable)
#   - .ralph/progress.txt (rolling notes Claude writes between iterations)
#   - AGENTS.md / per-package AGENTS.md (lessons learned)
#
# Termination: the loop exits when any of the following is true.
#   1. Gates pass AND the completion phrase appears in Claude's last output.
#   2. Iteration cap is hit.
#   3. Same gate failure two iterations in a row (loop detector).
#   4. SIGINT / SIGTERM (Ctrl-C is always honored).
#
# Read tools/RALPH.md before using this. It explains when Ralph is the right
# tool, when it isn't, and what the cost/safety rules are.

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────
MAX_ITERATIONS="${MAX_ITERATIONS:-20}"
COMPLETION_PHRASE="${COMPLETION_PHRASE:-RALPH_DONE}"
PROMPT_FILE="${PROMPT_FILE:-PROMPT.md}"
STATE_DIR=".ralph"
LOG_FILE="${STATE_DIR}/ralph.log"
LIVE_FILE="${STATE_DIR}/live.log"
PROGRESS_FILE="${STATE_DIR}/progress.txt"
LAST_OUTPUT_FILE="${STATE_DIR}/last-output.txt"

# Gates — override via env or .ralphrc.
LINT_CMD="${LINT_CMD:-}"
TEST_CMD="${TEST_CMD:-}"
TYPECHECK_CMD="${TYPECHECK_CMD:-}"

# ── Load project overrides ───────────────────────────────────────────────
if [[ -f .ralphrc ]]; then
  # shellcheck disable=SC1091
  source .ralphrc
fi

# ── Setup ────────────────────────────────────────────────────────────────
mkdir -p "$STATE_DIR"
: > "$LIVE_FILE"  # truncate live tail file each run

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "✖ $PROMPT_FILE missing. Create it before running Ralph." >&2
  echo "  See tools/RALPH.md for the PROMPT.md template." >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "✖ 'claude' CLI not found in PATH." >&2
  exit 1
fi

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG_FILE"; }

# ── Confirmation prompt (skip with --yes) ────────────────────────────────
yes_flag=0
for arg in "$@"; do
  [[ "$arg" == "--yes" || "$arg" == "-y" ]] && yes_flag=1
done

if (( ! yes_flag )); then
  cat <<EOF
You are about to start Ralph. Settings:

  MAX_ITERATIONS    = $MAX_ITERATIONS
  COMPLETION_PHRASE = $COMPLETION_PHRASE
  PROMPT_FILE       = $PROMPT_FILE
  LINT_CMD          = ${LINT_CMD:-<not set>}
  TYPECHECK_CMD     = ${TYPECHECK_CMD:-<not set>}
  TEST_CMD          = ${TEST_CMD:-<not set>}

Ralph will run unattended. It will commit changes. Each iteration spends API
credit. Ctrl-C exits between iterations.

Have you read tools/RALPH.md? Type 'yes' to continue:
EOF
  read -r answer
  [[ "$answer" == "yes" ]] || { echo "Aborted."; exit 1; }
fi

# ── Gate runner ──────────────────────────────────────────────────────────
# Returns 0 if all configured gates pass. Captures last failure for the loop
# detector.
LAST_GATE_FAILURE=""

run_gates() {
  local cmd_label cmd
  for pair in "lint:$LINT_CMD" "typecheck:$TYPECHECK_CMD" "test:$TEST_CMD"; do
    cmd_label="${pair%%:*}"
    cmd="${pair#*:}"
    [[ -z "$cmd" ]] && continue
    log "Gate: $cmd_label — $cmd"
    if ! eval "$cmd" >>"$LOG_FILE" 2>&1; then
      LAST_GATE_FAILURE="$cmd_label"
      log "Gate failed: $cmd_label"
      return 1
    fi
  done
  LAST_GATE_FAILURE=""
  return 0
}

# ── The loop ────────────────────────────────────────────────────────────
prev_failure=""
i=0
while (( i < MAX_ITERATIONS )); do
  i=$((i+1))
  log "════ Iteration $i / $MAX_ITERATIONS ════"

  # Build the per-iteration prompt: stable PROMPT.md + rolling progress.
  iter_prompt=$(cat "$PROMPT_FILE")
  if [[ -f "$PROGRESS_FILE" ]]; then
    iter_prompt+=$'\n\n--- PROGRESS NOTES (from previous iterations) ---\n'
    iter_prompt+=$(cat "$PROGRESS_FILE")
  fi
  iter_prompt+=$'\n\n--- COMPLETION ---\nWhen the task is fully complete and all gates pass, end your output with the line: '"$COMPLETION_PHRASE"

  # Run Claude. Each iteration is a fresh session — no --continue.
  if ! claude -p "$iter_prompt" --output-format text \
        > "$LAST_OUTPUT_FILE" 2> >(tee -a "$LIVE_FILE" >&2); then
    log "claude exited non-zero on iteration $i. Aborting."
    exit 2
  fi

  # Append iteration output to log (truncated).
  {
    echo "── iteration $i output (head) ──"
    head -200 "$LAST_OUTPUT_FILE"
    echo "── iteration $i output (tail) ──"
    tail -100 "$LAST_OUTPUT_FILE"
  } >> "$LOG_FILE"

  # Run gates after Claude's iteration.
  if run_gates; then
    # Gates green — check completion phrase.
    if grep -qF "$COMPLETION_PHRASE" "$LAST_OUTPUT_FILE"; then
      log "✓ Completion phrase found and gates green. Exiting clean."
      exit 0
    else
      log "Gates green but no completion phrase. Continuing — Claude says it's not done."
      prev_failure=""
    fi
  else
    # Gates failed — loop detector.
    if [[ "$LAST_GATE_FAILURE" == "$prev_failure" ]]; then
      log "✖ Same gate ($LAST_GATE_FAILURE) failed two iterations in a row. Aborting — Ralph is stuck."
      exit 3
    fi
    prev_failure="$LAST_GATE_FAILURE"
  fi
done

log "✖ Hit MAX_ITERATIONS ($MAX_ITERATIONS) without completion. Exiting."
exit 4
