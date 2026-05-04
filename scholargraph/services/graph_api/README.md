# Graph API (`services/graph_api`)

FastAPI service: paper CRUD-style reads, **`/search`**, **`/graph`** (for the React Flow explorer), and related endpoints.

**Run with Docker:** from `scholargraph/`, `docker compose up --build` — this service listens on **http://localhost:8000**. Open **http://localhost:8000/docs** for Swagger.

**Environment (set by Compose or manually):**

- `NEO4J_URI` — inside Compose use `bolt://neo4j:7687`; on the host use `bolt://localhost:7687`.
- `NEO4J_USER`, `NEO4J_PASSWORD` — must match Neo4j.

**Typical flow:** ingest papers with **`clearcites-ingest`** (see [root README](../../../README.md)), then call **`GET /search?q=...`** to find a DOI, then open **`/explore`** on the web app or call **`GET /graph?doi=...&expand=citations,authors,coauthors,keywords`**.
