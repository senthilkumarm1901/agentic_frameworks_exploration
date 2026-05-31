#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="${SCRIPT_DIR}/logs.txt"
FRAMEWORK="langgraph"
PATTERN="agent_with_multiple_mcp_tools"

# Model/runtime settings for experiments.
# Override at runtime, for example:
#   OLLAMA_MODEL="qwen3:8b" ./experiments.bash
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
  
  # Run and capture output
  local output
  local start_time=$(date +%s.%N)
  
  if output=$(uv run python -m src.main --task "$task" --question "$question" 2>&1); then
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    
    echo "$output"
    
    # Append output to logs in readable format
    {
      echo "duration_seconds: ${duration}"
      echo "status: success"
      echo "output:"
      echo "$output" | sed 's/^/  /'
      echo ""
    } >> "${LOG_FILE}"
  else
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    
    echo "ERROR: $output"
    
    {
      echo "duration_seconds: ${duration}"
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
  echo "Running experiments with:"
  echo "  FRAMEWORK=$FRAMEWORK"
  echo "  PATTERN=$PATTERN"
  echo "  OLLAMA_MODEL=$OLLAMA_MODEL"
  echo "  OLLAMA_BASE_URL=$OLLAMA_BASE_URL"
  echo "  LOG_FILE=$LOG_FILE"
  echo
  
  # If logs.txt doesn't exist or is empty, capture static metrics first
  if [[ ! -s "${LOG_FILE}" ]]; then
    echo "Capturing static metrics (first run)..."
    capture_static_metrics > "${LOG_FILE}"
  fi
  
  # Ensure run section header exists
  ensure_run_section
  
  # Run experiments
  run_experiment "country_analysis" "What is the population density of Japan in people per square kilometer?"
  run_experiment "country_analysis" "What is the ratio of GDP per capita between the United States and Japan? Calculate it precisely"
  run_experiment "country_analysis" "What is the GDP per capita of Germany in trillion USD per million people?"
  run_experiment "country_analysis" "Which country has a larger population, India or China?"
  
  echo "All experiments finished."
  echo "Check logs in: ${LOG_FILE}"
}

# Run main
main "$@"
