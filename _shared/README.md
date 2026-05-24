## Shared Scripts
Utility scripts in this directory are intended to be run individually with uv.

Countries JSON generator
Source file: generate_countries_json.py

Run from the repository root:

```
uv run --with requests python generate_countries_json.py
```

This script fetches country metrics from the World Bank API and writes the result to _shared/data/countries.json.

Notes
- Run commands from the repository root because the script uses a workspace-relative output path.
- If _shared/data does not exist, create it first or update the script to create the directory automatically.