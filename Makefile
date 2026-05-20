.PHONY: setup run eval report clean

FRAMEWORK ?= langgraph
TYPE ?= workflow
PATTERN ?= routing

# Setup all Python environments
setup:
	@echo "Setting up _shared..."
	cd _shared && uv venv && uv pip install -e .
	@echo "Setting up eval harness..."
	cd eval && uv venv && uv pip install -e .
	@echo "Setting up $(FRAMEWORK)/$(TYPE)/$(PATTERN)..."
	cd $(FRAMEWORK)/$(TYPE)/$(PATTERN) && uv venv && uv pip install -e .

# Setup a single leaf
setup-leaf:
	cd $(FRAMEWORK)/$(TYPE)/$(PATTERN) && uv venv && uv pip install -e .

# Run a single pattern
run:
	cd $(FRAMEWORK)/$(TYPE)/$(PATTERN) && uv run python src/main.py --task $(PATTERN)

# Run full evaluation across all frameworks and patterns
eval:
	cd eval && uv run python -m eval.runner --runs 3

# Generate comparison report
report:
	cd eval && uv run python -m eval.report

# Build all Rust crates
build-rust:
	cd rig && cargo build --release --workspace

clean:
	find . -name ".venv" -type d -exec rm -rf {} + 2>/dev/null || true
	cd rig && cargo clean 2>/dev/null || true
