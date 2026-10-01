# Contract amendment: core changelog authority

Date: 2026-09-29

Owner authority: eugenelim approved the controlled amendment in the delivery
session after the repository evidence below was surfaced.

Reason: the approved T3 task named `packs/core/CHANGELOG.md`, but that file does
not exist. `tools/check-core-release.py` names `docs/product/changelog.md` as the
core release changelog, and `packs/core/seeds/docs/product/changelog.md` is its
pack-source seed. The repository therefore overrides the prompt and initial
contract on this file location.

Bounded amendment: replace the nonexistent core changelog destination with the
seed source and generated product-changelog projection. T1 and T2 remain
complete and unchanged. No behavior, payload, refusal, safety boundary, or
release-version rule changes.

Additional Owner authority: after secure-design review sustained a finding,
eugenelim approved a second bounded amendment in the delivery session. JSON
refusal `detail` becomes a fixed public-safe message per refusal code with a
96-character schema maximum; human stderr keeps the richer diagnostic. A new
unfinished correction task owns the code, schema, tests, and mutation proof,
and the prior release/projection task moves after it. The nine refusal codes,
envelope fields, payload version, completed T1/T2 work, and dispatch boundary
do not change.

Final Owner authority: after `FORCE=1 make build-self` restored source/projection
parity, eugenelim approved correcting the changelog ownership statement. Pack
seeds are scaffold inputs and do not generate over an existing repository file;
`packs/core/seeds/docs/product/changelog.md` and
`docs/product/changelog.md` are therefore separately maintained outputs. The
seed carries the new-release scaffold and the repository changelog carries the
actual core release entry read by `tools/check-core-release.py`. T1, T2, and T3
remain complete; only unfinished T4 reopens. No CLI behavior, schema, safety
boundary, or version rule changes.

Resource-bound Owner authority: after post-gates security review found that the
`Touches:` comparison fan-out was unbounded, eugenelim requested a measurement
of the current repository corpus and approved the measured limits on 2026-09-29.
Across 2,835 recognized tasks, the maximum effective declaration was 34 globs
per task, 163 characters per glob, and 34 total globs in a scheduled wave; the
largest potential wave comparison count was 197. The amended contract keeps the
existing 64-task wave limit and adds limits of 64 effective globs per task, 256
effective globs per selected wave, and 256 characters per effective glob. A
limit breach folds into the existing `plan-status-illegal` refusal because the
invalid input is authored plan content; no refusal code is added. The per-wave
limit bounds the worst-case comparison count to 32,256 under the existing
64-task limit. T1, T2, and T3 remain complete; unfinished T4 owns the repair,
schema changes, tests, and source-edited mutation proof.
