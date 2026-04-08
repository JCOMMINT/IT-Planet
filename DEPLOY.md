# Deploy Guide (Dev)

## Required Infrastructure

| Service | Purpose |
|---------|---------|
| GCP Cloud Run | Hosts all 5 services (CRS + 4 collectors) |
| GCP Cloud Tasks | Async job dispatch CRS → workers |
| GCP Firestore | Job state + Tonitrus product staging |
| GCP Artifact Registry | Docker image storage |
| GCP GCS | CSV output (`gs://{bucket}/{collector}/{date}/{run_id}.csv`) |
| GCP API Gateway | Public-facing API layer — auth, rate limits, quotas in front of CRS |
| Brightdata Proxy | DC port 22225 (Jacob, IT Market) · Residential port 33335 (IT Resell, Tonitrus) |
| Slack webhook | Job event notifications |
| SMTP | complete/failed email notifications |

**IAM minimum:** Cloud Run SA needs `roles/datastore.user`, `roles/storage.objectCreator`, `roles/cloudtasks.enqueuer`.

---

## One-Time Setup

```bash
# Artifact Registry repo
gcloud artifacts repositories create it-planet \
  --repository-format=docker --location=europe-west1

# Cloud Tasks queue
gcloud tasks queues create it-planet-queue \
  --location=europe-west1 \
  --max-concurrent-dispatches=10 \
  --max-attempts=3 \
  --min-backoff=10s
```

Firestore TTL policies (console):
- Collection `jobs` → field `expires_at` → 30 days
- Collection `tonitrus_products/{run_id}/*` → field `expires_at` → 7 days

---

## Build & Push

All builds run from project root (`IT planet/`). Replace `REGION` and `PROJECT`.

```bash
REPO=europe-west1-docker.pkg.dev/PROJECT/it-planet

docker build -f crs/Dockerfile                  -t $REPO/crs:latest          .
docker build -f collectors/jacob/Dockerfile      -t $REPO/jacob:latest        .
docker build -f collectors/it_resell/Dockerfile  -t $REPO/it-resell:latest    .
docker build -f collectors/it_market/Dockerfile  -t $REPO/it-market:latest    .
docker build -f collectors/tonitrus/Dockerfile   -t $REPO/tonitrus:latest     .

docker push $REPO/crs:latest
docker push $REPO/jacob:latest
docker push $REPO/it-resell:latest
docker push $REPO/it-market:latest
docker push $REPO/tonitrus:latest
```

---

## Deploy Order

**Step 1 — Deploy workers first** (no inter-service deps)

```bash
# Jacob
gcloud run deploy jacob-worker \
  --image $REPO/jacob:latest \
  --region europe-west1 --no-allow-unauthenticated \
  --set-env-vars "$(cat .env | xargs | tr ' ' ',')"

# IT Resell
gcloud run deploy it-resell-worker \
  --image $REPO/it-resell:latest \
  --region europe-west1 --no-allow-unauthenticated \
  --set-env-vars "$(cat .env | xargs | tr ' ' ',')"

# IT Market
gcloud run deploy it-market-worker \
  --image $REPO/it-market:latest \
  --region europe-west1 --no-allow-unauthenticated \
  --set-env-vars "$(cat .env | xargs | tr ' ' ',')"

# Tonitrus — 3 services, 1 image, different ENTRY_POINT
gcloud run deploy tonitrus-discovery \
  --image $REPO/tonitrus:latest \
  --region europe-west1 --no-allow-unauthenticated \
  --set-env-vars "ENTRY_POINT=discovery,$(cat .env | xargs | tr ' ' ',')"

gcloud run deploy tonitrus-worker \
  --image $REPO/tonitrus:latest \
  --region europe-west1 --no-allow-unauthenticated \
  --set-env-vars "ENTRY_POINT=worker,$(cat .env | xargs | tr ' ' ',')"

gcloud run deploy tonitrus-merge \
  --image $REPO/tonitrus:latest \
  --region europe-west1 --no-allow-unauthenticated \
  --set-env-vars "ENTRY_POINT=merge,$(cat .env | xargs | tr ' ' ',')"
```

**Step 2 — Collect worker URLs**

```bash
gcloud run services describe jacob-worker --region europe-west1 --format 'value(status.url)'
# repeat for each service
```

**Step 3 — Deploy CRS with worker URLs**

Add all `*_WORKER_URL` vars to `.env`, then:

