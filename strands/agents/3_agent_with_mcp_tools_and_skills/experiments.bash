#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FRAMEWORK="strands"
PATTERN="agent_with_mcp_tools_and_skills"

export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:35b-a3b-coding-nvfp4}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
LOG_FILE_NAME="${LOG_FILE_NAME:-logs.txt}"
LOG_FILE="$(pwd)/$LOG_FILE_NAME"

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
  local venv_kb=$(du -sk .venv 2>/dev/null | cut -f1)
  local venv_mb=$(echo "scale=2; ${venv_kb:-0} / 1024" | bc)
  echo "packaging_size_mb: ${venv_mb}"

  # Lines of code (pattern's src/ only, excludes _shared)
  local loc=$(find src -name "*.py" -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')
  echo "loc: ${loc}"

  # Dependency count from uv.lock
  local deps=$(grep -c 'name = ' uv.lock 2>/dev/null || echo "0")
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
  local expected_skill="${3:-}"

  echo "============================================================"
  echo "Task: $task"
  if [[ -n "$expected_skill" ]]; then
    echo "Expected Skill: $expected_skill"
  fi
  echo "Question: $question"
  echo "============================================================"

  # Append run header to logs
  {
    echo "--------------------------------------------------------------------------------"
    echo "run_timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "task: ${task}"
    echo "question: ${question}"
    if [[ -n "$expected_skill" ]]; then
      echo "expected_skill: ${expected_skill}"
    fi
    echo "model: ${OLLAMA_MODEL}"
  } >> "${LOG_FILE}"

  # Run and capture output
  local output
  local start_time=$(python3 -c "import time; print(int(time.time() * 1000))")

  if output=$(uv run python -m src.main --task "$task" --question "$question" 2>&1); then
    local end_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    local duration=$((end_time - start_time))

    echo "$output"

    {
      echo "duration_ms: ${duration}"
      echo "status: success"
      echo "output:"
      echo "$output" | sed 's/^/  /'
      echo ""
    } >> "${LOG_FILE}"
  else
    local end_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    local duration=$((end_time - start_time))

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
  # Load HF_TOKEN from _shared/.env if available
  SHARED_ENV="$(dirname "$(dirname "$(dirname "$(pwd)")")")/_shared/.env"
  if [[ -f "$SHARED_ENV" ]]; then
      export $(grep -v '^#' "$SHARED_ENV" | xargs)
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

  # Ensure dependencies are installed
  uv sync --quiet

  # Pre-download embedding model for RAG (pattern2_server uses it)
  echo "Ensuring embedding model is cached..."
  uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
  echo "Embedding model ready."
  echo

  # If logs.txt doesn't exist or is empty, capture static metrics first
  if [[ ! -s "${LOG_FILE}" ]]; then
    echo "Capturing static metrics (first run)..."
    capture_static_metrics > "${LOG_FILE}"
  fi

  # Ensure run section header exists
  ensure_run_section

  # ---------------------------------------------------------------------------
  # Experiments — each targets a specific skill
  # ---------------------------------------------------------------------------

  # Skill: country-comparison
  run_experiment \
    "comparison_japan_germany" \
    "Compare the GDP and population of Japan and Germany. Which country has higher GDP per capita?" \
    "country-comparison"

  # Skill: country-profile
  run_experiment \
    "profile_brazil" \
    "Give me a comprehensive profile of Brazil including key statistics and what makes it notable." \
    "country-profile"

  # Skill: regional-analysis
  run_experiment \
    "europe_gdp_analysis" \
    "Analyze the GDP of European countries in the dataset. Which has the highest and what's the regional total?" \
    "regional-analysis"

  # Skill: report-formatting (used alongside another skill)
  run_experiment \
    "formatted_comparison_report" \
    "Create a professionally formatted report comparing the United States and China across all metrics." \
    "report-formatting"

  echo "========================================"
  echo "Experiments complete!"
  echo "Results logged to: $LOG_FILE"
  echo "========================================"
}

main "$@"
