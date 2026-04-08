# IT Planet Scraping Pipeline

Async GCP-based product scraping pipeline for 4 e-commerce collectors. Clients submit a URL via API, the pipeline scrapes the site in the background, and delivers a structured CSV to Google Cloud Storage.

---

## Architecture

```
Client
  │  POST /scrape  (API Key)
  ▼
Cloud Run Service (CRS) ─── Firestore (job state)
  │  Cloud Task
  ▼
Collector Worker (Cloud Run Service)
  │  curl_cffi / camoufox + Brightdata proxy
  ▼
GCS  ─── Slack + Email notifications
```

**Tonitrus fan-out:**

```
CRS → Cloud Task → Tonitrus Discovery
                       │  N Cloud Tasks (one per leaf category)
                       ▼
               Tonitrus Workers (parallel)
                       │  atomic Firestore counter
                       ▼ (last worker)
               Tonitrus Merge → GCS
```

---

## Collectors

| Collector  | Site            | HTTP Client     | Proxy | Dedup Key     | Special Logic                        |
|------------|-----------------|-----------------|-------|---------------|--------------------------------------|
| jacob      | jacob.de        | curl_cffi       | DC    | `artnr`       | Binary-search pagination + price-range split when > MAX_PAGE=500 |
| it_resell  | it-resell.com   | curl_cffi       | Res.  | `variant_id`  | 4 parallel workers across ~740 pages |
| it_market  | it-market.com   | curl_cffi       | DC    | `product_code`| 5 sort orders (name-asc/desc, price-asc/desc, topseller) + MAX_PAGE_CAP=415 |
| tonitrus   | tonitrus.com    | camoufox        | Res.  | `product_code`| Fan-out: 1 Cloud Task per leaf category; CTO variant swatch-click extraction |

---

## Project Structure

```
IT planet/
├── shared/                   # Shared utilities (imported by all services)
│   ├── config.py             # Env var loader – fast-fails on missing required vars
│   ├── firestore_client.py   # Job CRUD + Tonitrus atomic counter
│   ├── gcs_client.py         # CSV upload
│   ├── http_client.py        # curl_cffi session + proxy factories
│   ├── notifications.py      # Slack webhook + SMTP email
│   └── tasks.py              # Cloud Tasks enqueue helper
│
├── crs/                      # Public API (Cloud Run Service)
│   ├── main.py               # POST /scrape, GET /jobs/{id}
│   ├── requirements.txt
│   └── Dockerfile
│
├── collectors/
│   ├── jacob/                # Jacob.de collector
│   │   ├── scraper.py        # Full scrape logic (PLP → price ranges → PDPs)
│   │   ├── main.py           # FastAPI worker (receives Cloud Tasks POST)
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── it_resell/            # IT-Resell.com collector
│   │   ├── scraper.py
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── it_market/            # IT-Market.com collector
│   │   ├── scraper.py        # 5-sort strategy
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── tonitrus/             # Tonitrus.com collector (fan-out)
│       ├── discovery.py      # Scrapes category tree, enqueues N worker tasks
│       ├── worker.py         # Scrapes one leaf category (PLPs + CTO PDPs)
│       ├── merge.py          # Reads Firestore, writes CSV to GCS
│       ├── requirements.txt
│       └── Dockerfile        # Single image; ENTRY_POINT=discovery|worker|merge
│
├── tests/
│   ├── conftest.py           # Env stubs + HTML fixtures
│   ├── unit/                 # Pure unit tests (no I/O)
│   ├── integration/          # Mocked HTTP, real pipeline logic
│   └── e2e/                  # Full API cycle with mocked GCP services
│
├── pyproject.toml            # Ruff + pytest + coverage config
├── .env.example              # Template for environment variables
├── .gitignore
└── README.md
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all values.

### Required

| Variable | Description |
|---|---|
| `PROXY_USER` | Brightdata proxy username |
| `PROXY_PASS` | Brightdata proxy password |
| `GCS_BUCKET` | GCS bucket name for CSV output |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `CLOUD_TASKS_QUEUE` | Cloud Tasks queue name (short name, not full path) |
| `API_KEY` | Secret key for client authentication (`X-Api-Key` header) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `SMTP_HOST` | SMTP server host |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password |
| `SMTP_FROM` | Sender email address |
| `NOTIFICATION_EMAIL` | Recipient email address for job notifications |

### Worker URLs (set after initial deploy)

| Variable | Description |
|---|---|
| `JACOB_WORKER_URL` | Cloud Run URL of the Jacob worker |
| `IT_RESELL_WORKER_URL` | Cloud Run URL of the IT Resell worker |
| `IT_MARKET_WORKER_URL` | Cloud Run URL of the IT Market worker |
| `TONITRUS_DISCOVERY_URL` | Cloud Run URL of the Tonitrus discovery service |
| `TONITRUS_WORKER_URL` | Cloud Run URL of the Tonitrus worker service |
| `TONITRUS_MERGE_URL` | Cloud Run URL of the Tonitrus merge service |

### Optional

| Variable | Default | Description |
|---|---|---|
| `PROXY_HOST` | `brd.superproxy.io` | Brightdata proxy host |
| `PROXY_PORT_DC` | `22225` | Datacenter proxy port (Jacob, IT Market) |
| `PROXY_PORT_RESIDENTIAL` | `33335` | Residential proxy port (IT Resell, Tonitrus) |
| `CLOUD_TASKS_LOCATION` | `europe-west1` | GCP region for Cloud Tasks |
| `CLOUD_TASKS_SA_EMAIL` | _(empty)_ | Service account for OIDC auth on worker tasks |

---

## API

### `POST /scrape`

Enqueue a new scrape job.

**Headers:** `X-Api-Key: <your_key>`

**Body:**
```json
{
  "collector": "jacob",
  "input_url": "https://www.jacob.de/notebooks"
}
```

**Response `202`:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

### `GET /jobs/{job_id}`

Poll job status.

**Headers:** `X-Api-Key: <your_key>`

**Response `200`:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "collector": "jacob",
  "status": "complete",
  "output_url": "gs://your-bucket/jacob/2026-04-07/550e8400.csv",
  "error": null
}
```

