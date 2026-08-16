# ReleaseGuard AI

A FastAPI service that scores how risky a release is before it ships.

You send it whatever evidence you have about a release (CI and test results, a
Trivy scan, changed files, infrastructure changes, past failures). It fills in
the gaps honestly, runs a set of deterministic detectors over the result, and
returns a risk score with the reasons behind it.

Missing evidence is never treated as a pass. If Trivy did not run, the release
does not get a clean bill of health, it gets a `missing_critical_evidence`
signal instead.

## Scoring

Each detector that fires contributes a weight:

| Signal | Weight |
| --- | --- |
| `ci_failure` | 30 |
| `critical_vulnerability` | 30 |
| `rollback_required` | 30 |
| `similar_historical_failure` | 20 |
| `high_vulnerability` | 15 |
| `database_migration` | 15 |
| `high_risk_infrastructure_change` | 15 |
| `large_change_surface` | 10 |
| `missing_critical_evidence` | 10 |

Signals belong to deduplication groups, and only the heaviest signal in a group
counts, so a failed pipeline and a recent rollback are not charged twice. The
total is capped at 100 and mapped to a band:

| Score | Level | Recommendation |
| --- | --- | --- |
| 0-30 | LOW | `ALLOW` |
| 31-60 | MEDIUM | `REQUIRE_HUMAN_REVIEW` |
| 61-100 | HIGH | `BLOCK_APPROVAL_REQUIRED` |

The recommendation is advisory. Approvals are recorded against a release but do
not change its score, and nothing is blocked yet (`enforcement` is `none`).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness, reports the active storage backend |
| `POST` | `/v1/releases` | Submit evidence, get back evidence plus assessment |
| `GET` | `/v1/releases/{release_id}` | Fetch stored evidence |
| `GET` | `/v1/releases/{release_id}/assessment` | Re-score a stored release |
| `POST` | `/v1/releases/{release_id}/approval` | Record an approve or reject |

Interactive docs are at `/docs` once the server is running.

## Running it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then submit a release:

```bash
curl -X POST http://localhost:8000/v1/releases -H "Content-Type: application/json" -d '{"release_id":"REL-001","repository":"releaseguard-ai","commit_sha":"abc123def456","ci_status":"success","test_status":"success","critical_vulnerabilities":0,"high_vulnerabilities":2}'
```

Tests:

```bash
pytest
```

## Docker

```bash
docker build -t releaseguard-ai .
docker run --rm -p 8000:8000 releaseguard-ai
```

Without `DATABASE_URL` the API uses in-memory storage.

API + Postgres:

```bash
docker compose up --build
```

GitHub Actions on `master` runs pytest (Python 3.12) and builds the image. It
does not deploy.

## Evidence sources

The compact payload above is the minimum. You can also hand it richer input:

- `trivy_report`: paste raw `trivy --format json` output and the counts and CVE
  list are parsed out of it.
- Live GitHub data: set `GITHUB_TOKEN` and `GITHUB_REPOSITORY` (or use an
  `owner/repo` value for `repository`) and the service pulls the commit, its
  pull request, changed files, and the matching Actions run itself.

If a fetch fails, that source is marked failed rather than guessed at.

## Storage

Everything is in memory by default, which is enough for local work and for the
test suite. Set `DATABASE_URL` (copy `.env.example` to `.env`) and it switches
to Postgres, creating its tables on startup. A local Postgres is available via:

```bash
docker compose up -d db
```

## Layout

```
app/
  adapters/   pull evidence from GitHub, Actions, and Trivy
  api/        HTTP routes
  risk/       signal catalog, detectors, scoring engine
  schemas/    pydantic models for evidence and assessments
  normalize.py  compact payload -> full evidence
  storage.py    memory and Postgres backends
tests/
```
