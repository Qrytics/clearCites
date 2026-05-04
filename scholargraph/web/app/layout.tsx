import type { Metadata } from "next";
import { Courier_Prime, DM_Sans, Fraunces } from "next/font/google";

import "./discover/discover.css";

const fontMono = Courier_Prime({
  subsets: ["latin"],
  weight: ["400", "700"],
  style: ["normal", "italic"],
  variable: "--font-mono",
});

const fontSans = DM_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-sans",
});

const fontSerif = Fraunces({
  subsets: ["latin"],
  weight: ["300", "500", "700"],
  variable: "--font-serif",
});

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
    <html lang="en" className={`${fontMono.variable} ${fontSans.variable} ${fontSerif.variable}`}>
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#0c0c0b", color: "#e2d8c4" }}>
        {children}
      </body>
    </html>
  );
}
