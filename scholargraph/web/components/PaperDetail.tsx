import React from "react";

interface PaperData {
  doi: string;
  title: string;
  year?: number;
  cited_by_count?: number;
  impact_score?: number;
  funding_source?: string;
  abstract?: string;
  authors?: string[];
  keywords?: string[];
  funders?: string[];
  plain_summary?: string;
}

interface Props {
  paper: PaperData;
  onClose: () => void;
}

/** Badge used for keywords, funders, etc. */
const Badge: React.FC<{ text: string; colour?: string }> = ({
  text,
  colour = "bg-indigo-100 text-indigo-800",
}) => (
  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${colour}`}>
    {text}
  </span>
);

/** Display a 0–1 impact score as a filled progress bar. */
const ImpactBar: React.FC<{ score: number }> = ({ score }) => (
  <div className="mt-1 h-2 w-full rounded-full bg-gray-200">
    <div
      className="h-2 rounded-full bg-indigo-500 transition-all"
      style={{ width: `${Math.round(score * 100)}%` }}
    />
  </div>
);

const PaperDetail: React.FC<Props> = ({ paper, onClose }) => {
  const impactScore = paper.impact_score ?? 0;

  return (
    <aside className="w-80 shrink-0 overflow-y-auto border-l border-gray-200 bg-white p-5 shadow-lg">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <h2 className="text-base font-semibold leading-snug text-gray-900">
          {paper.title || "Untitled"}
        </h2>
        <button
          onClick={onClose}
          aria-label="Close detail panel"
          className="ml-2 shrink-0 text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {/* Meta */}
      <dl className="mb-4 space-y-1 text-sm text-gray-600">
        <div className="flex justify-between">
          <dt className="font-medium">DOI</dt>
          <dd>
            <a
              href={`https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noreferrer"
              className="truncate text-indigo-600 hover:underline"
            >
              {paper.doi}
            </a>
          </dd>
        </div>

        {paper.year && (
          <div className="flex justify-between">
            <dt className="font-medium">Year</dt>
            <dd>{paper.year}</dd>
          </div>
        )}

        {paper.cited_by_count !== undefined && (
          <div className="flex justify-between">
            <dt className="font-medium">Cited by</dt>
            <dd>{paper.cited_by_count.toLocaleString()}</dd>
          </div>
        )}
      </dl>

      {/* Impact score */}
      <div className="mb-4">
        <p className="text-xs font-medium text-gray-500">
          Impact Score: {(impactScore * 100).toFixed(0)} / 100
        </p>
        <ImpactBar score={impactScore} />
      </div>

      {/* Plain-English summary */}
      {paper.plain_summary && (
        <section className="mb-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Summary
          </h3>
          <p className="text-sm leading-relaxed text-gray-700">
            {paper.plain_summary}
          </p>
        </section>
      )}

      {/* Abstract */}
      {paper.abstract && (
        <section className="mb-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Abstract
          </h3>
          <p className="line-clamp-6 text-sm leading-relaxed text-gray-600">
            {paper.abstract}
          </p>
        </section>
      )}

      {/* Authors */}
      {paper.authors && paper.authors.length > 0 && (
        <section className="mb-4">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Authors
          </h3>
          <ul className="space-y-0.5 text-sm text-gray-700">
            {paper.authors.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Keywords */}
      {paper.keywords && paper.keywords.length > 0 && (
        <section className="mb-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Keywords
          </h3>
          <div className="flex flex-wrap gap-1">
            {paper.keywords.map((kw) => (
              <Badge key={kw} text={kw} />
            ))}
          </div>
        </section>
      )}

      {/* Funding sources */}
      {paper.funders && paper.funders.length > 0 && (
        <section className="mb-2">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Funded by
          </h3>
          <div className="flex flex-wrap gap-1">
            {paper.funders.map((f) => (
              <Badge key={f} text={f} colour="bg-green-100 text-green-800" />
            ))}
          </div>
        </section>
      )}

      {paper.funding_source && !paper.funders?.length && (
        <section className="mb-2">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            Funded by
          </h3>
          <Badge text={paper.funding_source} colour="bg-green-100 text-green-800" />
        </section>
      )}
    </aside>
  );
};

export default PaperDetail;
