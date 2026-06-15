#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="${SCRIPT_DIR}/logs.txt"
FRAMEWORK="hermes"
PATTERN="agent_with_rag_mcp_tool"

# Keep uv executions bound to this pattern's local environment.
export UV_PROJECT_ENVIRONMENT="${SCRIPT_DIR}/.venv"

# Model/runtime settings for experiments.
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:35b-a3b-coding-nvfp4}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

# =============================================================================
# STATIC METRICS (captured once per setup)
# =============================================================================
capture_static_metrics() {
  echo "================================================================================"
  echo "STATIC METRICS (captured once per setup)"
  echo "================================================================================"
  echo "timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "framework: ${FRAMEWORK}"
  echo "pattern: ${PATTERN}"

  # Packaging size (KB -> MB)
  local venv_kb
  venv_kb=$(du -sk .venv 2>/dev/null | cut -f1)
  local venv_mb
  venv_mb=$(echo "scale=2; ${venv_kb:-0} / 1024" | bc)
  echo "packaging_size_mb: ${venv_mb}"

  # Lines of code (pattern's src/ only, excludes _shared)
  local loc
  loc=$(find src -name "*.py" -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')
  echo "loc: ${loc}"

  # Dependency count from uv.lock (if present)
  local deps
  deps=$(grep -c 'name = ' uv.lock 2>/dev/null || echo "0")
  echo "dependency_count: ${deps}"
  echo ""
}

# =============================================================================
# RUN SECTION HEADER
# =============================================================================
ensure_run_section() {
  if ! grep -q "RUN METRICS" "${LOG_FILE}" 2>/dev/null; then
    echo "================================================================================" >> "${LOG_FILE}"
    echo "RUN METRICS (appended per execution)" >> "${LOG_FILE}"
    echo "================================================================================" >> "${LOG_FILE}"
  fi
}

# =============================================================================
# RUN EXPERIMENT
# =============================================================================
run_experiment() {
  local task="$1"
  local question="$2"

  echo "============================================================"
  echo "Task: $task"
  echo "Question: $question"
  echo "============================================================"

  # Append run header to logs
  {
    echo "--------------------------------------------------------------------------------"
    echo "run_timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "task: ${task}"
    echo "question: ${question}"
    echo "model: ${OLLAMA_MODEL}"
  } >> "${LOG_FILE}"

  # Run and capture output (use python3 for macOS-compatible millisecond timing)
  local output
  local start_time
  start_time=$(python3 -c "import time; print(int(time.time() * 1000))")

  if output=$(uv run python -m src.main --task "$task" --question "$question" 2>&1); then
    local end_time
    end_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    local duration
    duration=$((end_time - start_time))

    echo "$output"

    {
      echo "duration_ms: ${duration}"
      echo "status: success"
      echo "output:"
      echo "$output" | sed 's/^/  /'
      echo ""
    } >> "${LOG_FILE}"
  else
    local end_time
    end_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    local duration
    duration=$((end_time - start_time))

    echo "ERROR: $output"

    {
      echo "duration_ms: ${duration}"
      echo "status: error"
      echo "output:"
      echo "$output" | sed 's/^/  /'
      echo ""
    } >> "${LOG_FILE}"
  fi

  echo
}

# =============================================================================
# MAIN LOGIC
# =============================================================================
main() {
  # Load HF_TOKEN from _shared/.env if available (needed by sentence-transformers)
  SHARED_ENV="$(dirname "$(dirname "$(dirname "$(pwd)")")")/_shared/.env"
  if [[ -f "$SHARED_ENV" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$SHARED_ENV"
    set +a
  fi

  echo "Running experiments with:"
  echo "  FRAMEWORK=$FRAMEWORK"
  echo "  PATTERN=$PATTERN"
  echo "  OLLAMA_MODEL=$OLLAMA_MODEL"
  echo "  OLLAMA_BASE_URL=$OLLAMA_BASE_URL"
  if [[ -n "${HF_TOKEN:-}" ]]; then
    echo "  HF_TOKEN=****${HF_TOKEN: -4}"
  else
    echo "  HF_TOKEN=(not set)"
  fi
  echo "  LOG_FILE=$LOG_FILE"
  echo

  # Pre-download the embedding model so timing experiments aren't skewed
  echo "Ensuring embedding model is cached..."
  uv run python -c "
import warnings, os
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('HF_HUB_DISABLE_PROGRESS_BARS', '1')
warnings.filterwarnings('ignore')
from sentence_transformers import SentenceTransformer
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('Embedding model ready.')
"
  echo

  # If logs.txt doesn't exist or is empty, capture static metrics first
  if [[ ! -s "${LOG_FILE}" ]]; then
    echo "Capturing static metrics (first run)..."
    capture_static_metrics > "${LOG_FILE}"
  fi

  # Ensure run section header exists
  ensure_run_section

  # Pattern 2 experiments — mix of qualitative-only, numeric-only, and hybrid questions
  # to exercise all three tools (country_lookup, calculator, country_kb_search)

  run_experiment "country_analysis" "What are the main geographic features of Australia?"
  run_experiment "country_analysis" "Describe the political system of Germany."

  echo "All experiments finished."
  echo "Check logs in: ${LOG_FILE}"
}

# Run main
main "$@"
