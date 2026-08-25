# Assessment output layout

Saving is optional. First select the artifact role:

- `current-architecture` for a canonical model/report of the implemented system;
- `architecture-design` for remediation or future change;
- no durable role yet for mixed output until the user chooses where it belongs.

Then name exactly one operating mode:

1. **`chat-only`** — no destination and no write.
2. **`personal-workspace`** — an exact user-confirmed directory is the
   confinement root. An exact confirmed file would break the assessment's
   per-effort folder, so refuse it and ask for a directory or remain chat-only. A
   user-profile `[architecture] output_dir` may propose the personal root but is
   optional and is not repository authority. Expand `~`, realpath-resolve,
   reject `..`, symlink, junction/reparse-point, and containment uncertainty,
   and recheck every derived child beneath the root before writing.
3. **`repository-resolved`** — only when compatible Core exposes
   `semantic-surface-resolution.v1`. Supply the selected role and bounded
   candidates in the required precedence order: explicit destination; declared policy or
   configuration; established repository convention; established external
   destination. Discovery is at most two analogues and tests. Consume the Wave 1
   result unchanged; mandatory-policy conflict, ambiguity, absence, unsafe path,
   and refusal have zero effects.
4. **`repository-handoff`** — Core is absent or incompatible. Render the role,
   explicit destination if any, bounded evidence, and needed write, then stop
   with zero repository effects until compatible Core returns a confined
   result. The user may correct or confirm evidence in the handoff, but that is
   not a Wave 1 result. One analogue is not a convention and contradictions fail
   closed.

Repo-root `[architecture] output_dir` is optional declared-configuration
candidate evidence, not a universal architecture destination. Do not silently
create configuration or a directory. External locators stay external and are
not fetched or coerced to local paths. After a local destination clears its
mode-specific boundary, create `<destination>/<topic-slug>/assessment.md`, keep
approved profiler evidence beside it, surface the absolute target, and retain
the existing write approval. A repository handoff never reaches this write step.
