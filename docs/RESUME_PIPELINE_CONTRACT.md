# Resume Pipeline Contract

This document captures the current ApplyPilot resume workflow so future changes do not introduce parallel logic or score mismatches.

## Core Flow

The main analyze flow is:

1. `parse`
2. `analyze`
3. `optimize`
4. `polish`
5. `finalize + score`

The verified fix pass is separate:

1. user clicks `Apply Fixes`, or the pre-download guard triggers it
2. `apply_fixes`
3. `verify`
4. `finalize + rescore`
5. `render / export`

`/resume/apply_fixes` is already the product auto-fix entry point. The analyze stage does not inline fix application.

## Scoring Contract

Scoring must run on the final polished document so the same structured draft is used for:

- preview
- ATS score
- readiness score
- recruiter scan score
- PDF export

This avoids trust gaps between UI scoring and the exported resume.

## Formatting Guards

Empty bullet and spacing cleanup is pipeline-wide, not renderer-only. The current protection layers are:

- `packages/resume_formatter/builder.py`
- `packages/ai_engine/polish.py`
- `packages/resume_formatter/serializer.py`
- `packages/resume_formatter/templates/classic_resume.html`
- `packages/resume_formatter/renderer.py`

The intended behavior is:

`prevent -> normalize -> filter -> render`

## Fix Engine Scope

The current fix engine only supports:

- keyword injection
- contextual bullet enhancement
- skills expansion

It does not currently support:

- project title renaming
- resume header rewriting
- section renaming

Those belong in a future recommendation layer, not in the current verified fix engine.

## Near-Term Focus

The next improvements should focus on:

- signal recommendation layer
- multi-JD orchestration
- score calibration
