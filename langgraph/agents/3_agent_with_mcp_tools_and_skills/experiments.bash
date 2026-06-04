#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Pattern 3: Agent with MCP Tools and Skills
# ============================================================================

FRAMEWORK="langgraph"
PATTERN="agent_with_mcp_tools_and_skills"
# OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3:8b}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3.5:35b-a3b-coding-nvfp4}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
LOG_FILE_NAME="${LOG_FILE_NAME:-logs.txt}"
LOG_FILE="$(pwd)/$LOG_FILE_NAME"

export OLLAMA_MODEL
export OLLAMA_BASE_URL

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
echo "  HF_TOKEN=****${HF_TOKEN: -4}"
echo "  LOG_FILE=$LOG_FILE"
echo ""

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------

# Ensure dependencies are installed
uv sync --quiet

# Ensure embedding model is cached (for RAG tool)
echo "Ensuring embedding model is cached..."
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
echo "Embedding model ready."
echo ""

# Initialize log file with header
echo "# Pattern 3: Agent with MCP Tools and Skills - Experiment Logs" > "$LOG_FILE"
echo "# Started: $(date -Iseconds)" >> "$LOG_FILE"
echo "# Model: $OLLAMA_MODEL" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# ----------------------------------------------------------------------------
# Experiment Runner
# ----------------------------------------------------------------------------

run_experiment() {
    local name="$1"
    local question="$2"
    local expected_skill="$3"
    
    echo "----------------------------------------"
    echo "Running: $name"
    echo "Expected skill: $expected_skill"
    echo "Question: $question"
    echo ""
    
    # Capture start time (Python for macOS compatibility - date %N not supported)
    local start_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    
    # Run the agent and capture output (filter to JSON only)
    local raw_output
    raw_output=$(uv run python -m src.main --task "$name" --question "$question" 2>&1) || true
    
    # Extract only the JSON line (the final line starting with {)
    local json_output
    json_output=$(echo "$raw_output" | grep -E '^\{.*\}$' | tail -1)
    
    # Calculate duration (Python for macOS compatibility)
    local end_time=$(python3 -c "import time; print(int(time.time() * 1000))")
    local duration=$((end_time - start_time))
    
    # Log results
    echo "## $name" >> "$LOG_FILE"
    echo "Question: $question" >> "$LOG_FILE"
    echo "Expected Skill: $expected_skill" >> "$LOG_FILE"
    echo "Duration: ${duration}ms" >> "$LOG_FILE"
    echo '```json' >> "$LOG_FILE"
    # Pretty-print the JSON
    echo "$json_output" | python3 -m json.tool >> "$LOG_FILE" 2>/dev/null || echo "$json_output" >> "$LOG_FILE"
    echo '```' >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Print summary (show just the answer preview)
    local answer_preview
    answer_preview=$(echo "$json_output" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('answer','')[:100] + '...')" 2>/dev/null || echo "See log file")
    echo "Answer: $answer_preview"
    echo ""
}

# ----------------------------------------------------------------------------
# Experiments - Each targets a specific skill
# ----------------------------------------------------------------------------

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

# Skill: report-formatting (typically used with another skill)
run_experiment \
    "formatted_comparison_report" \
    "Create a professionally formatted report comparing the United States and China across all metrics." \
    "report-formatting"

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------

echo "========================================"
echo "Experiments complete!"
echo "Results logged to: $LOG_FILE"
echo "========================================"
