# Graph API (`services/graph_api`)

FastAPI service: paper reads, **`/search`**, **`/graph`** (React Flow), **`/openalex/*`** (Discover), and **`/ai/*`** (extractive summary + abstract similarity helper—no external LLM).

**Run with Docker:** from `scholargraph/`, `docker compose up --build`. This service listens on **http://localhost:8000**. Open **http://localhost:8000/docs** for Swagger.

---

## Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/papers/{doi}` | Paper node + authors / keywords / funders. |
| `GET` | `/papers/{doi}/citations` | Papers this DOI cites (depth 1–3). |
| `GET` | `/papers/{doi}/cited-by` | Papers that cite this DOI. |
| `GET` | `/papers/{doi}/pedigree` | Citation ancestors. |
| `GET` | `/search?q=…` | Title/abstract substring search in Neo4j. |
| `GET` | `/search/by-keyword?keyword=…` | Papers linked to keyword nodes. |
| `GET` | `/authors/{name}/papers` | Papers by author (substring match). |
| `GET` | `/graph?doi=…&depth=…&expand=…` | React Flow nodes/edges (`expand` = `citations,authors,coauthors,keywords`). |
| `GET` | `/openalex/search?q=…&entity=works\|authors\|institutions\|sources&…` | OpenAlex proxy (filters + whitelisted sort). |
| `POST` | `/openalex/explore` | `{ seed_work_id, modes, limit_per_mode }` — fetch + ingest a work neighborhood; returns `seed_canonical_id`. |
| `POST` | `/ai/summary` | TF-IDF extractive summary of a paper abstract. |
| `POST` | `/ai/relationship` | Cosine similarity + heuristic label between two abstracts. |

---

## Environment (set by Compose or manually)

- `NEO4J_URI` — inside Compose use `bolt://neo4j:7687`; on the host use `bolt://localhost:7687`.
- `NEO4J_USER`, `NEO4J_PASSWORD` — must match Neo4j.
- `OPENALEX_MAILTO` or `CROSSREF_MAILTO` — passed through for OpenAlex polite pool (Discover).
- `OPENALEX_MAX_RETRIES` (default `3`), `OPENALEX_RETRY_BACKOFF_SEC` (default `0.75`) — retries for transient OpenAlex HTTP statuses (see `data_pipeline/api_clients/openalex_http.py`).
- `SEMANTIC_SCHOLAR_API_KEY` — optional; higher rate limits for Semantic Scholar ingest paths.

---

## Implementation notes

- **Sort whitelist** (`data_pipeline/openalex_sort.py`) restricts `sort_field` per entity so OpenAlex does not return opaque `400`s. Works support `relevance_score`, `cited_by_count`, `publication_date`; other entities support `relevance_score`, `cited_by_count`, `works_count`. `relevance_score` is only sent when a `search` query is present.
- **Retries / errors** (`data_pipeline/api_clients/openalex_http.py`) — exponential backoff on `429`/`502`/`503`, JSON `detail` text shaped via `openalex_http_detail()` so the Discover UI shows a useful message.
- **Identity** (`data_pipeline/parser.py:canonical_paper_key_from_work`) — DOI when present, else `openalex:W…`. `graph_pusher.push_paper` always writes `openalex_id` when known so the dedup query in `db/dedup_openalex.cypher` can find collisions.
- **Tests** — `tests/test_graph_api.py` covers `/papers`, `/search`, `/graph`, and `/ai/*` smoke; `tests/test_openalex_routes.py` covers `/openalex/search` and `/openalex/explore` with the OpenAlex client + ingest function patched (no live HTTP). Shared `mock_neo4j` fixture lives in `tests/conftest.py`.

---

**Typical flows:** use **`/discover`** in the web app with **`/openalex/*`**, or ingest with **`clearcites-ingest`** (see [root README](../../../README.md)), then **`GET /search?q=...`** and **`/explore`** / **`GET /graph?doi=...&expand=citations,authors,coauthors,keywords`**.
