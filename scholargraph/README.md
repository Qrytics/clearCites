# clearCites stack (`scholargraph/`)

This folder is the **runnable stack**: Neo4j, the graph API, the Next.js web app (home, Discover, Explore), and the data pipeline.

The **full walkthrough** (dependencies, Docker, schema, Discover, `/explore`, ingest) is in the repository root: **[../README.md](../README.md)**.

---

## Quick orientation

| Path | Role |
|------|------|
| `docker-compose.yml` | Start Neo4j + API + web (`docker compose up --build`). **Web:** bind-mount **`./web` → `/app`**, build the **`deps`** Dockerfile stage, run **`npm run dev:docker`** with **`NODE_ENV=development`**, set **`NEXT_PUBLIC_BASE_PATH=""`**, and keep Next’s output on the Docker volume **`clearcites_web_next:/app/.next`** (see root README **§2.1**). |
| `.env` / `.env.example` | Passwords and optional API keys (copy example to `.env`); see root README **§1.3**. |
| `db/schema.cypher` | Run once in Neo4j Browser to create constraints/indexes (incl. `paper_openalex_id_index`). |
| `db/dedup_openalex.cypher` | Optional helper to spot papers sharing the same `openalex_id` across DOI keys (manual merge in Cypher). |
| `web/` | Next.js app — home, **`/discover`** (OpenAlex), **`/explore`** (DOI / `openalex:W…` graph). Both pages share the **`SCHOLARGRAPH`** header. |
| `services/graph_api/` | FastAPI — `/papers`, `/search`, `/graph`, `/openalex/*`, `/ai/*`. Mounts **`ai_summarizer.router`** for the AI endpoints. |
| `services/ai_summarizer/` | TF-IDF extractive summary + abstract similarity (no external LLM). |
| `data_pipeline/` | OpenAlex / Semantic Scholar / CrossRef clients, parser, graph_pusher, OpenAlex subgraph ingest. |
| `tools/ingest_doi.py` | Source for the `clearcites-ingest` CLI (installed from repo root). |

---

## Commands you run from *this* directory

```bash
# Start everything
docker compose up --build

# Tear down (keep data)
docker compose down

# Tear down and delete graph + Next-cache volumes (full reset)
docker compose down -v
```

Commands you run from **`clearCites/`** (parent, where `pyproject.toml` lives):

```bash
python -m pip install -e "."
clearcites-ingest 10.1038/nature14539
python -m pytest                      # mock-only tests; no Docker required
```

---

## URLs (default ports)

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 — **/discover** (OpenAlex terminal) · **/explore** (manual DOI / `openalex:W…` graph) |
| API docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

---

## Web container (quick reference)

- **Do not** switch the **web** service to **`next start`** while **`./web`** is bind-mounted unless you also remove the mount and ship a built **`.next`** — see root **§2.1**.
- **Global CSS:** import only from **`web/app/layout.tsx`** (Discover styles: **`./discover/discover.css`**). **`output: "export"`** is for Pages CI only (**`NEXT_STATIC_EXPORT`**); do not enable it for local **`next dev`**.
- **`GraphCanvas` embed contract:** wrap it in a **`position: relative`** parent with a **definite height** (fixed `height` or `flex: 1` inside a flex column). The component fills via **`position: absolute; inset: 0`**.
- **Reset Next cache in Docker:** `docker compose down`, then `docker volume rm <project>_clearcites_web_next` (volume name prefix matches the Compose project directory), then `docker compose up --build`.

---

## Need help?

See **[Troubleshooting](../README.md#9-troubleshooting)** in the main README (Docker engine, Neo4j password, empty graph, Next **404**/**500**, **`.next`** volume, OpenAlex 429).
