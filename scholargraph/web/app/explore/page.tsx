"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useMemo, useState } from "react";

const GraphCanvas = dynamic(() => import("@/components/GraphCanvas"), {
  ssr: false,
  loading: () => (
    <div style={{ padding: "1rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>
      Loading graph canvas…
    </div>
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

  return (
    <div className="arxterm">
      <header className="arx-header">
        <div className="arx-logo">
          <span className="arx-logo-dot" />
          SCHOLARGRAPH
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
          <span className="arx-header-meta">DOI → Neo4j graph</span>
          <Link href="/" className="arx-nav-link">
            Home
          </Link>
          <Link href="/discover" className="arx-nav-link">
            Discover
          </Link>
        </div>
      </header>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          minHeight: "calc(100vh - 56px)",
        }}
      >
        <section
          style={{
            borderBottom: "1px solid var(--border)",
            padding: "1rem 1.5rem",
            background: "var(--bg2)",
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: "0.75rem 1.25rem",
          }}
        >
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="arx-panel-label" style={{ margin: 0 }}>
              DOI
            </span>
            <input
              className="arx-search-input"
              style={{ width: 360, maxWidth: "100%" }}
              value={doi}
              onChange={(e) => setDoi(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && load()}
              placeholder="e.g. 10.1038/nature14539 or openalex:W…"
            />
          </label>

          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="arx-panel-label" style={{ margin: 0 }}>
              Depth
            </span>
            <select
              className="arx-filter-select"
              style={{ width: 80 }}
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>

          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
            <span className="arx-panel-label" style={{ margin: 0 }}>
              Show
            </span>
            {(
              [
                ["citations", "Citations"],
                ["authors", "Authors"],
                ["coauthors", "Co-authors"],
                ["keywords", "Keywords"],
              ] as const
            ).map(([key, label]) => (
              <label
                key={key}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  fontFamily: "var(--mono)",
                  fontSize: "0.72rem",
                  color: "var(--cream)",
                }}
              >
                <input
                  type="checkbox"
                  checked={facets[key]}
                  onChange={() => setFacets((f) => ({ ...f, [key]: !f[key] }))}
                />
                {label}
              </label>
            ))}
          </div>

          <button
            type="button"
            className="arx-btn-primary"
            style={{ marginLeft: "auto", maxWidth: 200 }}
            onClick={load}
          >
            ▶ Load graph
          </button>
        </section>

        <p
          style={{
            margin: "0.75rem 1.5rem 0",
            fontFamily: "var(--mono)",
            fontSize: "0.72rem",
            color: "var(--muted)",
            maxWidth: 820,
          }}
        >
          Purple circles = papers. Orange = authors (shared authorship). Teal = keyword tags. Edge{" "}
          <strong style={{ color: "var(--cream)" }}>cites</strong>: arrow direction = source cites target.
          Load data via Discover or <code style={{ color: "var(--amber)" }}>clearcites-ingest</code> first so
          the DOI exists in Neo4j.
        </p>

        <div
          style={{
            flex: 1,
            minHeight: 520,
            margin: "0.75rem 1.5rem 1.5rem",
            border: "1px solid var(--border)",
            borderRadius: 6,
            overflow: "hidden",
            position: "relative",
            background: "var(--bg)",
          }}
        >
          {activeDoi ? (
            <GraphCanvas seedDoi={activeDoi} depth={depth} expand={expand} />
          ) : (
            <div
              style={{
                padding: "2rem",
                fontFamily: "var(--mono)",
                fontSize: "0.78rem",
                color: "var(--muted)",
              }}
            >
              Enter a DOI and click <strong style={{ color: "var(--amber)" }}>Load graph</strong>. The web
              app talks to <code style={{ color: "var(--blue)" }}>NEXT_PUBLIC_API_URL</code>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
