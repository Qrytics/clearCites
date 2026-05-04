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

  Point the app at your API with **`NEXT_PUBLIC_API_URL`** (e.g. `http://localhost:8000` in `.env` under `scholargraph/`). For URLs at **`http://localhost:3000/`** (not under **`/clearCites`**), leave **`NEXT_PUBLIC_BASE_PATH`** empty (Compose does this for Docker).

---

## Next.js conventions in this repo

- **Global CSS** (plain **`.css`** files): import **only** from **`app/layout.tsx`**. Route-level **`app/discover/layout.tsx`** must **not** import global stylesheets—Next will mis-handle them and you can see **“Module parse failed”** on CSS. Colocate files under **`app/discover/`** but import **`./discover/discover.css`** from the root layout.
- **Static export vs dev:** **`next.config.mjs`** enables **`output: "export"`** only when **`NEXT_STATIC_EXPORT=true`**. GitHub Pages sets **`NEXT_STATIC_EXPORT`** in **`.github/workflows/pages.yml`** for **`npm run build`** only.
- **`NODE_ENV` in Docker:** the **`runner`** stage of **`Dockerfile`** sets **`NODE_ENV=production`** for prod images. Compose builds the **`deps`** stage instead and runs **`next dev`** with **`NODE_ENV=development`**—running `next dev` against `NODE_ENV=production` makes the CSS loader chain silently skip global `.css`, producing **“Module parse failed”** on `discover.css`.
- **GitHub Pages:** CI sets **`NEXT_PUBLIC_BASE_PATH=/clearCites`** and **`NEXT_STATIC_EXPORT=true`** (see `../../.github/workflows/pages.yml`). Local Docker forces an **empty** base path in **`docker-compose.yml`** and does **not** set static export.
- **Docker + bind mount:** Compose uses a named volume for **`/app/.next`** so dev builds are not overwritten by an empty **`web/.next`** on your machine. See root README **§2.1**.

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
