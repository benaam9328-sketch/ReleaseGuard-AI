# ReleaseGuard AI — Cursor Context Pack

Use these files as the project source of truth.

## Read First

1. `AGENTS.md`
2. `PROJECT.md`
3. `REQUIREMENTS.md`
4. `ARCHITECTURE.md`
5. `DECISIONS.md`
6. `CONTRACTS.md`
7. `TASKS.md`
8. `CONTEXT.md`

Then consult:
- `TECH_STACK.md`
- `DEVELOPMENT.md`
- `TESTING.md`
- `skills.md`

## Important Product Distinction

**DORA ≠ Release Risk**

DORA measures delivery performance:
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Time to Restore Service

ReleaseGuard risk combines current release evidence, security, infrastructure, historical context, DORA context, and runtime evidence.

## SOTA

SOTA means the project's state-of-the-art release-intelligence capability set:
- AI-assisted reasoning
- historical pattern detection
- multi-source evidence
- DORA-aware context
- security/IaC awareness
- runtime feedback
- explainability
- human-in-the-loop governance

Do not create an unsupported SOTA score.

## Current Task

`RG-005` / `RG-006` — Docker image and GitHub Actions CI. Evidence adapters are complete.

Do not generate the full platform.

## Evidence adapters

`POST /v1/releases` still accepts compact JSON.

Optional Trivy scanner JSON:

```json
{ "trivy_report": { "Results": [] } }
```

Optional live GitHub / Actions fetch when `.env` has `GITHUB_TOKEN` and the repository is `owner/repo` (or `GITHUB_REPOSITORY` is set). Failed fetches stay `unknown`; counts are not invented as zero.

