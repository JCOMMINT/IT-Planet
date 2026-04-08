# Jacob.de scraping pipeline

## Site info flow (what we learned)
- **Sitemaps**: `sitemap_idx_artikel.xml` is an index of product-ID sitemaps (only `/produkte/` URLs). No category→product mapping exists there.
- **Categories**: The category tree is embedded in the HTML nav. It is **UI‑driven**, not expressed in PDP URLs.
- **PDP**: Product JSON‑LD contains `Product.category` and `additionalProperty` (Gruppe). Breadcrumbs are not exposed as BreadcrumbList JSON‑LD.
- **PLP**: Category pages can be filtered by **price ranges** (e.g., `price-min` / `price-max`) and paginated. Total results are **not in HTML**, so we use page‑existence checks.

## Workflow
### 1) Discovery
- Check robots/sitemaps → confirm no category→product mapping.
- Inspect category HTML nav → derive top/child/grandchild logic.
- Validate PLP params (`sortBy`, `price-min`, `price-max`, `page`) and PDP JSON‑LD.

### 2) PLP (category product list)
- Use **price‑range recursion** to keep each range ≤ 500 pages.
- Fetch PLP pages, extract product URLs + basic fields (name, price, artnr).
- Save as **NDJSON** and resume by completed ranges.
- Attach breadcrumbs from **category map** (URL → breadcrumb).

### 3) PDP (full product details)
- If needed, read PDP JSON‑LD to extract:
  - name, price, currency, SKU/MPN/GTIN, brand, additional properties
  - category path from `Product.category`

## Strategy
1) Build the full **category map** from UI nav (top → child → grandchild).
2) For a target category URL, run **PLP price‑range recursion**.
3) Use the category map to attach **breadcrumbs** without PDP crawling.
4) Only hit PDPs when richer data is required.

## CLI usage (src/jacob_scrape.py)

### 1) Build category map (JSON tree)
```bash
python -m src.jacob_scrape \
  --mode category-map \
  --output jacob_category_tree.json \
  --workers 9 \
  --proxy "http://USER:PASS@HOST:PORT"
```

### 2) PLP URL list for one category (NDJSON, no PDP)
Uses **price ranges + resume** and auto‑adds breadcrumbs from the map.
```bash
python -m src.jacob_scrape \
  --mode plp-urls \
  --category-url "https://www.jacob.de/service-support-systeme/" \
  --category-map jacob_category_tree.json \
  --output service_support_systeme_plp.ndjson \
  --ranges-state service_support_systeme_ranges.json \
  --max-page 500 \
  --sort preis_up \
  --proxy "http://USER:PASS@HOST:PORT"
```

### 3) PLP URL list for all categories (NDJSON, no PDP)
**Use when you want breadth**: URLs + basic fields for the full site without PDP fetches.\nWalks the category tree and crawls each category URL with price‑range recursion.
```bash
python -m src.jacob_scrape \
  --mode plp-all-categories \
  --category-map jacob_category_tree.json \
  --output jacob_all_categories_plp.ndjson \
  --ranges-state jacob_all_categories_ranges.json \
  --max-page 500 \
  --sort preis_up \
  --proxy "http://USER:PASS@HOST:PORT"
```

### 4) PDP category mapping (sitemap → PDP JSON‑LD)
**Use when you want depth**: reads PDP JSON‑LD to get richer attributes and category paths.\nCrawls all PDP URLs from sitemap and filters by `--target`.
```bash
python -m src.jacob_scrape \
  --mode pdp-category \
  --target "Service & Support" \
  --output products.ndjson \
  --proxy "http://USER:PASS@HOST:PORT"
```

## Notes
- **Resume support**: `--ranges-state` prevents re‑processing finished price brackets (per category).
- **Breadcrumbs**: resolved from category map (URL → breadcrumb). If a URL is not found, breadcrumb is empty.
- **Proxy**: required for scale; adjust workers to proxy capacity.

---

