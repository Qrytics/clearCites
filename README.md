# clearCites

**Live site:** [https://qrytics.github.io/clearCites/](https://qrytics.github.io/clearCites/) (marketing page; the interactive graph needs the stack below.)

clearCites maps research papers as a graph: **papers** as nodes, **citations**, **authors**, **keywords**, and **funders** as relationships. This README walks you from **installing dependencies** through **searching for a paper** and **visualizing everything related to it**.

**Two paths**

| Path | When to use |
|------|----------------|
| **[Discover](http://localhost:3000/discover)** (`/discover`) | Default: search **OpenAlex** in the browser, pick a work, choose neighborhoods (citations, co-authors, …), **ingest into Neo4j automatically**, then see the graph on the same page. |
| **Manual DOI** (`/explore` + `clearcites-ingest`) | You already have DOIs, use Semantic Scholar/CrossRef CLI ingest, or want **Neo4j-only** `GET /search`. |

---

## What you need installed

| Requirement | Used for |
|-------------|----------|
| **Git** | Clone the repository |
| **Docker Desktop** (or another Docker engine) + **Compose v2** | Neo4j, FastAPI graph API, and Next.js web app in one command |
| **Python 3.11+** and **pip** | Ingest papers into Neo4j from your machine (`clearcites-ingest`), and run tests |
| **Node.js 20+** (optional) | Only if you run the frontend with `npm run dev` *outside* Docker |

Optional keys / email:

- **`SEMANTIC_SCHOLAR_API_KEY`** — higher rate limits for `clearcites-ingest` (Semantic Scholar).
- **`CROSSREF_MAILTO`** — [CrossRef polite pool](https://github.com/CrossRef/rest-api-doc#good-manners--more-reliable-service) for CrossRef ingest.
- **`OPENALEX_MAILTO`** — [OpenAlex polite pool](https://docs.openalex.org/how-to-use/api) for **Discover** and `/openalex/*` (strongly recommended).
- **`OPENALEX_MAX_RETRIES`**, **`OPENALEX_RETRY_BACKOFF_SEC`** — optional tuning for OpenAlex HTTP retries (defaults: `3` and `0.75`); see `scholargraph/.env.example`.

---

## 1. Clone and configure

```bash
git clone https://github.com/Qrytics/clearCites.git
cd clearCites/scholargraph
cp .env.example .env
```

Edit `.env` (see keys above). Required for Neo4j: **`NEO4J_PASSWORD`** (default in `.env.example`: `scholargraph`). Compose passes **`OPENALEX_MAILTO`** and **`CROSSREF_MAILTO`** into the **graph_api** container for OpenAlex and tooling.

---

## 2. Start the stack (Docker)

1. **Start Docker Desktop** (Windows/macOS) and wait until the engine is running (`docker version` should show a **Server** section, not only Client).
2. From the directory that contains **`docker-compose.yml`** (`clearCites/scholargraph`):

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Neo4j Browser | http://localhost:7474 |
| Graph API (Swagger UI) | http://localhost:8000/docs |
| Web app | http://localhost:3000 — **[/discover](http://localhost:3000/discover)** (OpenAlex) · **[/explore](http://localhost:3000/explore)** (manual DOI graph) |

Leave this terminal open while you work. Use a **second** terminal for ingest and `curl` examples.

---

## 3. Initialize Neo4j (one time per empty database)

1. Open **http://localhost:7474** and sign in:
   - **Username:** `neo4j`
   - **Password:** the value of **`NEO4J_PASSWORD`** in your `scholargraph/.env` (default in `.env.example`: `scholargraph`).

2. Open the **query editor** (large input at the top). Paste **either** the script below **or** the same text from `scholargraph/db/schema.cypher` (they should match). Run with the play button or Ctrl+Enter.

```cypher
// clearCites – Neo4j constraints and indexes (run once on a fresh database).

CREATE CONSTRAINT paper_doi_unique IF NOT EXISTS
  FOR (p:Paper) REQUIRE p.doi IS UNIQUE;

CREATE CONSTRAINT author_orcid_unique IF NOT EXISTS
  FOR (a:Author) REQUIRE a.orcid IS UNIQUE;

CREATE CONSTRAINT keyword_text_unique IF NOT EXISTS
  FOR (k:Keyword) REQUIRE k.text IS UNIQUE;

CREATE CONSTRAINT funder_name_unique IF NOT EXISTS
  FOR (f:Funder) REQUIRE f.name IS UNIQUE;

CREATE INDEX paper_title_index IF NOT EXISTS
  FOR (p:Paper) ON (p.title);

CREATE INDEX paper_year_index IF NOT EXISTS
  FOR (p:Paper) ON (p.year);

CREATE INDEX author_name_index IF NOT EXISTS
  FOR (a:Author) ON (a.name);

CREATE INDEX paper_openalex_id_index IF NOT EXISTS
  FOR (p:Paper) ON (p.openalex_id);
```

3. **Optional — find papers sharing the same OpenAlex id** (different `doi` keys; review before any manual merge). Same query as `scholargraph/db/dedup_openalex.cypher`:

```cypher
// Papers sharing the same openalex_id but different doi keys (review before merging).

MATCH (p:Paper)
WHERE p.openalex_id IS NOT NULL AND trim(p.openalex_id) <> ""
WITH p.openalex_id AS oa, collect(p.doi) AS dois, count(*) AS n
WHERE n > 1
RETURN oa, n, dois
ORDER BY n DESC;
```

4. **Optional — reset the DB** (wipes all graph data and volumes):

   ```bash
   docker compose down -v
   docker compose up --build
   ```

   Then sign in again and **re-run step 2** (constraints + indexes).

---

## 4. Install Python dependencies (on your host, for ingest + tests)

From the **`clearCites`** directory (repository root containing `pyproject.toml`):

```bash
cd clearCites
python -m pip install -e "."
```

This installs the **`clearcites`** package and the **`clearcites-ingest`** command.

---

## 5. Discover — OpenAlex search → Neo4j → graph (no manual DOI typing)

The **Discover** page (ARXTERM-inspired terminal UI) walks through the flow you described: search OpenAlex, pick a work, choose what kinds of related papers to pull, then **ingest and visualize** in one place.

1. Complete steps **1–3** above (Docker up, Neo4j schema applied).
2. Set **`OPENALEX_MAILTO`** in `scholargraph/.env` (same idea as CrossRef polite pool).
3. Open **http://localhost:3000/discover**.
4. Enter a query, optional filters (year, type, OA, …), click **Run query**.
5. Click a **paper card** to select it (highlighted border).
6. Tick neighborhood modes (**references / cited by / shared authors / OpenAlex concept cluster / related**), set **max works per mode**, then **Ingest & visualize**.  
   The API calls OpenAlex, upserts works into Neo4j via `push_paper`, then embeds the same React Flow graph as `/explore`.

**Entity tabs** — **Works** supports full Discover (search → ingest → graph). **Authors / Institutions / Sources** search the live OpenAlex catalog only (tabs are labeled “catalog” in the UI; no Neo4j ingest yet).

**API** (also in Swagger under **openalex**):

- `GET /openalex/search?q=…&entity=works&…` — proxy search with optional work filters (`year_from`, `year_to`, `work_type`, `min_citations`, `is_oa`, `has_abstract`, `sort_field`, `sort_dir`, `page`, `per_page`). Sort fields are **whitelisted** per entity so OpenAlex does not return opaque `400` errors (works: `relevance_score`, `cited_by_count`, `publication_date`; other entities: `relevance_score`, `cited_by_count`, `works_count`).
- `POST /openalex/explore` — JSON `{ "seed_work_id": "W…", "modes": ["citations_out",…], "limit_per_mode": 25 }` — fetch related works and merge into Neo4j; response includes `seed_canonical_id` for `GET /graph`.

---

## 6. Put papers in the graph manually (optional if you use Discover)

The built-in **`GET /search`** endpoint queries **Neo4j** only. If you are **not** using Discover, ingest papers first so `/search` and `/explore` have data.

**Set Neo4j connection** to match Docker’s published Bolt port (same password as in `.env`):

```bash
# Linux / macOS
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=scholargraph   # or whatever you set in scholargraph/.env

# Windows PowerShell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="scholargraph"
```

**Ingest one paper** (Semantic Scholar metadata):

```bash
clearcites-ingest 10.1038/nature14539
```

**Ingest via CrossRef** (good for funding metadata; set email):

```bash
clearcites-ingest 10.1038/nature14539 --source crossref --mailto you@example.com
```

Repeat for other DOIs if you want a richer neighborhood (citation edges and stubs are created from reference lists).

---

## 7. Search for a paper (Neo4j index)

With the stack running, use the **Graph API** (Swagger at http://localhost:8000/docs or `curl`).

**Full-text style search** (title / abstract text stored in Neo4j):

```bash
curl -s "http://localhost:8000/search?q=attention&limit=5"
```

Response is JSON: each item has a **`doi`**, **`title`**, **`year`**, etc. Pick the **`doi`** you care about.

**Search by keyword node** (from Semantic Scholar “fields of study” ingested as `Keyword` nodes):

```bash
curl -s "http://localhost:8000/search/by-keyword?keyword=biology&limit=5"
```

**Fetch one paper by DOI:**

```bash
curl -s "http://localhost:8000/papers/10.1038%2Fnature14539"
```

(Encode `/` in the path as `%2F`.)

---

## 8. Visualize related papers (web UI)

**After Discover:** the graph is already on `/discover` once ingest succeeds. You can also open **http://localhost:3000/explore** with the returned canonical id (DOI or `openalex:W…`).

**Manual path:**

1. Open **http://localhost:3000/explore** (or **Explore graph** on the home page).
2. Paste the **DOI** you found (e.g. from `/search`), choose **depth** (1–3 citation hops), and toggle:
   - **Citations** — papers linked by `CITES` (direction: source **cites** target).
   - **Authors** — who wrote each paper in view.
   - **Co-authors** — other papers that share an author with your seed.
   - **Keywords** — `HAS_KEYWORD` links into keyword nodes.
3. Click **Load graph**. Purple nodes are papers; orange are authors; teal are keywords. Click a **paper** to open the detail sidebar. The canvas uses a **left-to-right Dagre layout** (deterministic per load) with **Fit view** after layout and an optional **Full screen** control in the graph toolbar.

The page calls **`GET /graph`** with an `expand` query string. Example equivalent:

```bash
curl -s "http://localhost:8000/graph?doi=10.1038%2Fnature14539&depth=2&expand=citations,authors,coauthors,keywords"
```

**Browser-only alternative:** in Neo4j Browser, run Cypher that `MATCH`es your seed and expands `CITES` / `WROTE` / `HAS_KEYWORD`, then open the **graph** view on the result.

---

## 9. Troubleshooting

| Issue | What to try |
|--------|----------------|
| `dockerDesktopLinuxEngine` / cannot connect to Docker | Start **Docker Desktop** and wait until `docker version` shows **Server**. |
| Neo4j password rejected | Use **`NEO4J_PASSWORD`** from `scholargraph/.env`. If you changed it after first run, old volumes may keep the old password — run `docker compose down -v` and start again (data loss). |
| Empty **`GET /search`** or empty graph on **/explore** | Data must exist in Neo4j: use **/discover → Ingest & visualize**, or **`clearcites-ingest`**, then reload. |
| OpenAlex / **Discover** errors (429, 502, timeouts) | Set **`OPENALEX_MAILTO`** in `.env`; optional **`OPENALEX_MAX_RETRIES`** / **`OPENALEX_RETRY_BACKOFF_SEC`**; reduce **max works per mode**; read the JSON **`detail`** message from the API (also shown in the Discover UI). |
| Web cannot reach API from the browser | **`NEXT_PUBLIC_API_URL=http://localhost:8000`** in `.env` when using `http://localhost:3000`. Custom hosts need CORS updates in `services/graph_api/main.py`. |

---

## Project layout

```
scholargraph/
├── data_pipeline/          # Semantic Scholar, CrossRef, OpenAlex clients; parser; graph_pusher; openalex_subgraph
├── tools/
│   └── ingest_doi.py       # `clearcites-ingest` (pyproject.toml)
├── services/
│   ├── graph_api/          # FastAPI: /search, /graph, /openalex/*, CORS for localhost
│   └── ai_summarizer/
├── web/app/
│   ├── discover/           # OpenAlex terminal UI + ingest + embedded graph
│   └── explore/            # Manual DOI + graph toggles
├── db/
│   ├── schema.cypher
│   └── dedup_openalex.cypher   # optional: find shared openalex_id for manual merge
├── docker-compose.yml
└── .env.example
```

More READMEs:

- [scholargraph/README.md](scholargraph/README.md) — compose, ports, paths under `scholargraph/`
- [scholargraph/web/README.md](scholargraph/web/README.md) — optional local Node / `npm run dev`
- [scholargraph/services/graph_api/README.md](scholargraph/services/graph_api/README.md) — API env vars and Swagger

---

## Why clearCites?

- **Visualize relationships** — citations, shared authorship, and keywords in one view.
- **Transparency** — funders and metadata from CrossRef where available.
- **API-first** — build your own UI or scripts on top of the same endpoints.

---

## Tech stack

| Layer | Choice |
|--------|--------|
| Database | Neo4j |
| API | Python 3.11, FastAPI |
| Web | Next.js, React Flow |
| ML helpers | scikit-learn, numpy (`/ai/*`: extractive summary + TF-IDF relationship hint; no external LLM API) |
| External data | Semantic Scholar, CrossRef, **OpenAlex** (Discover + `/openalex/*`) |

---

## API quick reference

Interactive docs: **http://localhost:8000/docs** when the stack is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/papers/{doi}` | Paper with authors, keywords, funders |
| `GET` | `/papers/{doi}/citations` | Papers cited by this paper (depth 1–3) |
| `GET` | `/papers/{doi}/cited-by` | Papers that cite this paper |
| `GET` | `/papers/{doi}/pedigree` | Citation ancestors |
| `GET` | `/graph?doi=…&depth=…&expand=…` | JSON graph for the explorer (`expand`: `citations`, `authors`, `coauthors`, `keywords`) |
| `GET` | `/openalex/search?…` | OpenAlex proxy search (see Swagger; powers **/discover**) |
| `POST` | `/openalex/explore` | Ingest seed + related works from OpenAlex into Neo4j |
| `GET` | `/search?q=…` | Text search on stored title/abstract |
| `GET` | `/search/by-keyword?keyword=…` | Papers linked to keyword nodes |
| `POST` | `/ai/summary` | Extractive summary (TF-IDF sentence scoring on the abstract) |
| `POST` | `/ai/relationship` | Heuristic relationship label + cosine similarity on two abstracts |

---

## Running tests

From **`clearCites`** (repo root):

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

---

## Continuous integration

GitHub Actions on **`main`** (see `.github/workflows/ci.yml`):

- **`test`** — editable install + `pytest` (graph API with mocked Neo4j, parser, OpenAlex routes with mocked HTTP client).
- **`docker-images`** — `docker compose build graph_api web` from `scholargraph/` so API and web Dockerfiles stay buildable on a clean Linux runner.

---

## Neo4j schema (concepts)

**Node labels:** `Paper`, `Author`, `Keyword`, `Funder`.

**Paper properties:** the ingest path sets **`openalex_id`** when an OpenAlex work id is known (including DOI-keyed papers). `db/schema.cypher` defines **`paper_openalex_id_index`**. Older databases: re-run the new index line from the current schema file (safe `IF NOT EXISTS`).

**Relationship types:** `WROTE`, `CITES`, `HAS_KEYWORD`, `FUNDED_BY`, and optional typed edges `VALIDATES`, `BUILDS_ON`, `CHALLENGES` when you add them via the API or pipeline.

**Identity / deduplication:** one primary key per work — normalized DOI when available from OpenAlex, otherwise `openalex:W…` (`canonical_paper_key_from_work` in `data_pipeline/parser.py`). The same real-world paper can still appear twice if ingested under different keys; **`scholargraph/db/dedup_openalex.cypher`** lists collisions by shared `openalex_id`. Merging nodes (moving edges, deleting extras) remains a manual Cypher step.

---

## Current limitations (handoff)

These are **known** gaps, not setup mistakes:

- **Discover graph ingest** is only for **Works**; other entity tabs are OpenAlex catalog search only.
- **GitHub Pages** ships a **static** site only — no bundled Neo4j/API (see the note at the top of this README).
- **Graph layout** uses a deterministic **Dagre** layer in the web app (not physics-based persistence in Neo4j).
- **Tests** mock Neo4j and OpenAlex HTTP; they do not hit the live `api.openalex.org`.
- **`plain_summary` in the web UI** is only shown when the API provides it; default graph payloads may omit it.

---

## License

MIT (see repository files).
