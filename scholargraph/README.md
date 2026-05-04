# clearCites stack (`scholargraph/`)

This folder is the **runnable stack**: Neo4j, the graph API, the Next.js web app (home, Discover, Explore), and the data pipeline.

The **full walkthrough** (dependencies, Docker, schema, Discover, `/explore`, ingest) is in the repository root: **[../README.md](../README.md)**.

---

## Quick orientation

| Path | Role |
|------|------|
| `docker-compose.yml` | Start Neo4j + API + web (`docker compose up --build`) |
| `.env` / `.env.example` | Passwords and optional API keys (copy example to `.env`) |
| `db/schema.cypher` | Run once in Neo4j Browser to create constraints/indexes |
| `db/dedup_openalex.cypher` | Optional helper script to spot papers sharing the same `openalex_id` (manual merge in Cypher) |
| `web/` | Next.js app — home, **`/discover`** (OpenAlex), **`/explore`** (DOI graph) |
| `services/graph_api/` | FastAPI — `/search`, `/graph`, `/papers/...`, `/openalex/*`, `/ai/*` |
| `data_pipeline/` | `clearcites-ingest` uses these modules to write to Neo4j |
| `tools/ingest_doi.py` | Source for the `clearcites-ingest` CLI (installed from repo root) |

---

## Commands you run from *this* directory

```bash
# Start everything
docker compose up --build

# Tear down and delete graph volumes (full DB reset)
docker compose down -v
```

Commands you run from **`clearCites/`** (parent, where `pyproject.toml` lives):

```bash
python -m pip install -e "."
clearcites-ingest 10.1038/nature14539
```

---

## URLs (default ports)

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 — **/discover** (OpenAlex terminal) · **/explore** (manual DOI graph) |
| API docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

---

## Need help?

See **[Troubleshooting](../README.md#9-troubleshooting)** in the main README (Docker engine, Neo4j password, empty graph).
