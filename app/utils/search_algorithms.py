from math import asin, cos, radians, sin, sqrt
from typing import Iterable


def haversine_distance_km(
    origin_latitude: float,
    origin_longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    """Calculate great-circle distance between two latitude/longitude pairs."""
    earth_radius_km = 6371.0

    origin_lat = radians(origin_latitude)
    target_lat = radians(target_latitude)
    lat_delta = radians(target_latitude - origin_latitude)
    lon_delta = radians(target_longitude - origin_longitude)

    a = (
        sin(lat_delta / 2) ** 2
        + cos(origin_lat) * cos(target_lat) * sin(lon_delta / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(a))


def levenshtein_distance(left: str, right: str) -> int:
    left = left.casefold()
    right = right.casefold()

    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insert_cost = current[right_index - 1] + 1
            delete_cost = previous[right_index] + 1
            replace_cost = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current

    return previous[-1]


def fuzzy_score(query: str, value: str | None) -> float:
    if not query or not value:
        return 0.0

    normalized_query = query.strip().casefold()
    normalized_value = value.strip().casefold()
    if not normalized_query or not normalized_value:
        return 0.0

    if normalized_query in normalized_value:
        return 1.0

    tokens = normalized_value.replace(",", " ").split()
    candidates = tokens + [normalized_value]
    best_score = 0.0

    for candidate in candidates:
        max_length = max(len(normalized_query), len(candidate))
        if max_length == 0:
            continue
        distance = levenshtein_distance(normalized_query, candidate)
        best_score = max(best_score, 1 - (distance / max_length))

    return best_score


def best_fuzzy_score(query: str, values: Iterable[str | None]) -> float:
    return max((fuzzy_score(query, value) for value in values), default=0.0)


def fuzzy_matches(query: str, values: Iterable[str | None], threshold: float = 0.62) -> bool:
    return best_fuzzy_score(query, values) >= threshold
