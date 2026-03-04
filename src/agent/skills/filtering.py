from __future__ import annotations


def normalize_skill_filter(skill_filter: list[object] | None = None) -> list[str] | None:
    if skill_filter is None:
        return None
    return [str(entry).strip() for entry in skill_filter if str(entry).strip()]


def normalize_skill_filter_for_comparison(
    skill_filter: list[object] | None = None,
) -> list[str] | None:
    normalized = normalize_skill_filter(skill_filter)
    if normalized is None:
        return None
    return sorted(set(normalized))


def matches_skill_filter(
    cached: list[object] | None = None,
    next_filter: list[object] | None = None,
) -> bool:
    cached_norm = normalize_skill_filter_for_comparison(cached)
    next_norm = normalize_skill_filter_for_comparison(next_filter)
    if cached_norm is None or next_norm is None:
        return cached_norm is next_norm
    return cached_norm == next_norm