## Notebook: discovery + PDP sampler (proxy + logs)
A new notebook was created to consolidate **Discovery** and a **PDP sample** flow:
`jacob_discovery_pdp.ipynb`

Key behaviors:
- **Discovery**: UI-nav category tree (thread-pooled BFS) + breadcrumb index.
- **PLP**: price-range recursion to keep pages within the cap.
- **PDP**: sample only (2–3 URLs from discovery output).
- **Proxy ready**: single `PROXY_URL` is used for both HTTP/HTTPS.
- **Logging**: request-level logs with timestamps and latency; progress logs for discovery and PLP.

Important notes:
- The PDP sample **does not save** to disk by default. If needed, add a JSON or NDJSON write.
- Logging helps detect stalled ranges, blocked proxy pages, or slow endpoints.

### Logging format (examples)
- Request:
  - `[12:01:10] OK  200  0.7s https://www.jacob.de/...`
  - `[12:01:15] ERR ReadTimeout 60.0s https://www.jacob.de/...`
- Discovery progress:
  - `DISC done=100 queued=45 visited=180 depth=2`
- PLP progress:
  - `PLP range 100-200`

---

## Proposed package workflow (TDD + cloud-ready)
This is the flow we will standardize into a Python package with shared helpers and per-site modules.

### End-to-end flow of information
1) **Discovery**
   - Fetch homepage.
   - Parse category tree from UI nav.
   - Produce category tree JSON and breadcrumb index.
2) **PLP crawl**
   - For each category URL, find max price range.
   - Apply **price-range recursion** to keep ranges within `max_page`.
   - Fetch PLP pages and extract product URLs + basic fields.
   - Save as NDJSON (append-only).
3) **PDP sampling / enrichment**
   - From PLP URLs, sample N URLs (2–3 for notebook).
   - Parse PDP JSON-LD.
   - Optional: full PDP enrichment when needed.

### Package layout (proposed)
- `electro_info/`
  - `core/`
    - `http.py` (requests session, proxy, retries, logging)
    - `parsing.py` (JSON-LD helpers)
    - `storage.py` (NDJSON, checkpoints)
    - `models.py` (typed dicts or dataclasses)
  - `sites/`
    - `jacob/`
      - `discovery.py`
      - `plp.py`
      - `pdp.py`
      - `cli.py`
    - `arrow/`
    - `...`
  - `tests/`
    - `test_discovery.py`
    - `test_plp.py`
    - `test_pdp.py`
  - `pyproject.toml` (ruff, pytest, packaging)

### TDD + quality gates
- Unit tests for:
  - URL normalization
  - JSON-LD parsing
  - PLP extraction
  - Range recursion behavior
- Integration tests with **saved HTML fixtures** (no live network).
- `ruff` linting and formatting.
- Optional `mypy` typing for core helpers.

---

## Cloud-ready execution (GCP / AWS)
Target: run at scale with proxies and resumable jobs.

### Execution model
- **Discovery job** (single run per site, produces category tree + index).
- **PLP job** (per category or per price-range shard).
- **PDP job** (batch PDP fetch; optional, can be parallelized).

### Scaling approach
- Use **queue-based sharding**:
  - Each task processes a category URL + price range.
  - Task writes NDJSON and updates checkpoint state.
- Avoid global locks by writing per-shard outputs and merging after.

### Storage
- GCP: write outputs to **GCS**; checkpoints in **Firestore** or **GCS**.
- AWS: write outputs to **S3**; checkpoints in **DynamoDB** or **S3**.

### Observability
- Structured logs (JSON) for request and crawl progress.
- Metrics: pages/min, errors/min, retries, timeout ratio.

### Containerization
- Build a Docker image for the package.
- Run as:
  - GCP Cloud Run / Cloud Tasks workers
  - AWS ECS / Fargate workers

---

## Next steps
1) Finalize the notebook behavior (logging, PDP save format).
2) Extract helpers into shared core modules.
3) Add tests and ruff config.
4) Implement site modules under `sites/`.
