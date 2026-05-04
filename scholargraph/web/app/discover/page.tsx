"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import "./discover.css";

const GraphCanvas = dynamic(() => import("@/components/GraphCanvas"), {
  ssr: false,
  loading: () => (
    <div style={{ padding: "1rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>Loading graph…</div>
  ),
});

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Entity = "works" | "authors" | "institutions" | "sources";

function workShortId(id: string): string {
  return id?.replace?.("https://openalex.org/", "")?.split("/")?.pop?.() ?? "";
}

function invertedIndexToText(inv: Record<string, number[]> | undefined): string {
  if (!inv) return "";
  const words: string[] = [];
  for (const [word, positions] of Object.entries(inv)) {
    for (const pos of positions) {
      if (typeof pos === "number") words[pos] = word;
    }
  }
  return words.filter(Boolean).join(" ");
}

function parseApiError(status: number, statusText: string, bodyText: string): string {
  if (!bodyText.trim()) return `${status} ${statusText}`;
  try {
    const j = JSON.parse(bodyText) as { detail?: string | { msg?: string }[] };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) {
      const parts = j.detail.map((d) => (typeof d === "object" && d && "msg" in d ? String(d.msg) : "")).filter(Boolean);
      if (parts.length) return parts.join("; ");
    }
  } catch {
    /* not JSON */
  }
  return bodyText.length > 400 ? `${bodyText.slice(0, 400)}…` : bodyText;
}

function buildSearchApiUrl(
  entity: Entity,
  q: string,
  opts: {
    page: number;
    perPage: number;
    yearFrom: string;
    yearTo: string;
    workType: string;
    minCitations: string;
    oaOnly: boolean;
    hasAbstract: boolean;
    sortField: string;
    sortDir: string;
  }
): string {
  const p = new URLSearchParams();
  p.set("q", q.trim());
  p.set("entity", entity);
  p.set("page", String(opts.page));
  p.set("per_page", String(opts.perPage));
  if (entity === "works") {
    if (opts.yearFrom.trim()) p.set("year_from", opts.yearFrom.trim());
    if (opts.yearTo.trim()) p.set("year_to", opts.yearTo.trim());
    if (opts.workType) p.set("work_type", opts.workType);
    if (opts.minCitations.trim()) p.set("min_citations", opts.minCitations.trim());
    if (opts.oaOnly) p.set("is_oa", "true");
    if (opts.hasAbstract) p.set("has_abstract", "true");
  }
  p.set("sort_field", opts.sortField);
  p.set("sort_dir", opts.sortDir);
  return `${API_BASE}/openalex/search?${p.toString()}`;
}

export default function DiscoverPage() {
  const [entity, setEntity] = useState<Entity>("works");
  const [q, setQ] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [workType, setWorkType] = useState("");
  const [minCitations, setMinCitations] = useState("");
  const [oaOnly, setOaOnly] = useState(false);
  const [hasAbstract, setHasAbstract] = useState(false);
  const [sortField, setSortField] = useState("relevance_score");
  const [sortDir, setSortDir] = useState("desc");
  const [perPage, setPerPage] = useState(25);
  const [page, setPage] = useState(1);

  const workSortFields = useMemo(
    () =>
      [
        { value: "relevance_score", label: "Relevance" },
        { value: "cited_by_count", label: "Citations" },
        { value: "publication_date", label: "Pub. date" },
      ] as const,
    []
  );
  const catalogSortFields = useMemo(
    () =>
      [
        { value: "relevance_score", label: "Relevance" },
        { value: "cited_by_count", label: "Citations" },
        { value: "works_count", label: "Works count" },
      ] as const,
    []
  );

  useEffect(() => {
    const allowed: readonly string[] =
      entity === "works"
        ? workSortFields.map((x) => x.value)
        : catalogSortFields.map((x) => x.value);
    if (!allowed.includes(sortField)) {
      setSortField("relevance_score");
    }
  }, [entity, sortField, workSortFields, catalogSortFields]);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<unknown[]>([]);
  const [meta, setMeta] = useState<{ count?: number; page?: number; per_page?: number }>({});
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<string | null>(null);

  const [selectedWorkId, setSelectedWorkId] = useState<string | null>(null);
  const [graphSeed, setGraphSeed] = useState<string | null>(null);
  const [ingestBusy, setIngestBusy] = useState(false);
  const [ingestMsg, setIngestMsg] = useState<string | null>(null);

  const [modes, setModes] = useState({
    citations_out: true,
    citations_in: true,
    coauthors: true,
    concepts: false,
    related: false,
  });
  const [limitPerMode, setLimitPerMode] = useState(25);

  const previewUrl = useMemo(
    () =>
      q.trim()
        ? buildSearchApiUrl(entity, q, {
            page,
            perPage,
            yearFrom,
            yearTo,
            workType,
            minCitations,
            oaOnly,
            hasAbstract,
            sortField,
            sortDir,
          })
        : "—",
    [
      entity,
      q,
      page,
      perPage,
      yearFrom,
      yearTo,
      workType,
      minCitations,
      oaOnly,
      hasAbstract,
      sortField,
      sortDir,
    ]
  );

  const graphExpand = useMemo(() => {
    const p: string[] = ["citations", "authors", "coauthors"];
    if (modes.concepts) p.push("keywords");
    return p.join(",");
  }, [modes.concepts]);

  const runQuery = useCallback(
    async (nextPage: number) => {
      if (!q.trim()) {
        setError("Enter a search query.");
        return;
      }
      setLoading(true);
      setError(null);
      setSelectedWorkId(null);
      setGraphSeed(null);
      const t0 = performance.now();
      try {
        const url = buildSearchApiUrl(entity, q, {
          page: nextPage,
          perPage,
          yearFrom,
          yearTo,
          workType,
          minCitations,
          oaOnly,
          hasAbstract,
          sortField,
          sortDir,
        });
        const res = await fetch(url);
        const bodyText = await res.text();
        if (!res.ok) {
          throw new Error(parseApiError(res.status, res.statusText, bodyText));
        }
        const data = JSON.parse(bodyText) as {
          results?: unknown[];
          meta?: { count?: number; page?: number; per_page?: number };
        };
        setResults(data.results ?? []);
        setMeta(data.meta ?? {});
        setPage(nextPage);
        setElapsed(((performance.now() - t0) / 1000).toFixed(2));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Request failed");
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [
      entity,
      q,
      perPage,
      yearFrom,
      yearTo,
      workType,
      minCitations,
      oaOnly,
      hasAbstract,
      sortField,
      sortDir,
    ]
  );

  const totalPages = useMemo(() => {
    const c = meta.count ?? 0;
    if (!c || !perPage) return 1;
    return Math.min(Math.ceil(c / perPage), 500);
  }, [meta.count, perPage]);

  const ingestAndVisualize = async () => {
    if (!selectedWorkId) return;
    const modeList = (Object.keys(modes) as (keyof typeof modes)[]).filter((k) => modes[k]);
    if (modeList.length === 0) {
      setIngestMsg("Select at least one neighborhood mode.");
      return;
    }
    setIngestBusy(true);
    setIngestMsg(null);
    setGraphSeed(null);
    try {
      const res = await fetch(`${API_BASE}/openalex/explore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seed_work_id: selectedWorkId,
          modes: modeList,
          limit_per_mode: limitPerMode,
        }),
      });
      const bodyText = await res.text();
      if (!res.ok) {
        throw new Error(parseApiError(res.status, res.statusText, bodyText));
      }
      const data = JSON.parse(bodyText) as { seed_canonical_id?: string; ingested_works?: number };
      setGraphSeed(data.seed_canonical_id as string);
      setIngestMsg(`Ingested ${data.ingested_works} works. Graph below.`);
    } catch (e) {
      setIngestMsg(e instanceof Error ? e.message : "Ingest failed");
    } finally {
      setIngestBusy(false);
    }
  };

  return (
    <div className="arxterm">
      <header className="arx-header">
        <div className="arx-logo">
          <span className="arx-logo-dot" />
          SCHOLARGRAPH
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
          <span className="arx-header-meta">OpenAlex → Neo4j</span>
          <Link href="/" className="arx-nav-link">
            Home
          </Link>
          <Link href="/explore" className="arx-nav-link">
            Manual DOI
          </Link>
        </div>
      </header>

      <div className="arx-shell">
        <aside className="arx-aside">
          <div>
            <div className="arx-panel-label">Entity</div>
            <div className="arx-entity-tabs">
              {(
                [
                  ["works", "Works"],
                  ["authors", "Authors (catalog)"],
                  ["institutions", "Inst. (catalog)"],
                  ["sources", "Sources (catalog)"],
                ] as const
              ).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  className={`arx-entity-tab ${entity === key ? "active" : ""}`}
                  onClick={() => {
                    setEntity(key as Entity);
                    setSelectedWorkId(null);
                    setGraphSeed(null);
                    setIngestMsg(null);
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="arx-panel-label">Search query</div>
            <div className="arx-search-wrap">
              <span className="arx-search-icon">⌕</span>
              <input
                className="arx-search-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="e.g. neural scaling laws…"
                onKeyDown={(e) => e.key === "Enter" && runQuery(1)}
              />
            </div>
          </div>

          <hr className="arx-sep" />

          {entity === "works" && (
            <div>
              <div className="arx-panel-label">Filters</div>
              <div className="arx-filter-row">
                <label>Publication year</label>
                <div className="arx-filter-range">
                  <input
                    className="arx-filter-input"
                    type="number"
                    placeholder="1900"
                    value={yearFrom}
                    onChange={(e) => setYearFrom(e.target.value)}
                  />
                  <span style={{ color: "var(--muted)", fontFamily: "var(--mono)" }}>—</span>
                  <input
                    className="arx-filter-input"
                    type="number"
                    placeholder="2026"
                    value={yearTo}
                    onChange={(e) => setYearTo(e.target.value)}
                  />
                </div>
              </div>
              <div className="arx-filter-row">
                <label>Work type</label>
                <select className="arx-filter-select" value={workType} onChange={(e) => setWorkType(e.target.value)}>
                  <option value="">Any type</option>
                  <option value="article">Article</option>
                  <option value="book">Book</option>
                  <option value="book-chapter">Book chapter</option>
                  <option value="dataset">Dataset</option>
                  <option value="dissertation">Dissertation</option>
                  <option value="preprint">Preprint</option>
                  <option value="report">Report</option>
                  <option value="review">Review</option>
                </select>
              </div>
              <div className="arx-filter-row">
                <label>Min. citations</label>
                <input
                  className="arx-filter-input"
                  type="number"
                  min={0}
                  placeholder="e.g. 100"
                  value={minCitations}
                  onChange={(e) => setMinCitations(e.target.value)}
                />
              </div>
              <div className="arx-toggle-row">
                <label>Open access only</label>
                <button
                  type="button"
                  className={`arx-toggle ${oaOnly ? "on" : ""}`}
                  aria-checked={oaOnly}
                  onClick={() => setOaOnly(!oaOnly)}
                />
              </div>
              <div className="arx-toggle-row">
                <label>Has abstract</label>
                <button
                  type="button"
                  className={`arx-toggle ${hasAbstract ? "on" : ""}`}
                  aria-checked={hasAbstract}
                  onClick={() => setHasAbstract(!hasAbstract)}
                />
              </div>
            </div>
          )}

          <hr className="arx-sep" />

          <div>
            <div className="arx-panel-label">Sort</div>
            <div className="arx-sort-row">
              <select className="arx-filter-select" value={sortField} onChange={(e) => setSortField(e.target.value)}>
                {(entity === "works" ? workSortFields : catalogSortFields).map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
              <select className="arx-filter-select" value={sortDir} onChange={(e) => setSortDir(e.target.value)}>
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>

          <div>
            <div className="arx-panel-label">Results / page</div>
            <select
              className="arx-filter-select"
              value={perPage}
              onChange={(e) => setPerPage(Number(e.target.value))}
            >
              {[10, 25, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          <hr className="arx-sep" />

          <div>
            <div className="arx-panel-label">API request (preview)</div>
            <div className="arx-url-display">{previewUrl}</div>
          </div>

          <button type="button" className="arx-btn-primary" disabled={loading} onClick={() => runQuery(1)}>
            {loading ? "Fetching…" : "▶ Run query"}
          </button>
          <button
            type="button"
            className="arx-btn-ghost"
            onClick={() => {
              setQ("");
              setYearFrom("");
              setYearTo("");
              setWorkType("");
              setMinCitations("");
              setOaOnly(false);
              setHasAbstract(false);
              setSortField("relevance_score");
              setSortDir("desc");
              setPerPage(25);
              setResults([]);
              setError(null);
            }}
          >
            Clear
          </button>
        </aside>

        <main className="arx-main">
          <div className={`arx-loading-bar ${loading ? "active" : ""}`} />

          <div className="arx-stats-bar">
            <span>
              <span className="arx-stats-count">
                {meta.count != null ? meta.count.toLocaleString() : "—"} results
              </span>
              {elapsed != null && <span style={{ marginLeft: "1rem" }}>({elapsed}s)</span>}
            </span>
          </div>

          {error && <div className="arx-error">{error}</div>}

          <div className="arx-results">
            {!loading && results.length === 0 && !error && (
              <div className="arx-empty">
                <p style={{ fontFamily: "var(--serif)", fontSize: "1.1rem", color: "var(--cream)", opacity: 0.6 }}>
                  No query yet
                </p>
                <p>Search OpenAlex from the left panel, then select a work to push into Neo4j and open the graph.</p>
              </div>
            )}

            {entity === "works" &&
              results.map((raw) => {
                const w = raw as Record<string, unknown>;
                const id = String(w.id ?? "");
                const wid = workShortId(id);
                const title = String(w.title ?? "Untitled");
                const year = w.publication_year ?? "—";
                const type = String(w.type ?? "");
                const cites = Number(w.cited_by_count ?? 0).toLocaleString();
                const oa = Boolean((w.open_access as { is_oa?: boolean } | undefined)?.is_oa);
                const doiRaw = w.doi ? String(w.doi) : "";
                const doi = doiRaw.replace("https://doi.org/", "");
                const doiHref = doi ? `https://doi.org/${doi}` : null;
                const authorships = (w.authorships as { author?: { display_name?: string } }[]) ?? [];
                const authors = authorships
                  .slice(0, 4)
                  .map((a) => a.author?.display_name)
                  .filter(Boolean)
                  .join(", ");
                const more = authorships.length > 4 ? ` +${authorships.length - 4}` : "";
                const inv = w.abstract_inverted_index as Record<string, number[]> | undefined;
                const abstract = inv
                  ? `${invertedIndexToText(inv).slice(0, 280)}…`
                  : typeof w.abstract === "string"
                    ? w.abstract.slice(0, 280)
                    : "";
                const topics = ((w.topics as { display_name?: string }[]) ?? [])
                  .slice(0, 4)
                  .map((t) => t.display_name)
                  .filter(Boolean) as string[];
                const selected = selectedWorkId === wid;
                return (
                  <div
                    key={id || wid}
                    className={`arx-paper-card ${selected ? "selected" : ""}`}
                    onClick={() => setSelectedWorkId(wid)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && setSelectedWorkId(wid)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                      <div className="arx-card-title">
                        {doiHref ? (
                          <a href={doiHref} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                            {title}
                          </a>
                        ) : (
                          title
                        )}
                      </div>
                      <div style={{ display: "flex", gap: "0.35rem", flexShrink: 0 }}>
                        {oa && <span className="arx-badge arx-badge-oa">OA</span>}
                        {type && <span className="arx-badge arx-badge-type">{type}</span>}
                      </div>
                    </div>
                    <div className="arx-meta">
                      {authors && (
                        <span>
                          <strong style={{ color: "var(--cream)" }}>{authors}</strong>
                          {more}
                        </span>
                      )}
                      <span> · Year {String(year)}</span>
                      <span> · Citations {cites}</span>
                    </div>
                    {abstract ? <div className="arx-abstract">{abstract}</div> : null}
                    {topics.length > 0 && (
                      <div style={{ marginTop: "0.5rem", display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                        {topics.map((t) => (
                          <span key={t} className="arx-badge arx-badge-type" style={{ fontSize: "0.58rem" }}>
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                    <div style={{ marginTop: "0.6rem", fontFamily: "var(--mono)", fontSize: "0.65rem" }}>
                      <a href={id} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                        OpenAlex ↗
                      </a>
                      {doiHref && (
                        <a
                          href={doiHref}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ marginLeft: "0.75rem" }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          DOI ↗
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}

            {entity !== "works" &&
              results.map((raw) => {
                const item = raw as Record<string, unknown>;
                const id = String(item.id ?? "");
                const name = String(item.display_name ?? "Unknown");
                const worksC = Number(item.works_count ?? 0).toLocaleString();
                const citedC = Number(item.cited_by_count ?? 0).toLocaleString();
                const initial = name.charAt(0).toUpperCase();
                return (
                  <div key={id} className="arx-entity-card">
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: "50%",
                        background: "var(--bg3)",
                        border: "1px solid var(--border2)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontFamily: "var(--mono)",
                        color: "var(--amber-dim)",
                      }}
                    >
                      {initial}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontFamily: "var(--serif)", fontSize: "1rem", fontWeight: 500 }}>
                        <a href={id} target="_blank" rel="noopener noreferrer" style={{ color: "inherit" }}>
                          {name}
                        </a>
                      </div>
                      <div className="arx-meta">
                        Works <strong style={{ color: "var(--cream)" }}>{worksC}</strong> · Citations{" "}
                        <strong style={{ color: "var(--cream)" }}>{citedC}</strong>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>

          {totalPages > 1 && (
            <div className="arx-pagination">
              <span>
                Page {page} / {totalPages}
              </span>
              <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                <button type="button" className="arx-page-btn" disabled={page <= 1} onClick={() => runQuery(page - 1)}>
                  ← Prev
                </button>
                <button
                  type="button"
                  className="arx-page-btn"
                  disabled={page >= totalPages}
                  onClick={() => runQuery(page + 1)}
                >
                  Next →
                </button>
              </div>
            </div>
          )}

          {entity === "works" && selectedWorkId && (
            <div className="arx-viz-panel">
              <h3>Graph ingest · {selectedWorkId}</h3>
              <p style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "0.75rem" }}>
                Choose which OpenAlex neighborhoods to fetch and merge into Neo4j, then load the React Flow graph (same
                engine as /explore).
              </p>
              <div className="arx-mode-grid">
                {(
                  [
                    ["citations_out", "References (this paper cites)"],
                    ["citations_in", "Cited by"],
                    ["coauthors", "Shared authors"],
                    ["concepts", "Same OpenAlex concept cluster"],
                    ["related", "OpenAlex “related” works"],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key}>
                    <input
                      type="checkbox"
                      checked={modes[key]}
                      onChange={() => setModes((m) => ({ ...m, [key]: !m[key] }))}
                    />
                    {label}
                  </label>
                ))}
              </div>
              <div className="arx-filter-row" style={{ maxWidth: 200 }}>
                <label>Max works / mode</label>
                <input
                  className="arx-filter-input"
                  type="number"
                  min={1}
                  max={100}
                  value={limitPerMode}
                  onChange={(e) => setLimitPerMode(Number(e.target.value) || 25)}
                />
              </div>
              <button
                type="button"
                className="arx-btn-primary"
                style={{ marginTop: "0.75rem", maxWidth: 320 }}
                disabled={ingestBusy}
                onClick={() => ingestAndVisualize()}
              >
                {ingestBusy ? "Ingesting…" : "Ingest & visualize"}
              </button>
              {ingestMsg && (
                <p style={{ marginTop: "0.75rem", fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--muted)" }}>
                  {ingestMsg}
                </p>
              )}
              {graphSeed && (
                <div className="arx-graph-wrap" style={{ display: "flex", flexDirection: "column" }}>
                  <div style={{ flex: 1, minHeight: 400, position: "relative" }}>
                    <GraphCanvas seedDoi={graphSeed} depth={2} expand={graphExpand} />
                  </div>
                </div>
              )}
            </div>
          )}

          {entity !== "works" && (
            <div className="arx-viz-panel">
              <p style={{ fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--muted)" }}>
                Switch to <strong style={{ color: "var(--amber)" }}>Works</strong> to select a paper and build the
                citation graph.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