```bash
gcloud run deploy it-planet-crs \
  --image $REPO/crs:latest \
  --region europe-west1 --allow-unauthenticated \
  --set-env-vars "$(cat .env | xargs | tr ' ' ',')"
```

CRS is the only public-facing service. Workers are internal (`--no-allow-unauthenticated`), reached only via Cloud Tasks.

**Step 4 — Deploy GCP API Gateway in front of CRS**

Create OpenAPI spec `api.yaml`:

```yaml
swagger: "2.0"
info:
  title: IT Planet API
  version: "1.0"
host: "GATEWAY_HOST"
schemes: [https]
x-google-backend:
  address: "https://it-planet-crs-xxxx-ew.a.run.app"  # CRS URL from Step 3
paths:
  /scrape:
    post:
      operationId: postScrape
      parameters:
        - in: header
          name: X-Api-Key
          type: string
          required: true
      responses:
        "202":
          description: Queued
  /jobs/{job_id}:
    get:
      operationId: getJob
      parameters:
        - in: path
          name: job_id
          type: string
          required: true
        - in: header
          name: X-Api-Key
          type: string
          required: true
      responses:
        "200":
          description: Job status
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: OK
```

Deploy gateway:

```bash
# Create API config
gcloud api-gateway api-configs create it-planet-config \
  --api=it-planet-api \
  --openapi-spec=api.yaml \
  --project=PROJECT

# Create gateway
gcloud api-gateway gateways create it-planet-gateway \
  --api=it-planet-api \
  --api-config=it-planet-config \
  --location=europe-west1 \
  --project=PROJECT
```

Gateway URL = client-facing endpoint. CRS URL stays internal.

Flow:
```
Client → API Gateway → CRS (Cloud Run) → Cloud Tasks → workers → GCS
```

---

## API

### Enqueue a scrape

```
POST /scrape
X-Api-Key: <API_KEY>
Content-Type: application/json

{
  "collector": "jacob",        // jacob | it_resell | it_market | tonitrus
  "input_url": "https://www.jacob.de/notebooks"
}
```

**202 response:**
```json
{ "job_id": "uuid-v4", "status": "queued" }
```

`input_url` for full-site scrape: pass the collector's base URL.
`input_url` for a single category: pass the specific category URL — scraper skips discovery.

### Poll status

```
GET /jobs/{job_id}
X-Api-Key: <API_KEY>
```

```json
{
  "job_id": "...",
  "collector": "jacob",
  "status": "complete",           // queued | running | complete | failed
  "output_url": "gs://bucket/jacob/2026-04-07/uuid.csv",
  "error": null
}
```

### Health (no auth)

```
GET /health
→ 200  { "ok": true }
```

Used as Cloud Run liveness probe.

---

## Internal Flow (dev context)

```
POST /scrape
  → Firestore: create job (status=queued)
  → Cloud Tasks: enqueue POST to worker URL with {run_id, input_url}

Worker receives Cloud Task
  → Firestore: status=running
  → scraper.run(input_url, run_id)
  → GCS: upload CSV
  → Firestore: status=complete, output_url=gs://...
  → Slack + email notify
```

**Tonitrus fan-out differs:**

```
Cloud Task → tonitrus-discovery
  → camoufox scrapes category tree
  → Firestore: set expected_count = N
  → enqueue N Cloud Tasks → tonitrus-worker (one per leaf category)

Each tonitrus-worker
  → camoufox scrapes leaf PLP pages
  → writes products to Firestore sub-collection
  → atomic increment completed_count
  → if completed_count == expected_count:
      enqueue Cloud Task → tonitrus-merge

tonitrus-merge
  → reads all products from Firestore
  → dedup on product_code
  → GCS: upload CSV
  → notify
```

---

## Env Vars Quick Ref

Copy `.env.example` → `.env` and fill all values before deploy.

| Var | Notes |
|-----|-------|
| `PROXY_USER` / `PROXY_PASS` | Brightdata credentials |
| `PROXY_PORT_DC` | `22225` — Jacob, IT Market |
| `PROXY_PORT_RESIDENTIAL` | `33335` — IT Resell, Tonitrus |
| `GCS_BUCKET` | Output CSV bucket |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `CLOUD_TASKS_QUEUE` | Short name (not full resource path) |
| `CLOUD_TASKS_SA_EMAIL` | SA for OIDC on worker task requests (optional but recommended) |
| `API_KEY` | Client auth secret — keep secret |
| `*_WORKER_URL` | Set after Step 1 deploy, needed before Step 3 |
