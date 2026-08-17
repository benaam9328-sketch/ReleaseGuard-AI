# ReleaseGuard AI — Development Guide

## Development Philosophy

Build ReleaseGuard incrementally.

The goal is not only to finish a hackathon application but to rebuild practical development skills while strengthening DevOps skills.

Recommended sequence:

`Understand → implement → test → containerize → CI/CD → security → DORA → AI → infrastructure → observability → dashboard`

Do not generate the entire project with an AI coding agent in one shot.

## Initial Environment

Expected:
- Git
- Python 3.12 (project target). Local test run on this machine used Python 3.10 until 3.12 is installed.
- Node.js (for Next.js)
- VS Code
- Docker / Docker Desktop
- PostgreSQL (via Docker Compose for local development)
- GitHub account/repository
- Groq API access for `openai/gpt-oss-20b` (Free plan)

## Run the bootstrap (RG-003)

From the repository root:

```text
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

API:
- `GET /health` — process liveness
- `GET /ready` — storage backend (`memory` or `postgres`)
- `POST /v1/releases` — submit compact or canonical evidence; returns `{ evidence, assessment }`
- `GET /v1/releases/{release_id}` — retrieve stored evidence
- `GET /v1/releases/{release_id}/assessment` — deterministic risk score, signals, recommendation
- `POST /v1/releases/{release_id}/approval` — record `approve` or `reject` (does not change the score)

Without `DATABASE_URL`, evidence is stored in memory so the API can start. That is a bootstrap fallback, not a second database.

## Run with Docker (RG-005)

```text
docker build -t releaseguard-ai .
docker run --rm -p 8000:8000 releaseguard-ai
docker compose up --build
```

GitHub Actions CI (RG-006) runs pytest on Python 3.12 and builds the image. It does not deploy.

PostgreSQL:

```text
docker compose up -d db
copy .env.example .env
uvicorn app.main:app --reload
```

Do not implement scoring, DORA calculation, AI, or the dashboard in this stage.

## Database

PostgreSQL is the approved store (ADR-011).

Use it for:
- normalized release evidence,
- DORA events,
- assessment history,
- labeled synthetic historical data,
- recorded Approve/Reject decisions.

Do not add a second database.

## Environment Variables

Never commit secrets.

Document names, not values.

Expected names (values stay in local env / secret store):
- `DATABASE_URL`
- `GROQ_API_KEY`
- `GITHUB_TOKEN` (or equivalent)
- AWS credentials only if real AWS evidence is enabled

## DORA Development Rules

- Define event types before calculations.
- Default window is 30 days; also compute a 7-day trend.
- Lead time starts at the first commit associated with the PR and ends at production deployment.
- CFR counts failed deploy, rollback, or an incident with `attribution_confidence=attributed`.
- `likely_related` timestamp matches do not increment CFR.
- Preserve timestamps.
- Test calculations with known examples.
- Treat missing events as unknown/unavailable.
- Count a failed deployment once even if multiple failure outcomes apply.

## Deployment

Later path: Docker build → ECR → ECS → CloudWatch.

Not part of the first evidence slice. If live ECS/CloudWatch data is unavailable, use clearly labeled synthetic fallback data.

## Recommended Learning Workflow

For each feature:
1. Understand the concept.
2. Define the requirement.
3. Attempt a small implementation.
4. Ask an AI agent to review/explain.
5. Fix issues.
6. Add tests.
7. Commit a focused change.

## Development Stages

### Stage 1 — Minimal API
Build a small FastAPI service.

Learn:
- Python structure,
- virtual environments,
- HTTP,
- JSON,
- Pydantic,
- REST APIs.

### Stage 2 — Risk Engine
Build deterministic release-risk logic without AI.

Learn:
- data modelling,
- functions,
- validation,
- unit testing.

### Stage 3 — DORA Engine
Build DORA calculations from normalized events.

Learn:
- event modelling,
- timestamps,
- aggregation,
- metric definitions,
- edge-case handling.

### Stage 4 — Docker
Containerize the service.

### Stage 5 — GitHub Actions
Automate:
- dependency installation,
- tests,
- linting,
- Docker build.

### Stage 6 — Security
Add Trivy/security evidence.

### Stage 7 — AI
Add grounded Groq explanation after deterministic logic works.

### Stage 8 — Terraform/AWS
Add infrastructure/deployment evidence. Use real AWS where practical; otherwise labeled synthetic fallback.

### Stage 9 — Observability
Add runtime health and post-release context.

### Stage 10 — Dashboard
Build `/dashboard` only (Next.js App Router + Tailwind):
- DORA,
- release risk,
- historical context,
- AI recommendation,
- recorded approval state.

## AI Coding Assistant Rules

Use Cursor/Codex/Claude Code for:
- repetitive implementation,
- test generation after understanding the requirement,
- debugging,
- refactoring,
- documentation.

Do not ask an agent to:
- build the entire project without a plan,
- invent architecture,
- invent DORA formulas,
- invent external APIs,
- silently add dependencies,
- refactor unrelated code.

