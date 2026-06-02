## Shared Scripts
Utility scripts in this directory are intended to be run individually with uv.

## Environment Setup

### Hugging Face Token (Required for RAG patterns)

Patterns 2+ use `sentence-transformers` which downloads models from Hugging Face Hub.
To avoid rate limiting warnings, set up your HF token:

1. Get a token at https://huggingface.co/settings/tokens (read access is sufficient)
2. Copy `.env.example` to `.env` and add your token:
   ```bash
   cp .env.example .env
   # Edit .env and set HF_TOKEN=hf_your_token_here
   ```

The experiments scripts will automatically load this token.

---

## Countries JSON generator
Source file: generate_countries_json.py

Run from the repository root:

```
uv run --with requests python generate_countries_json.py
```

This script fetches country metrics from the World Bank API and writes the result to _shared/data/countries.json.

Notes
- Run commands from the repository root because the script uses a workspace-relative output path.
- If _shared/data does not exist, create it first or update the script to create the directory automatically.