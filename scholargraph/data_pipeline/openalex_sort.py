"""
Map UI/API sort parameters to OpenAlex ``sort`` query values.

OpenAlex rejects unknown sort fields per entity; we whitelist here so the API and UI stay aligned.
See https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/sorting-entity-lists
"""

from __future__ import annotations

# Fields we expose in Discover + ``GET /openalex/search`` (validated against OpenAlex behaviour).
_WORKS_SORT_FIELDS = frozenset({"relevance_score", "cited_by_count", "publication_date"})
_NON_WORKS_SORT_FIELDS = frozenset({"relevance_score", "cited_by_count", "works_count"})


def openalex_sort_param(
    entity: str,
    sort_field: str,
    sort_dir: str,
    *,
    has_search_query: bool,
) -> str | None:
    """
    Return ``field:dir`` for the OpenAlex ``sort`` param, or ``None`` for API default sorting.

    *has_search_query* — ``relevance_score`` is only valid when a ``search`` term is present.
    """
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"
    allowed = _WORKS_SORT_FIELDS if entity == "works" else _NON_WORKS_SORT_FIELDS
    if sort_field not in allowed:
        return None
    if sort_field == "relevance_score":
        if not has_search_query:
            return None
        return f"relevance_score:{sort_dir}"
    return f"{sort_field}:{sort_dir}"
