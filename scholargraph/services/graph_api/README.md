# Graph API (`services/graph_api`)

FastAPI service: paper reads, **`/search`**, **`/graph`** (React Flow), **`/openalex/*`** (Discover), and **`/ai/*`** (extractive summary + abstract similarity helper—no external LLM).

**Run with Docker:** from `scholargraph/`, `docker compose up --build` — this service listens on **http://localhost:8000**. Open **http://localhost:8000/docs** for Swagger.

**Environment (set by Compose or manually):**

- `NEO4J_URI` — inside Compose use `bolt://neo4j:7687`; on the host use `bolt://localhost:7687`.
- `NEO4J_USER`, `NEO4J_PASSWORD` — must match Neo4j.
- `OPENALEX_MAILTO` or `CROSSREF_MAILTO` — passed through for OpenAlex polite pool (Discover).
- `OPENALEX_MAX_RETRIES` (default `3`), `OPENALEX_RETRY_BACKOFF_SEC` (default `0.75`) — retries for transient OpenAlex HTTP statuses (see `data_pipeline/api_clients/openalex_http.py`).

**Typical flows:** use **`/discover`** in the web app with **`/openalex/*`**, or ingest with **`clearcites-ingest`** (see [root README](../../../README.md)), then **`GET /search?q=...`** and **`/explore`** / **`GET /graph?doi=...&expand=citations,authors,coauthors,keywords`**.
