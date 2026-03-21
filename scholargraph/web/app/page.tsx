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
        🕸️ ScholarGraph
      </h1>
      <p style={{ fontSize: "1.25rem", color: "#94a3b8", maxWidth: 560, marginBottom: "2rem" }}>
        Mapping the DNA of Human Knowledge — an open-source visual discovery
        tool that turns academic research into an interactive, navigable map.
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
            title: "Citation Graph",
            desc: "Visualise how papers build on and validate each other through a dynamic node-edge canvas.",
          },
          {
            icon: "💰",
            title: "Follow the Money",
            desc: "See which research is publicly funded (NIH, NSF, …) and trace taxpayer dollars to outcomes.",
          },
          {
            icon: "🤖",
            title: "AI Summaries",
            desc: "LLM-powered plain-English abstracts and relationship scoring for non-specialists.",
          },
          {
            icon: "🔍",
            title: "Keyword Discovery",
            desc: "Search papers by keyword, author, or DOI and explore their full citation pedigree.",
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
          href="https://github.com/Qrytics/clearCites#-quick-start"
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

      <footer style={{ marginTop: "3rem", fontSize: "0.8rem", color: "#475569" }}>
        clearCites · open-source · MIT License
      </footer>
    </main>
  );
}
