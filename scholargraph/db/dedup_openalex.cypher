// Papers sharing the same openalex_id but different doi keys (review before merging).

MATCH (p:Paper)
WHERE p.openalex_id IS NOT NULL AND trim(p.openalex_id) <> ""
WITH p.openalex_id AS oa, collect(p.doi) AS dois, count(*) AS n
WHERE n > 1
RETURN oa, n, dois
ORDER BY n DESC;
