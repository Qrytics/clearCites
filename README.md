# clearCites

**Live site:** [https://qrytics.github.io/clearCites/](https://qrytics.github.io/clearCites/) (marketing page; the interactive graph needs the stack below.)

clearCites maps research papers as a graph: **papers** as nodes, **citations**, **authors**, **keywords**, and **funders** as relationships. This README walks you from **installing dependencies** through **searching for a paper** and **visualizing everything related to it**.

**First-time path**

1. **§1** — Clone the repo, create `scholargraph/.env`, and complete **§1.3** (check every row; for Discover you need at least **`NEO4J_PASSWORD`** and **`OPENALEX_MAILTO`** as described there).
2. **§2** — Start Docker Compose.
3. **§3** — Log into Neo4j Browser and run the schema Cypher (**§3** steps **1** and **2** only).  
   **§3** steps **3** and **4** (dedup query, full DB reset) are **optional** and are not part of a minimal first run.

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

All environment variables live in **`scholargraph/.env`**. The line-by-line checklist is in **§1.3** (not summarized here, so nothing is easy to miss).

---

## 1. Clone and configure

### 1.1 Clone the repository

```bash
git clone https://github.com/Qrytics/clearCites.git
cd clearCites/scholargraph
```

Stay in **`clearCites/scholargraph`** for **§1.2**, **§2**, and **§3** (that directory contains `docker-compose.yml` and `.env`).

### 1.2 Create `.env` from the example

```bash
cp .env.example .env
```

This creates **`scholargraph/.env`**. Open that file in a text editor before continuing.

### 1.3 Edit `scholargraph/.env` — go through every row

Work **top to bottom** so you do not skip a line. After any change to `.env`, restart the stack (**§2**) so containers pick up new values.

| Order | Variable | Required? | What to put |
|:-----:|----------|-----------|-------------|
| 1 | **`NEO4J_PASSWORD`** | **Yes** | Pick a password. The **Neo4j** and **graph_api** services read this from `.env` when Compose starts. In **§3**, you sign into Neo4j Browser as user **`neo4j`** with **this same password**. |
| 2 | **`NEO4J_USER`** | Usually leave default | Keep **`neo4j`** unless you know you changed the DB user. |
| 3 | **`NEO4J_URI`** | **For CLI ingest on your host** | Use **`bolt://localhost:7687`** when Neo4j is running in Docker with port **7687** published (this repo’s default). That value is for **`clearcites-ingest`** and other tools on your machine. The **graph_api** container uses Compose’s own Bolt URL (`bolt://neo4j:7687`); you do not set that inside `.env` for the API. |
| 4 | **`OPENALEX_MAILTO`** | **Yes if you use Discover or `/openalex/*`** | Set to a **real email** you control (e.g. `you@university.edu`). OpenAlex uses it for the [polite pool](https://docs.openalex.org/how-to-use/api). If this is empty **and** `CROSSREF_MAILTO` is empty, Discover often fails with HTTP **429**. You can skip this only if you will **not** use Discover/OpenAlex (e.g. Explore-only with data already in Neo4j). |
| 5 | **`CROSSREF_MAILTO`** | Optional | Use for [CrossRef polite pool](https://github.com/CrossRef/rest-api-doc#good-manners--more-reliable-service) when running **`clearcites-ingest --source crossref`**. The API also uses it as a **fallback** mailto for OpenAlex when `OPENALEX_MAILTO` is unset. |
| 6 | **`SEMANTIC_SCHOLAR_API_KEY`** | Optional | Leave empty for anonymous Semantic Scholar; set a key for higher rate limits on **`clearcites-ingest`** (Semantic Scholar source). |
| 7 | **`NEXT_PUBLIC_API_URL`** | **Yes if you run Next.js on the host** | Example: **`http://localhost:8000`**. With **this repo’s `docker compose`**, the **web** service is already given that URL in `docker-compose.yml`, so local Docker browsing works even if you do not customize this line—set it anyway if you later run **`npm run dev`** outside Docker. |
| 8 | **`NEXT_PUBLIC_BASE_PATH`** | **Usually leave empty** | For **`http://localhost:3000/`** at the **site root** (home, `/discover`, `/explore`), leave this **empty** or unset. **`docker-compose.yml`** sets **`NEXT_PUBLIC_BASE_PATH=""`** on the **web** container so local Docker always matches that. Use **`/clearCites`** only if you intentionally want the same URL layout as [GitHub Pages](https://qrytics.github.io/clearCites/) while developing on the host (then open **`http://localhost:3000/clearCites/…`**). The Pages workflow sets this path in CI only. |
| 9 | **`OPENALEX_MAX_RETRIES`**, **`OPENALEX_RETRY_BACKOFF_SEC`** | Optional | Uncomment in `.env.example` to tune retries. The **default** `docker-compose.yml` does **not** pass these into **graph_api**, so the running API uses code defaults (**`3`** retries, **`0.75`** s backoff) unless you add the variables to **`graph_api.environment`** in Compose or run the API outside Docker. |

**Compose note:** **`OPENALEX_MAILTO`** and **`CROSSREF_MAILTO`** from your `.env` are injected into the **graph_api** container automatically (`docker-compose.yml`). **`SEMANTIC_SCHOLAR_API_KEY`** is as well (for any server-side use). The **web** service gets **`NEXT_PUBLIC_API_URL`**, **`NEXT_PUBLIC_BASE_PATH`**, the **`dev:docker`** command, and volumes from the same file—see **§2.1**.

**Password caveat:** If you change **`NEO4J_PASSWORD`** after Neo4j has already been created, the old password may still live in the Docker volume. Use **`docker compose down -v`** (see **§3.4**) only if you intend to wipe data and start fresh.

When **§1.3** is done, continue to **§2**.

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

### 2.1 Web app in Docker (bind mount, dev server, `.next` volume)

This matters if you change the frontend or hit odd Next.js errors.

| Mechanism | Why it exists |
|-------------|----------------|
| **`build.target: deps`** (Compose) | The Dockerfile’s `runner` stage sets **`NODE_ENV=production`**, which makes **`next dev`** skip its CSS loader chain and you see **`Module parse failed`** on `.css`. Compose targets the **`deps`** stage (just `node_modules`) so the dev server can apply normal loaders. |
| **`NODE_ENV=development`** (Compose) | Belt + suspenders for the same problem—**`next dev`** must run with the development env, regardless of base image defaults. |
| **`./web:/app` bind mount** | Your edited files under **`scholargraph/web/`** show up in the container immediately. |
| **`npm run dev:docker`** (see `docker-compose.yml`) | A production **`next start`** would need a **`.next`** build inside `/app`, but the bind mount hides the image’s build. The dev server compiles on demand instead. |
| **Named volume `clearcites_web_next` → `/app/.next`** | Next’s cache and dev output live **outside** the bind mount. Without this, a **`web/.next`** folder on your host (empty or stale) could break the app with missing **`required-server-files.json`** or 500s. |
| **`NEXT_PUBLIC_BASE_PATH=""` in Compose** | Serves the app at **`/`** (not under **`/clearCites`**). GitHub Pages still uses **`/clearCites`** via CI only. |
| **Discover global CSS** | Import global styles only from **`web/app/layout.tsx`** (Discover uses **`./discover/discover.css`**). Nested layouts must not import global `.css` files. |
| **`output: "export"`** | Static export is **off** during **`next dev`** (Docker and local). It is turned on **only** when **`NEXT_STATIC_EXPORT=true`** (GitHub Pages sets this in **`.github/workflows/pages.yml`**). Leaving export always on breaks the dev server’s CSS pipeline (“Module parse failed” on `.css`). |

**If you need a clean Next cache:** `docker compose down` then remove the volume explicitly, e.g. `docker volume rm scholargraph_clearcites_web_next` (prefix may match your project folder name), then **`docker compose up --build`**. Optionally delete **`scholargraph/web/.next`** on the host so nothing stale shadows the mount (Compose’s volume normally overrides that path in the container anyway).

---

## 3. Initialize Neo4j (one time per empty database)

**Required:** steps **1** and **2** below. **Optional:** steps **3** (dedup) and **4** (wipe volumes).

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

1. Complete **§2** (Docker up) and **§3** steps **1** and **2** (Neo4j login + schema Cypher).
2. Confirm **`OPENALEX_MAILTO`** is set as in **§1.3** (or rely on **`CROSSREF_MAILTO`** as the API’s fallback mailto). If you just edited `.env`, restart Compose (**§2**) before using Discover.
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
| **`localhost:3000` won’t load** or `clearcites-web` exits immediately | With Docker, the **`web`** service must not run plain `next start` while `./web` is bind-mounted (there is no `.next` on the host). Compose should use **`npm run dev:docker`** (see `scholargraph/docker-compose.yml`). Run `docker compose up --build` again from `scholargraph/`. |
| **Next.js shows 404** for `/` or `/discover` at port 3000 | Local dev uses **`NEXT_PUBLIC_BASE_PATH=""`** (root). If you still see 404s, ensure you are not using an old image: rebuild the **web** service. The GitHub Pages site lives under **`/clearCites`** only in CI (`pages.yml` sets that env). |
| **500 on `/discover`** or **`Module parse failed`** on **`discover.css`** | The dev server is running with **`NODE_ENV=production`** (warning: *“non-standard NODE_ENV value”*). Ensure **`docker-compose.yml`** has **`build.target: deps`** **and** **`NODE_ENV=development`** for the **web** service (see **§2.1**), then **`docker compose up --build`** so the right image is rebuilt. Also keep global CSS imports inside **`web/app/layout.tsx`** only, and leave **`output: "export"`** gated on **`NEXT_STATIC_EXPORT`**. |
| **`ENOENT` … `required-server-files.json`** under **`clearcites-web`** | Usually a broken or host-shadowed **`.next`**. Ensure **`docker-compose.yml`** still mounts the **`clearcites_web_next`** volume on **`/app/.next`**, then **`docker compose down`**, remove that Docker volume if needed, and **`docker compose up --build`**. Delete **`scholargraph/web/.next`** on the host if it exists. |

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
