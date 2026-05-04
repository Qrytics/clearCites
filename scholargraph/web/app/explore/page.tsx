"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import type { CSSProperties } from "react";
import { useMemo, useState } from "react";

const GraphCanvas = dynamic(() => import("@/components/GraphCanvas"), {
  ssr: false,
  loading: () => (
    <div style={{ padding: "2rem", color: "#94a3b8" }}>Loading graph canvas…</div>
  ),
});

export default function ExplorePage() {
  const [doi, setDoi] = useState("");
  const [activeDoi, setActiveDoi] = useState("");
  const [depth, setDepth] = useState(2);
  const [facets, setFacets] = useState({
    citations: true,
    authors: true,
    coauthors: true,
    keywords: true,
  });

  const expand = useMemo(() => {
    const parts: string[] = [];
    if (facets.citations) parts.push("citations");
    if (facets.authors) parts.push("authors");
    if (facets.coauthors) parts.push("coauthors");
    if (facets.keywords) parts.push("keywords");
    return parts.join(",") || "citations";
  }, [facets]);

  const load = () => {
    const d = doi.trim();
    if (d) setActiveDoi(d);
  };

  const btnStyle: CSSProperties = {
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
    color: "#fff",
    border: "none",
    padding: "0.5rem 1.25rem",
    borderRadius: 8,
    fontWeight: 600,
    cursor: "pointer",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0f0f1a",
        color: "#e2e8f0",
        display: "flex",
        flexDirection: "column",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <header
        style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid #2d2d3f",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <Link href="/" style={{ color: "#818cf8", textDecoration: "none", fontWeight: 600 }}>
          ← Home
        </Link>
        <Link href="/discover" style={{ color: "#d4a843", textDecoration: "none", fontWeight: 600 }}>
          Discover
        </Link>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: "0.875rem", color: "#94a3b8" }}>DOI</span>
          <input
            value={doi}
            onChange={(e) => setDoi(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="e.g. 10.1038/nature14539"
            style={{
              width: 320,
              maxWidth: "100%",
              padding: "0.5rem 0.75rem",
              borderRadius: 6,
              border: "1px solid #334155",
              background: "#1e293b",
              color: "#f8fafc",
            }}
          />
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.875rem" }}>
          Depth
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            style={{
              padding: "0.35rem 0.5rem",
              borderRadius: 6,
              border: "1px solid #334155",
              background: "#1e293b",
              color: "#f8fafc",
            }}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </label>
        <span style={{ fontSize: "0.8rem", color: "#64748b" }}>Show:</span>
        {(
          [
            ["citations", "Citations"],
            ["authors", "Authors"],
            ["coauthors", "Co-authors"],
            ["keywords", "Keywords"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8rem" }}>
            <input
              type="checkbox"
              checked={facets[key]}
              onChange={() => setFacets((f) => ({ ...f, [key]: !f[key] }))}
            />
            {label}
          </label>
        ))}
        <button type="button" onClick={load} style={btnStyle}>
          Load graph
        </button>
      </header>

      <p style={{ margin: "0.75rem 1.5rem 0", fontSize: "0.8rem", color: "#64748b", maxWidth: 720 }}>
        Purple circles = papers. Orange = authors (shared authorship). Teal = keyword tags. Edge{" "}
        <strong style={{ color: "#cbd5e1" }}>cites</strong>: arrow direction = source cites target (target is in the
        bibliography of source). Load data with the Python pipeline (Semantic Scholar / CrossRef → parser →
        push_paper) so your DOI exists in Neo4j.
      </p>

      <div style={{ flex: 1, minHeight: 520, marginTop: "0.5rem" }}>
        {activeDoi ? (
          <GraphCanvas seedDoi={activeDoi} depth={depth} expand={expand} />
        ) : (
          <div style={{ padding: "2rem", color: "#64748b" }}>
            Enter a DOI and click <strong style={{ color: "#94a3b8" }}>Load graph</strong>. The API must reach your
            graph service (e.g. <code style={{ color: "#818cf8" }}>NEXT_PUBLIC_API_URL</code>).
          </div>
        )}
      </div>
    </div>
  );
}
