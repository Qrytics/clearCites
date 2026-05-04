// clearCites – Neo4j constraints and indexes (run once on a fresh database).

CREATE CONSTRAINT paper_doi_unique IF NOT EXISTS
  FOR (p:Paper) REQUIRE p.doi IS UNIQUE;

CREATE CONSTRAINT author_orcid_unique IF NOT EXISTS
  FOR (a:Author) REQUIRE a.orcid IS UNIQUE;

CREATE CONSTRAINT keyword_text_unique IF NOT EXISTS
  FOR (k:Keyword) REQUIRE k.text IS UNIQUE;

CREATE CONSTRAINT funder_name_unique IF NOT EXISTS
  FOR (f:Funder) REQUIRE f.name IS UNIQUE;

CREATE INDEX paper_title_index IF NOT EXISTS
  FOR (p:Paper) ON (p.title);

CREATE INDEX paper_year_index IF NOT EXISTS
  FOR (p:Paper) ON (p.year);

CREATE INDEX author_name_index IF NOT EXISTS
  FOR (a:Author) ON (a.name);

CREATE INDEX paper_openalex_id_index IF NOT EXISTS
  FOR (p:Paper) ON (p.openalex_id);
