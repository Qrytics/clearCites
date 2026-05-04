import type { Metadata } from "next";

import "./discover/discover.css";

export const metadata: Metadata = {
  title: "clearCites — citation graph",
  description:
    "Neo4j-backed papers and citations, OpenAlex Discover (works ingest), React Flow + Dagre explorer, FastAPI (search, graph, optional /ai extractive helpers).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#0f0f1a", color: "#e2e8f0" }}>
        {children}
      </body>
    </html>
  );
}