**Status values:** `queued` → `running` → `complete` | `failed`

---

## CSV Output Schemas

All CSVs include `status` (`ok` | `failed`) and `error_message` columns per row.

**Jacob:** `artnr, name, url, sku, mpn, ean, description, brand, category_path, breadcrumbs, price, currency, price_min, price_max, condition, availability, stock, delivery_time, raw_condition, jsonld_offer_count, jsonld_price_min, jsonld_price_max, status, error_message`

**IT Resell:** `handle, name, product_url, variant_id, sku, price_min, price_max, availability, description, ean, brand, mpn, manufacturer, price_zero_flag, source_url, status, error_message`

**IT Market:** `product_name, product_code, product_id, product_url, breadcrumb, category, subcategory, model, description, ean_upc, brand, variants (JSON), input_url, coverage_pct, status, error_message`

**Tonitrus:** `product_name, product_code, product_url, category, breadcrumb, description, ean_upc, brand, price, condition, stock, availability, variants (JSON), input_url, is_cto, status, error_message`

---

## Local Development

```bash
# Install dev dependencies
pip install -r collectors/jacob/requirements.txt
pip install pytest pytest-asyncio httpx ruff coverage

# Run all tests
pytest

# Run by layer
pytest tests/unit/ -m unit
pytest tests/integration/ -m integration
pytest tests/e2e/ -m e2e

# Lint
ruff check .

# Format
ruff format .

# Coverage
coverage run -m pytest tests/unit/ tests/integration/
coverage report
```

---

## Deployment

Each service is containerised independently. Deploy order:

1. **Build and push all images** to Artifact Registry
2. **Deploy worker services** (jacob, it_resell, it_market, tonitrus × 3)
3. **Copy worker URLs** into CRS env vars
4. **Deploy CRS** with all `*_WORKER_URL` vars set

**Tonitrus** uses a single Docker image with the `ENTRY_POINT` env var selecting the role:

```bash
# Three separate Cloud Run Services from one image:
ENTRY_POINT=discovery  # → runs discovery.py
ENTRY_POINT=worker     # → runs worker.py
ENTRY_POINT=merge      # → runs merge.py
```

### Cloud Tasks queue setup

```bash
gcloud tasks queues create it-planet-queue \
  --location=europe-west1 \
  --max-concurrent-dispatches=10 \
  --max-attempts=3 \
  --min-backoff=10s
```

### Firestore TTL policies

Create TTL policies in the Firestore console:
- Collection `jobs` → field `expires_at` (30 days)
- Collection `tonitrus_products/{run_id}/*` → field `expires_at` (7 days)

---

## Observability

- **Slack:** All job events (start, complete, fail, rate-limit) posted to webhook
- **Email:** Job complete / fail sent to `NOTIFICATION_EMAIL` via SMTP
- **Firestore:** Live job state readable at any time via `GET /jobs/{job_id}`
- **GCS:** Output CSVs at `gs://{GCS_BUCKET}/{collector}/{YYYY-MM-DD}/{run_id}.csv`
- **Cloud Run logs:** Structured stdout from uvicorn + Python traceback on error
