# ReleaseGuard AI — Technology Stack

## Selected / Strongly Intended

### Python 3.12
Backend/application language.

### FastAPI
Backend/API framework. Use the current stable FastAPI release compatible with Python 3.12.

### Next.js App Router + React + Tailwind
Frontend dashboard. First page: `/dashboard` only.

### PostgreSQL
Persistence for release evidence, DORA events, assessment history, labeled synthetic history, and recorded approvals.

Local development: PostgreSQL via Docker Compose unless a later decision says otherwise.

### Git / GitHub
Source control, collaboration, and first-slice code evidence (one configured repository).

The adapter should allow additional repos later.

### GitHub Actions
First-slice CI/CD evidence: build, test, workflow duration, deployment workflow when present.

### Trivy
First-slice security evidence: CRITICAL / HIGH / MEDIUM / LOW.

### Docker
Application packaging, local PostgreSQL, and later image build for ECR/ECS.

## DORA / Delivery Data

### GitHub / GitHub Actions
Primary source for code-change and workflow events in the first slice.

Lead time starts at the first commit associated with the PR and ends at production deployment.

Default DORA window: 30 days, plus a 7-day trend.

Until ECS exists, qualifying deployment events may come from a GitHub Actions deploy workflow and/or labeled synthetic events.

### AWS ECS + ECR
Later deployment path (not first slice):

`Docker build → ECR → ECS → CloudWatch`

If live AWS evidence is unavailable, use clearly labeled synthetic fallback data.

### CloudWatch
Later source for post-release health (error rate / latency).

### Incident Data Source
ReleaseGuard-owned historical dataset first (synthetic allowed if labeled).

Future candidate: ServiceNow/Jira.

## Infrastructure

### Terraform
Later candidate for high-risk infrastructure-change evidence. Not a first-slice critical source.

## AI

### Groq + openai/gpt-oss-20b
LLM provider/model for grounded AI explanation. Groq retired `llama-3.3-70b-versatile` on 2026-08-16. `openai/gpt-oss-20b` is on Groq's Free plan.

The AI must receive structured evidence and deterministic risk signals.

One LLM provider for the MVP.

## Auth

No user login for the hackathon MVP.

Protect secrets and APIs: environment variables, no hard-coded keys, minimize sensitive data in logs and prompts.

## Developer Tools

- VS Code.
- Docker Desktop.
- Git.
- AI coding assistants such as Cursor, Codex, or Claude Code.

## Technology Guardrails

- One backend framework (FastAPI).
- One primary frontend framework (Next.js App Router + React + Tailwind).
- One LLM provider (Groq) in the MVP.
- PostgreSQL is the approved database; do not add a second database.
- No Kubernetes solely for technology count.
- No Argo Rollouts, OPA/Kyverno, SBOM, or Cosign until an approved task pulls them in.
- Every dependency must support an approved requirement/task.
- DORA calculations should remain deterministic and testable.
