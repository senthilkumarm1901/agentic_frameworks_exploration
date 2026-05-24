
"""
Generate _shared/data/countries.json from World Bank Indicators API.
Source: https://data.worldbank.org/ (CC BY-4.0)
Indicators: NY.GDP.MKTP.CD, SP.POP.TOTL, AG.LND.TOTL.K2
"""
import json, requests
from pathlib import Path
import json, requests

OUTPUT_PATH = Path("_shared/data/countries.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

YEAR = "2023"
COUNTRIES = ["US", "IN", "JP", "DE", "BR", "GB", "FR", "CN", "AU", "CA",
             "KR", "MX", "ID", "NG", "ZA", "SA", "RU", "IT", "ES", "EG"]

INDICATORS = {
    "gdp_usd":        "NY.GDP.MKTP.CD",
    "population":     "SP.POP.TOTL",
    "area_sq_km":     "AG.LND.TOTL.K2",
}

BASE = "https://api.worldbank.org/v2/country/{codes}/indicator/{ind}?format=json&date={year}&per_page=300"

def fetch(indicator, codes):
    url = BASE.format(codes=";".join(codes), ind=indicator, year=YEAR)
    resp = requests.get(url).json()
    return {r["countryiso3code"]: r["value"] for r in resp[1] if r["value"]}

data = {}
for metric, code in INDICATORS.items():
    for iso3, val in fetch(code, COUNTRIES).items():
        data.setdefault(iso3, {})[metric] = val

# Enrich with country names
url = f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}?format=json&per_page=50"
names = {c["id"]: c["name"] for c in requests.get(url).json()[1]}

result = {}
for iso3, metrics in data.items():
    key = names.get(iso3, iso3).lower().replace(" ", "_")
    result[key] = {
        "name": names.get(iso3, iso3),
        "iso3": iso3,
        "gdp_usd": metrics.get("gdp_usd"),
        "gdp_trillion": round(metrics.get("gdp_usd", 0) / 1e12, 2),
        "population": int(metrics.get("population", 0)),
        "population_million": round(metrics.get("population", 0) / 1e6, 1),
        "area_sq_km": int(metrics.get("area_sq_km", 0)),
        "source": "World Bank Open Data (CC BY-4.0)",
        "year": YEAR,
    }

with OUTPUT_PATH.open("w") as f:
    json.dump(result, f, indent=2)


print(f"Generated {len(result)} countries -> {OUTPUT_PATH}")