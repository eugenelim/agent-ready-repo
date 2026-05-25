# jira-defect-flow — canonical examples

Three end-to-end shapes you'll see most often. Replace `PROJ-123` etc.
with the values from your environment.

## Notation

These examples reference sibling skills **by name**, never by path. A
line like `jira: get-issue PROJ-123` means *invoke the skill registered
under the name `jira` with subcommand `get-issue` and the given args*.
How that dispatch happens depends on the IDE:

- **Claude Code**: the Skill tool, or `/jira get-issue PROJ-123` (and
  similarly for `bug-fix`).
- **Cursor / Kiro / Codex**: the IDE's skill/rule invocation
  equivalent.
- **Raw CLI** (no IDE): `cd` to the skill's install dir and run
  `python scripts/jira.py get-issue PROJ-123`. Where that dir lives
  depends on where the user installed the skill.

Path locations like `~/.claude/skills/jira/...` are install-time
details, not contract.

---

## 1. Full happy path

User: *"Take PROJ-123 from triage to PR on dev."*

```
# Stage 1 — intake
jira: check
jira: get-issue PROJ-123 --expand renderedFields,attachments,changelog,transitions

# (agent reads env / repro / expected-vs-actual — all present)

# Stage 2 — triage + start
# (agent writes .context/defects/PROJ-123.md with severity, class, suspects)
# (user confirms start)
jira: list-transitions PROJ-123
jira: transition PROJ-123 --to "In Progress"

# Stage 3 — hand to bug-fix skill
bug-fix: take PROJ-123 with the triage brief at .context/defects/PROJ-123.md
# bug-fix writes failing test, identifies root cause, applies minimum fix

# Stage 4 — branch (local script, lives in this skill — relative path is fine)
BRANCH=$(python scripts/branch_name.py PROJ-123 \
  "Null pointer in cart checkout when coupon expired")
git checkout -b "$BRANCH"
# -> fix/proj-123-null-pointer-in-cart-checkout-when

# Stage 5 — review (in consumer repo's work-loop)
# (adversarial-reviewer + security-reviewer return Clean — ready to commit)

# Stage 6 — PR
gh pr create --base main \
  --title "fix(checkout): null-pointer on expired coupon (PROJ-123)" \
  --body-file .context/defects/PROJ-123-pr-body.md
# PR body's Why? section contains: Closes: PROJ-123

# Stage 7 — Jira loopback (bug-fix step 8 mechanism)
jira: comment PROJ-123 --body "PR: https://github.com/acme/web/pull/4321. Repro test: tests/checkout/coupon_expiry_test.py::test_expired_coupon_does_not_crash"
jira: transition PROJ-123 --to "In Review"

# Stage 8 — dev deploy (only because DEPLOY_DEV_CMD is set)
"$DEPLOY_DEV_CMD"
jira: comment PROJ-123 --body "Deployed to dev: https://dev.acme.example/checkout. Ready for QA."
jira: transition PROJ-123 --to "Ready for QA"
```

Note: `scripts/branch_name.py` lives **inside this skill**, so a
relative path is correct there — it's not a cross-skill reference.

---

## 2. Intake blocked by missing info

User: *"Fix PROJ-456."*

```
jira: get-issue PROJ-456 --expand renderedFields,attachments,changelog
```

Agent reads the ticket — description is one line: *"Search is broken,
please fix."* No environment, no repro, no expected-vs-actual.

**Do not proceed.** Comment and stop:

```
jira: comment PROJ-456 --body "Before picking this up I need: (1) environment — which deployment / build, on which browser; (2) reproduction steps — what query did you run; (3) expected vs actual behavior — what should have happened vs what did. Once those are in I'll start."
```

No branch created, no transition applied. Surface to the user that the
ticket was blocked back to the reporter.

---

## 3. No deploy hook (stops at PR-merged)

User: *"Ship the fix for PROJ-789 to dev."*

All stages 1–7 run normally. At stage 8:

```bash
[ -n "$DEPLOY_DEV_CMD" ] && echo "have env hook" || echo "no env hook"
# -> no env hook
[ -x .context/deploy_dev.sh ] && echo "have file hook" || echo "no file hook"
# -> no file hook
```

Stop. Tell the user:

> The PR for PROJ-789 is open and Jira is moved to *In Review*. I don't
> see a `DEPLOY_DEV_CMD` env var or a `.context/deploy_dev.sh` script in
> this repo, so I won't guess at a deploy command. How is dev deployed
> here? Once I know, I can add a `.context/deploy_dev.sh` so the next
> run of this skill can do it automatically.

Do not run `gh workflow run`, `kubectl apply`, or any deploy-shaped
command on speculation.
