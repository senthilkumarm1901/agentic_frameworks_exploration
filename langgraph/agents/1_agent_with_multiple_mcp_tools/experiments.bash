#!/usr/bin/env bash
set -euo pipefail

# Run from anywhere; execute commands inside this project folder.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Model/runtime settings for experiments.
# Override at runtime, for example:
#   OLLAMA_MODEL="qwen3:8b" ./experiments.bash
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:35b-a3b-coding-nvfp4}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "Running experiments with:"
echo "  OLLAMA_MODEL=$OLLAMA_MODEL"
echo "  OLLAMA_BASE_URL=$OLLAMA_BASE_URL"
echo

run_exp() {
  local question="$1"
  echo "============================================================"
  echo "Question: $question"
  uv run python -m src.main --task augmented_llm --question "$question"
  echo
}

run_exp "What is the population density of Japan in people per square kilometer?"
run_exp "What is the ratio of GDP per capita between the United States and Japan? Calculate it precisely"
run_exp "What is the GDP per capita of Germany in trillion USD per million people?"
run_exp "Which country has a larger population, India or China?"

echo "All experiments finished."
echo "Check logs in: $SCRIPT_DIR/logs.txt"
