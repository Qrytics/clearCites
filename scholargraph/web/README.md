# Web app (`scholargraph/web`)

Next.js front end for clearCites: marketing home page and **`/explore`** (React Flow graph fed by the graph API).

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
| `/explore` | Enter a DOI, load citation + author + keyword graph |

---

## Production / GitHub Pages

The GitHub Actions workflow may build a static export of this app for Pages. The **live explorer** needs a running **Graph API** and **Neo4j** (or a hosted backend); use **Docker locally** for the full experience.
