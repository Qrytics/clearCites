// ============================================================
// ScholarGraph – Neo4j Graph Schema
// ============================================================
// Run these statements once against a fresh Neo4j instance.

// ------ Constraints (ensure uniqueness & fast look-ups) ------

CREATE CONSTRAINT paper_doi_unique IF NOT EXISTS
  FOR (p:Paper) REQUIRE p.doi IS UNIQUE;

CREATE CONSTRAINT author_orcid_unique IF NOT EXISTS
  FOR (a:Author) REQUIRE a.orcid IS UNIQUE;

CREATE CONSTRAINT keyword_text_unique IF NOT EXISTS
  FOR (k:Keyword) REQUIRE k.text IS UNIQUE;

CREATE CONSTRAINT funder_name_unique IF NOT EXISTS
  FOR (f:Funder) REQUIRE f.name IS UNIQUE;

// ------ Indexes for common search patterns ------

CREATE INDEX paper_title_index IF NOT EXISTS
  FOR (p:Paper) ON (p.title);

CREATE INDEX paper_year_index IF NOT EXISTS
  FOR (p:Paper) ON (p.year);

CREATE INDEX author_name_index IF NOT EXISTS
  FOR (a:Author) ON (a.name);

// ============================================================
// Node Definitions (illustrative CREATE examples)
// ============================================================

// Paper node
// MERGE (p:Paper {doi: $doi})
//   ON CREATE SET
//     p.title          = $title,
//     p.year           = $year,
//     p.abstract       = $abstract,
//     p.plain_summary  = $plain_summary,   -- AI-generated 3-sentence summary
//     p.funding_source = $funding_source,  -- e.g. "NIH", "NSF"
//     p.cited_by_count = $cited_by_count,
//     p.impact_score   = $impact_score,    -- AI-derived 0-1 correlation value
//     p.created_at     = datetime();

// Author node
// MERGE (a:Author {orcid: $orcid})
//   ON CREATE SET
//     a.name       = $name,
//     a.created_at = datetime();

// Keyword node
// MERGE (k:Keyword {text: $text});

// Funder node
// MERGE (f:Funder {name: $name});

// ============================================================
// Relationship Definitions
// ============================================================

// (Author)-[:WROTE]->(Paper)
// MATCH (a:Author {orcid: $orcid}), (p:Paper {doi: $doi})
// MERGE (a)-[:WROTE]->(p);

// (Paper)-[:CITES]->(Paper)
// MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi})
// MERGE (src)-[:CITES]->(tgt);

// (Paper)-[:VALIDATES]->(Paper)
//   Properties: correlation_value (0–1), evaluated_by (model name)
// MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi})
// MERGE (src)-[r:VALIDATES]->(tgt)
//   ON CREATE SET r.correlation_value = $correlation_value,
//                 r.evaluated_by      = $evaluated_by;

// (Paper)-[:BUILDS_ON]->(Paper)
// MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi})
// MERGE (src)-[:BUILDS_ON]->(tgt);

// (Paper)-[:CHALLENGES]->(Paper)
// MATCH (src:Paper {doi: $src_doi}), (tgt:Paper {doi: $tgt_doi})
// MERGE (src)-[:CHALLENGES]->(tgt);

// (Paper)-[:HAS_KEYWORD]->(Keyword)
// MATCH (p:Paper {doi: $doi}), (k:Keyword {text: $text})
// MERGE (p)-[:HAS_KEYWORD]->(k);

// (Paper)-[:FUNDED_BY]->(Funder)
// MATCH (p:Paper {doi: $doi}), (f:Funder {name: $name})
// MERGE (p)-[:FUNDED_BY]->(f);
