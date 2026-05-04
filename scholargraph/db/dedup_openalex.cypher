// ---------------------------------------------------------------------------
// Optional: find Paper nodes that share the same OpenAlex work id but
// different `doi` keys (e.g. one row keyed as 10.x/... and another as openalex:W...).
//
// Ingest now sets `p.openalex_id` on every upsert so you can spot collisions.
// Merging nodes is graph-specific (re-point CITES/WROTE/etc.); review in Neo4j
// Browser before running destructive writes.
// ---------------------------------------------------------------------------

MATCH (p:Paper)
WHERE p.openalex_id IS NOT NULL AND trim(p.openalex_id) <> ""
WITH p.openalex_id AS oa, collect(p.doi) AS dois, count(*) AS n
WHERE n > 1
RETURN oa, n, dois
ORDER BY n DESC;
