# ReleaseGuard AI — Testing Strategy

## Testing Principle

A task is not complete merely because the application starts. Release-risk decisions and DORA metrics must be correct, explainable, and reproducible.

## Unit Testing

Test:
- Evidence normalization.
- DORA event normalization.
- DORA metric calculations.
- Risk rules.
- Score calculation.
- Decision mapping.
- Input validation.
- Missing/unknown evidence handling.

## DORA Test Cases

### Deployment Frequency
Given 10 qualifying deployments in a 30-day window:
- count = 10
- frequency representation must match the documented definition.
Also compute the 7-day trend from the same event set.

### Lead Time
Given:
- first commit associated with the PR at 10:00
- production deployment at 18:00
Expected lead time:
- 8 hours.

### Change Failure Rate
Given:
- 20 qualifying deployments
- 3 qualifying failed outcomes (failed deploy, rollback, or attributable incident)
Expected CFR:
- 15%.
A deployment with both rollback and an attributable incident still counts as one failure.
A `likely_related` incident (timestamp correlation only) does not increment CFR.

## Risk Score Test Cases

### High-risk example from CONTRACTS.md
Given signals: critical vulnerability +30, DB migration +15, similar historical failure +20, large change +10.
Expected:
- score = 75
- level = HIGH
- recommendation = BLOCK_APPROVAL_REQUIRED
- enforcement = none

### Deduplication
Given `ci_failure` +30 and `rollback_required` +30 in group `delivery_failure`.
Expected contribution: +30, not +60.

### Missing Trivy
Trivy `scan_failed` or unavailable:
- not treated as a clean scan
- `missing_critical_evidence` +10 applies
- vulnerability counts are not coerced to 0

### Time to Restore
Given:
- incident starts 14:10
- service restored 14:50
Expected duration:
- 40 minutes.

Also test:
- unmatched events,
- reversed timestamps,
- open incidents,
- duplicate events,
- unknown source data.

## Integration Testing

Test:
- Source adapters.
- CI/CD ingestion.
- Security scanner ingestion.
- DORA event ingestion.
- Persistence if introduced.
- AI service integration using controlled inputs.

## API Testing

When APIs exist:
- valid release input,
- invalid input,
- missing fields,
- source failure,
- AI failure,
- DORA query with valid time window,
- empty event set,
- successful assessment.

## End-to-End Testing

Core scenario:

`release evidence → DORA context → risk assessment → AI explanation → recommendation`

At least:
- one low-risk/allow scenario,
- one elevated-risk/review scenario,
- one high-risk/block scenario.

## AI Evaluation

Test:
- grounding,
- hallucination,
- missing context,
- invalid input,
- model/API failure,
- prompt injection where untrusted source text reaches the model,
- consistency between recommendation and deterministic evidence.

AI must not be evaluated only on prose quality.

## Metric Integrity

DORA values must:
- be reproducible,
- identify time window,
- identify event counts,
- preserve source context,
- distinguish zero from unavailable,
- be regression-tested after changes.

## Regression

Whenever risk rules, event definitions, prompts, or decision policies change:
- run relevant tests,
- verify known DORA examples,
- verify existing release scenarios,
- verify AI explanations remain consistent with evidence.

## Definition of Done

1. Functional acceptance criteria pass.
2. Relevant tests pass.
3. Missing/error states are tested.
4. Security handling is reviewed.
5. DORA calculations are validated.
6. AI output is grounded.
7. No unrelated behavior changes.
8. Documentation reflects meaningful changes.
