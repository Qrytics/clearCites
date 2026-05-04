# Web app (`scholargraph/web`)

Next.js front end for clearCites: marketing **`/`**, **`/discover`** (OpenAlex terminal + ingest + embedded graph), and **`/explore`** (DOI-driven graph from the API).

End-to-end setup (Docker, ingest, search, visualize) is documented in **[../../README.md](../../README.md)**.

---

## When do you need Node?

- **Docker Compose** builds and runs this app for you — no local Node required.
- Install **Node.js 20+** only if you want to develop the UI on the host:

  ```bash
  cd scholargraph/web
  npm install
  npm run dev
  ```

  Point the app at your API with **`NEXT_PUBLIC_API_URL`** (e.g. `http://localhost:8000` in `.env` under `scholargraph/`).

---

## Useful routes

| Route | Purpose |
|-------|---------|
| `/` | Landing / feature overview |
| `/discover` | OpenAlex search, neighborhood ingest into Neo4j, embedded graph |
| `/explore` | Enter a DOI, load citation + author + keyword graph (needs API) |

---

## Production / GitHub Pages

The GitHub Actions workflow may build a static export of this app for Pages. The **live explorer** needs a running **Graph API** and **Neo4j** (or a hosted backend); use **Docker locally** for the full experience.

The **Dockerfile** uses `npm install` (not `npm ci`) so CI stays green when `package.json` gains dependencies before `package-lock.json` is committed; for stricter reproducibility, run `npm install` locally and commit an updated lockfile when you change dependencies.

**Graph canvas:** `/explore` and embedded Discover graphs use **Dagre** for layout (see `lib/graphLayout.ts`) plus a **Full screen** control on the graph toolbar.
