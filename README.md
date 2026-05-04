# clearCites

**Live site:** [https://qrytics.github.io/clearCites/](https://qrytics.github.io/clearCites/) (marketing page; the interactive graph needs the stack below.)

clearCites maps research papers as a graph: **papers** as nodes, **citations**, **authors**, **keywords**, and **funders** as relationships. This README walks you from **installing dependencies** through **searching for a paper** and **visualizing everything related to it**.

---

## What you need installed

| Requirement | Used for |
|-------------|----------|
| **Git** | Clone the repository |
| **Docker Desktop** (or another Docker engine) + **Compose v2** | Neo4j, FastAPI graph API, and Next.js web app in one command |
| **Python 3.11+** and **pip** | Ingest papers into Neo4j from your machine (`clearcites-ingest`), and run tests |
| **Node.js 20+** (optional) | Only if you run the frontend with `npm run dev` *outside* Docker |

Optional: a **Semantic Scholar API key** in `.env` as `SEMANTIC_SCHOLAR_API_KEY` for higher rate limits when ingesting. CrossRef works without a key; set `CROSSREF_MAILTO` in `.env` for their [polite pool](https://github.com/CrossRef/rest-api-doc#good-manners--more-reliable-service).

---

## 1. Clone and configure

```bash
git clone https://github.com/Qrytics/clearCites.git
cd clearCites/scholargraph
cp .env.example .env
```

Edit `.env`:

- **`NEO4J_PASSWORD`** — used by Docker **and** by Neo4j Browser; the default in `.env.example` is `scholargraph` (not `clearcites`).
- **`SEMANTIC_SCHOLAR_API_KEY`** — optional.
- **`CROSSREF_MAILTO`** — your email when using CrossRef from the ingest CLI.

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
| Web app | http://localhost:3000 |

Leave this terminal open while you work. Use a **second** terminal for ingest and `curl` examples.

---

## 3. Initialize Neo4j (one time per empty database)

1. Open **http://localhost:7474** and sign in:
   - **Username:** `neo4j`
   - **Password:** the value of **`NEO4J_PASSWORD`** in your `scholargraph/.env` (default in `.env.example`: `scholargraph`).

2. Paste the **contents** of `scholargraph/db/schema.cypher` into the **query editor** (the large input at the top), then run it (play button or Ctrl+Enter).  
   Do **not** type the filename alone; Neo4j expects Cypher text.

3. **Optional — reset the DB** (wipes all graph data and volumes):

   ```bash
   docker compose down -v
   docker compose up --build
   ```

   Then sign in again and re-run `schema.cypher`.

---

## 4. Install Python dependencies (on your host, for ingest + tests)

From the **`clearCites`** directory (repository root containing `pyproject.toml`):

```bash
cd clearCites
python -m pip install -e "."
```

This installs the **`clearcites`** package and the **`clearcites-ingest`** command.

---

## 5. Put papers in the graph (required before search/visualize)

The graph API searches **Neo4j**, not the live web. Ingest at least one paper (and ideally a few referenced works) so `/search` and `/explore` have data.

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

## 6. Search for a paper

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

## 7. Visualize related papers (web UI)

1. Open **http://localhost:3000/explore** (or click **Explore graph** on the home page).
2. Paste the **DOI** you found (e.g. from `/search`), choose **depth** (1–3 citation hops), and toggle:
   - **Citations** — papers linked by `CITES` (direction: source **cites** target).
   - **Authors** — who wrote each paper in view.
   - **Co-authors** — other papers that share an author with your seed.
   - **Keywords** — `HAS_KEYWORD` links into keyword nodes.
3. Click **Load graph**. Purple nodes are papers; orange are authors; teal are keywords. Click a **paper** to open the detail sidebar.

The page calls **`GET /graph`** with an `expand` query string. Example equivalent:

```bash
curl -s "http://localhost:8000/graph?doi=10.1038%2Fnature14539&depth=2&expand=citations,authors,coauthors,keywords"
```

**Browser-only alternative:** in Neo4j Browser, run Cypher that `MATCH`es your seed and expands `CITES` / `WROTE` / `HAS_KEYWORD`, then open the **graph** view on the result.

---

## 8. Troubleshooting

| Issue | What to try |
|--------|----------------|
| `dockerDesktopLinuxEngine` / cannot connect to Docker | Start **Docker Desktop** and wait until `docker version` shows **Server**. |
| Neo4j password rejected | Use **`NEO4J_PASSWORD`** from `scholargraph/.env`. If you changed it after first run, old volumes may keep the old password — run `docker compose down -v` and start again (data loss). |
| Empty search or empty graph | Ingest papers with **`clearcites-ingest`** while Neo4j is up. |
| Web cannot reach API from the browser | With Docker Compose defaults, **`NEXT_PUBLIC_API_URL=http://localhost:8000`** in `.env` is correct when you open the site at `http://localhost:3000`. |

---

## Project layout

```
scholargraph/
├── data_pipeline/          # API clients, parser, graph_pusher
├── tools/
│   └── ingest_doi.py       # CLI entry: `clearcites-ingest` (see pyproject.toml)
├── services/
│   ├── graph_api/          # FastAPI (search, /graph, papers, …)
│   └── ai_summarizer/
├── web/                    # Next.js (home + /explore)
├── db/schema.cypher
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
| ML helpers | scikit-learn, numpy (see `ai_summarizer`) |
| External data | Semantic Scholar, CrossRef |

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
| `GET` | `/search?q=…` | Text search on stored title/abstract |
| `GET` | `/search/by-keyword?keyword=…` | Papers linked to keyword nodes |
| `POST` | `/ai/summary` | Plain-language summary (when wired) |
| `POST` | `/ai/relationship` | Relationship hint between two abstracts (when wired) |

---

## Running tests

From **`clearCites`** (repo root):

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

---

## Neo4j schema (concepts)

**Node labels:** `Paper`, `Author`, `Keyword`, `Funder`.

**Relationship types:** `WROTE`, `CITES`, `HAS_KEYWORD`, `FUNDED_BY`, and optional typed edges `VALIDATES`, `BUILDS_ON`, `CHALLENGES` when you add them via the API or pipeline.

---

## License

MIT (see repository files).
