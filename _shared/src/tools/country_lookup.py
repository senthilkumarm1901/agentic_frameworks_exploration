"""Country data lookup tool — loads data from countries.json."""

import json
from pathlib import Path

# Path to the countries.json data file (relative to this file's location)
_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "countries.json"

# Valid metrics that can be queried
_VALID_METRICS = ("gdp_trillion", "population_million", "area_sq_km")

# Human-readable units for each metric
_METRIC_LABELS = {
    "gdp_trillion": "trillion USD",
    "population_million": "million people",
    "area_sq_km": "square kilometers",
}


def _load_countries() -> dict:
    """Load and return the countries JSON data."""
    with open(_DATA_PATH, "r") as f:
        return json.load(f)


def _normalize_key(name: str) -> str:
    """Normalize a country name to match JSON keys (lowercase, underscored)."""
    return name.strip().lower().replace(" ", "_")


def country_lookup(country: str, metric: str) -> str:
    """Look up a country statistic.

    Args:
        country: Country name (e.g., "United States", "India", "Japan")
        metric: One of "gdp_trillion", "population_million", "area_sq_km"

    Returns:
        String with the numeric value and context
    """
    # Validate metric
    if metric not in _VALID_METRICS:
        return f"Invalid metric '{metric}'. Valid metrics: {', '.join(_VALID_METRICS)}"

    # Load data and normalize country key
    data = _load_countries()
    key = _normalize_key(country)

    # Look up country
    if key not in data:
        available = [entry["name"] for entry in data.values()]
        return f"Country '{country}' not found. Available: {', '.join(available)}"

    # Return the requested metric
    value = data[key][metric]
    label = _METRIC_LABELS[metric]
    display_name = data[key]["name"]
    return f"The {metric.replace('_', ' ')} of {display_name} is {value} {label}"
