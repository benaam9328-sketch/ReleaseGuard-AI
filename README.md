> ## 📌 Project Credits
> 
> **Development:** Done with help of Cursor  
> **README:** Created with help of ChatGPT  
> **DevOps:** Done by me


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
| `GET` | `/v1/releases` | List stored releases |
| `GET` | `/v1/releases/{release_id}` | Fetch stored evidence |
| `GET` | `/v1/releases/{release_id}/assessment` | Re-score a stored release |
| `POST` | `/v1/releases/{release_id}/approval` | Record an approve or reject |
| `GET` | `/v1/dora` | 30-day DORA metrics plus a 7-day trend |
| `POST` | `/v1/events` | Store a delivery/incident event |

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

## Docker (API + Postgres)

Start Docker Desktop, then from the repository root:

```bash
docker compose up --build
```

Check it:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

You should see `{"status":"ok","service":"releaseguard-ai"}` and `{"status":"ok","storage":"postgres"}`.

API docs: http://localhost:8000/docs

Create a sample release:

```bash
curl -X POST http://localhost:8000/v1/releases -H "Content-Type: application/json" -d "{\"release_id\":\"REL-001\",\"repository\":\"releaseguard-ai\",\"commit_sha\":\"abc123def456\",\"ci_status\":\"success\",\"test_status\":\"success\",\"critical_vulnerabilities\":0,\"high_vulnerabilities\":2}"
```

Optional Groq explanation: put `GROQ_API_KEY` in local `.env` (never commit `.env`), then recreate the API container.

API-only, in-memory, no Postgres:

```bash
docker build -t releaseguard-ai .
docker run --rm -p 8000:8000 releaseguard-ai
```

## Dashboard

With the API running on port 8000:

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000/dashboard

## GitHub Actions

## Evidence sources

The compact payload above is the minimum. You can also hand it richer input:

- `trivy_report`: paste raw `trivy --format json` output and the counts and CVE
  list are parsed out of it.
- Live GitHub data: set `GITHUB_TOKEN` and `GITHUB_REPOSITORY` (or use an
  `owner/repo` value for `repository`) and the service pulls the commit, its
  pull request, changed files, and the matching Actions run itself.

If a fetch fails, that source is marked failed rather than guessed at.

Labeled synthetic history records in `app/history/synthetic_records.json` are
matched against the current release (migration or matching vulnerability severity).
They are never presented as real enterprise history (`history.is_synthetic`).
No catalog match leaves `similar_historical_failure` false; an empty catalog stays
`unknown`, not a clean history.

DORA metrics come from stored `DeliveryEvent` records (`POST /v1/events`).
Empty event history is `unavailable`, not zero. DORA is not the risk score.

Set `GROQ_API_KEY` in `.env` (not in git) to attach a Llama 3.3 70B explanation.
The model only comments on the deterministic score and signals; it cannot change them.
Without a key, `ai_explanation.status` stays `unknown`.

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
  history/    labeled synthetic similar-failure matching
  dora/       deployment frequency, lead time, CFR, MTTR
  adapters/   pull evidence from GitHub, Actions, and Trivy
  ai/         Groq explanation of the deterministic assessment
  api/        HTTP routes
  risk/       signal catalog, detectors, scoring engine
  schemas/    pydantic models for evidence and assessments
  normalize.py  compact payload -> full evidence
  storage.py    memory and Postgres backends
web/            Next.js /dashboard
tests/
```
