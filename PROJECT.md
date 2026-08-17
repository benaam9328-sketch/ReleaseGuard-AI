# ReleaseGuard AI — Project Constitution

## One-Line Description

ReleaseGuard AI is an intelligent release-risk and governance platform that combines DevOps release evidence, DORA delivery-performance metrics, historical operational context, security/infrastructure signals, and AI reasoning to help human approvers make better production-release decisions.

## Problem Statement

A release can pass build, automated tests, and staging validation and still carry production-specific operational or security risk.

Organizations also have delivery-performance data spread across CI/CD, deployment, incident, and source-control systems. Existing tools produce evidence, but the evidence is often fragmented.

ReleaseGuard brings the evidence together and turns it into:
- delivery-performance visibility,
- contextual release-risk analysis,
- explainable findings,
- and an approval recommendation.

## Why It Exists

The project demonstrates practical DevOps + AI release governance rather than another generic AI chatbot or another CI/CD system.

## Target Users

- Developers preparing a release.
- DevOps/platform engineers.
- Release/change approvers.
- Engineering managers.
- Teams that need auditable release decisions and delivery-performance visibility.

## Core Value Proposition

ReleaseGuard:
1. Collects release evidence.
2. Calculates DORA delivery metrics from delivery/deployment/incident events.
3. Normalizes current release context.
4. Applies deterministic risk signals.
5. Adds historical and operational context.
6. Uses AI to explain contextual risk.
7. Produces an auditable recommendation for the human approver.

## Primary Workflow

`Code → CI/CD → testing/security/infrastructure evidence → ReleaseGuard → DORA context + risk assessment → AI explanation → human approval → deployment → runtime outcome → historical feedback`

ReleaseGuard is not intended to replace staging or normal CI/CD.

## DORA Layer

Initial DORA metrics:
- Deployment Frequency.
- Lead Time for Changes.
- Change Failure Rate.
- Time to Restore Service.

DORA answers:

> **How healthy and effective is our software delivery process?**

DORA does not by itself answer whether one specific release is safe.

## Release Risk Layer

Release risk considers:
- Code/change complexity.
- CI/CD results.
- Security findings.
- Infrastructure changes.
- Deployment context.
- Historical incidents/rollbacks.
- DORA context.
- Runtime/deployment health where available.

This answers:

> **Given the current release and its operational context, what should the approver pay attention to?**

## SOTA Capability Layer

SOTA is treated as the modern release-intelligence capability set:
- AI-assisted contextual analysis.
- Historical pattern detection.
- Change-risk analysis.
- Security and IaC context.
- DORA-aware release analysis.
- Deployment/runtime feedback.
- Explainable recommendations.
- Human-in-the-loop governance.

No unsupported “SOTA score” is required.

## Core MVP Scope

### MVP 1 — Release Risk
- Release evidence.
- Normalized release context.
- Deterministic risk rules.
- Risk score/level.
- Explainable findings.
- Human approval recommendation.

### MVP 2 — DORA
- Four DORA metrics.
- Source event model.
- Time-window selection.
- Metric calculation and validation.
- DORA dashboard/summary.
- DORA context available to release analysis.

### MVP 3 — AI
- Grounded AI explanation.
- Recommendation rationale.
- Historical/contextual interpretation.

## Planned / Candidate Integrations

First slice:
- GitHub.
- GitHub Actions.
- Trivy.

Later:
- Docker / ECR / ECS.
- CloudWatch.
- Terraform.
- Historical release/incident data.
- Future ServiceNow/Jira incident adapters.

Not current: Argo Rollouts, OPA/Kyverno, SBOM, Cosign.

## Out of Scope

- Replacing CI/CD.
- Replacing staging/QA.
- Guaranteeing production safety.
- Fully autonomous production deployment.
- Building every enterprise integration.
- Treating AI as the only source of truth.
- Fabricating real enterprise history.
- Inventing an unsupported SOTA metric.

## Success Criteria

The project should demonstrate a believable workflow where:
1. Release evidence is collected.
2. DORA metrics provide delivery context.
3. Risk rules identify release signals.
4. AI explains the important context.
5. The system produces an auditable recommendation.
6. A human approver remains in control.

## Constraints

- Hackathon implementation window is limited.
- Development should remain understandable and incremental because coding skills are being rebuilt.
- DevOps learning is a first-class goal.
- Scope should remain focused on release safety, delivery intelligence, and governance.
