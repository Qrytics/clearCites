export default function Home() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      {/* Hero */}
      <h1
        style={{
          fontSize: "3rem",
          fontWeight: 800,
          background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          marginBottom: "0.5rem",
        }}
      >
        🕸️ clearCites
      </h1>
      <p style={{ fontSize: "1.25rem", color: "#94a3b8", maxWidth: 640, marginBottom: "2rem" }}>
        Open-source citation graph in Neo4j: papers, citations, authors, and keywords on a React Flow
        canvas (Dagre layer layout, fit view, full-screen). <strong>Discover</strong> searches OpenAlex
        and ingests work neighborhoods. <strong>Explore</strong> loads by DOI or{" "}
        <code style={{ fontSize: "0.85em" }}>openalex:W…</code>. Funding and abstracts show in the paper
        sidebar when the API has them. Optional <code style={{ fontSize: "0.85em" }}>/ai/*</code> routes
        are extractive TF-IDF helpers — no external LLM. Everything below needs Docker
        (Neo4j + FastAPI).
      </p>

      {/* Feature cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1.25rem",
          maxWidth: 800,
          width: "100%",
          marginBottom: "2.5rem",
        }}
      >
        {[
          {
            icon: "🔗",
            title: "Citation graph",
            desc: "Citation edges plus optional authors, co-authors, and keywords. Dagre layer layout, fit view after load, and a full-screen control on the toolbar.",
          },
          {
            icon: "💰",
            title: "Funding metadata",
            desc: "Funder names and funding fields in the paper detail panel when ingested (e.g. CrossRef). Neo4j stores Funder nodes—the canvas does not draw them as nodes.",
          },
          {
            icon: "🛰️",
            title: "OpenAlex Discover",
            desc: "Works tab: search, pick a seed, choose neighborhoods (references, cited-by, related, …), ingest into Neo4j, graph on the same page. Authors / institutions / sources tabs are catalog search only (no graph ingest yet).",
          },
          {
            icon: "🔍",
            title: "Search & ingest",
            desc: "Neo4j GET /search and /search/by-keyword for what's already in the DB; clearcites-ingest (Semantic Scholar or CrossRef) for DOI-first pipelines. Papers carry openalex_id for dedup (db/dedup_openalex.cypher).",
          },
        ].map(({ icon, title, desc }) => (
          <div
            key={title}
            style={{
              background: "#1e1e2e",
              border: "1px solid #2d2d3f",
              borderRadius: 12,
              padding: "1.25rem",
              textAlign: "left",
            }}
          >
            <div style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>{icon}</div>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "0.4rem" }}>{title}</h2>
            <p style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.5, margin: 0 }}>{desc}</p>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
        <a
          href="/discover"
          style={{
            background: "linear-gradient(135deg, #d4a843, #8a6c28)",
            color: "#0c0c0b",
            padding: "0.75rem 1.75rem",
            borderRadius: 8,
            fontWeight: 600,
            textDecoration: "none",
            fontSize: "0.95rem",
          }}
        >
          Discover (OpenAlex)
        </a>
        <a
          href="/explore"
          style={{
            background: "linear-gradient(135deg, #22c55e, #16a34a)",
            color: "#fff",
            padding: "0.75rem 1.75rem",
            borderRadius: 8,
            fontWeight: 600,
            textDecoration: "none",
            fontSize: "0.95rem",
          }}
        >
          Explore graph
        </a>
        <a
          href="https://github.com/Qrytics/clearCites"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            color: "#fff",
            padding: "0.75rem 1.75rem",
            borderRadius: 8,
            fontWeight: 600,
            textDecoration: "none",
            fontSize: "0.95rem",
          }}
        >
          View on GitHub
        </a>
        <a
          href="https://github.com/Qrytics/clearCites#2-start-the-stack-docker"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: "transparent",
            color: "#6366f1",
            padding: "0.75rem 1.75rem",
            borderRadius: 8,
            fontWeight: 600,
            textDecoration: "none",
            fontSize: "0.95rem",
            border: "1px solid #6366f1",
          }}
        >
          Quick Start
        </a>
      </div>

      <footer style={{ marginTop: "3rem", fontSize: "0.8rem", color: "#475569", maxWidth: 560, lineHeight: 1.5 }}>
        This GitHub Pages build is a static export from Actions: navigation works, but Discover/Explore
        need <code style={{ fontSize: "0.75rem" }}>docker compose up</code> in{" "}
        <code style={{ fontSize: "0.75rem" }}>scholargraph/</code> (Neo4j schema + API). See the repo
        README for OpenAlex retries (<code style={{ fontSize: "0.75rem" }}>OPENALEX_MAX_RETRIES</code>),
        CI (test + docker-images), and dedup notes. MIT License.
      </footer>
    </main>
  );
}
