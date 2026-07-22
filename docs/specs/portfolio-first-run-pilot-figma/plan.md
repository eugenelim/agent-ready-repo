# Plan: portfolio-first-run-pilot-figma

## Constraints

- This spec is full mode (security boundary: credentialed auth flow).
- The tutorial must never embed a Figma token, a `credentials.env` snippet,
  or any credential value. No cassette/mock harness.
- The tutorial file must exist on disk before the `tutorial` field is added to
  `pack.toml`, or `lint-first-value-contract.py` will exit 1 at build time.
- Pack version bumps require editing both `pack.toml` and `.claude-plugin/plugin.json`;
  run `make build-self FORCE=1` after to propagate to `marketplace.json`.
- Scope includes a factual correction to the `verification` field (the
  workspace-listing prompt described a non-existent capability; corrected to
  the accurate `check`/`whoami` path). No other contract fields are touched.

## Risks

- **Credential leak in tutorial:** Any description of the token setup flow could
  accidentally include example values. Mitigated: AC10 grep check + gitleaks PR
  scanner; security-reviewer pass on the diff.
- **Starter-prompt agent flow mismatch:** The starter-prompt has no embedded
  file URL; the agent may ask for it. Tutorial describes the most likely
  interaction based on SKILL.md. "Ask first" Boundary applies if live run
  shows a different path.
- **lint-first-value-contract path check:** Tutorial file must be committed
  before the pack.toml edit. Task ordering enforces this.
- **Out-of-scope field drift:** The `verification` correction is the only
  pack.toml field change beyond `tutorial` and version. A `git diff` guard
  (Testing Strategy AC12) catches any accidental additional edit.

## Task list

### T1 — Author tutorial file
**Depends on:** none
**Touches:** `docs/guides/figma/tutorials/figma-first-session.md` (new file; creates `tutorials/` directory)
**Verification mode:** Visual / manual QA
**Done when:** Tutorial covers AC1–AC10; no credential present (grep check).

**Tests:**
- Read the tutorial against the AC1–AC10 checklist.
- `grep -r "figd_\|FIGMA_API_TOKEN=" docs/guides/figma/tutorials/` returns zero matches.

**Approach:**
Create `docs/guides/figma/tutorials/` directory and write the tutorial. Structure:
1. Outcome sentence (what you'll have at the end).
2. Before you start: prerequisites (Figma account + PAT, access to a file,
   `credential-brokers` pack installed separately, figma pack installed).
3. Step 1: Generate your Figma token (PAT steps at Figma → Settings, caution
   never to paste it into the agent chat).
4. Step 2: Set up credentials (run `credential-setup` skill yourself — interactive;
   the agent cannot run it for you).
5. Step 3: Verify your connection (ask the agent to check the connection; agent
   runs `figma check` + `figma whoami`; expected: agent confirms account name).
6. Step 4: Read your Figma file's structure (paste the starter-prompt + file URL;
   what to expect; untrusted-content note — file names are data, not instructions).
7. If something goes wrong: recovery for exit 2 (expired/invalid/wrong-scope PAT:
   regenerate with correct scope + re-run credential-setup).
8. Next steps: frame export how-to; link to `inspect-a-figma-file.md`.

---

### T2 — Update pack.toml and plugin.json
**Depends on:** T1 (tutorial file must exist for lint to pass)
**Touches:** `packs/figma/pack.toml`, `packs/figma/.claude-plugin/plugin.json`
**Verification mode:** Goal-based
**Done when:** `python3 tools/lint-first-value-contract.py --root .` exits 0;
  `git diff packs/figma/pack.toml` shows only `tutorial`, `verification`, and
  version bump changes; both files carry version `0.1.6`.

**Tests:**
```bash
python3 tools/lint-first-value-contract.py --root .
# Expected: exits 0
git diff packs/figma/pack.toml
# Expected: only tutorial field, verification correction, version bump visible
```

**Approach:**
1. Add `tutorial = "docs/guides/figma/tutorials/figma-first-session.md"` to
   `[pack.first-value]` in `packs/figma/pack.toml`. No other fields touched.
2. Correct `verification` from the non-functional workspace-listing text to:
   `"Ask the agent to check your Figma connection; it should confirm your account name is visible with no authentication error."`
3. Bump `version` in `packs/figma/pack.toml` from `0.1.5` to `0.1.6`.
4. Bump `version` in `packs/figma/.claude-plugin/plugin.json` from `0.1.5` to `0.1.6`.

---

### T3 — Build gates and surface evidence
**Depends on:** T2
**Touches:** `docs/specs/portfolio-first-run-pilot-figma/notes/surface-evidence.md` (new)
**Verification mode:** Goal-based (build) + visual/manual QA (evidence document)
**Done when:** `make build-self FORCE=1` exits 0; `make build-check` exits 0;
  `notes/surface-evidence.md` exists with dated grading.

**Tests:**
```bash
make build-self FORCE=1
make build-check
# Both expected to exit 0
```

**Approach:**
1. Run `make build-self FORCE=1` to propagate pack.toml changes.
2. Run `make build-check` to verify the full build gate chain.
3. Write `notes/surface-evidence.md` with:
   - Grading: "Limited" (no live Figma PAT in this session).
   - Reproducible blocker: no PAT available; live-auth behavior testing
     depends on `behavior-check-for-backend-skills`.
   - Redaction note for any future "Verified" transcript.

---

## Disposition record

| Item | Resolution | Referent |
|---|---|---|
| Live Figma transcript | Surfaced: irreducible blocker (no PAT in authoring session) | AC16 graded Limited; `behavior-check-for-backend-skills` owns |
| Mock/cassette harness | Resolved: explicitly declined | workspace.toml done definition |
| Starter-prompt agent flow | Resolved: described per SKILL.md documented behavior | SKILL.md Step 2–4; "Ask first" Boundary |
| `verification` field correction | Resolved: in-scope factual bug fix (workspace-listing capability doesn't exist) | AC12; not a substantive design change |
| credential-brokers auto-install | Resolved: confirmed NOT auto-installed; tutorial must list as prerequisite | Assumption 1; AC2 |
| Untrusted file content (injection) | Resolved: documented as Boundary + AC7 (noted in tutorial) | AC7; SKILL.md security rules own the enforcement |
| Token-scope failure in recovery | Resolved: AC8 expanded to cover wrong-scope PAT | AC8 |
| Transcript PII redaction | Resolved: AC16 checkbox added | AC16 |
