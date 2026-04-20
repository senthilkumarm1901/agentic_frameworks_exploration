# LangGraph Exploration

This project reproduces the runnable experiments from the article below against a local Ollama setup:

- https://senthilkumarm1901.github.io/learn_by_blogging/posts/langgraph_tutorial/2025-08-20-agentic-ai-oreilly.html

The implementation is script-first rather than notebook-first. It keeps the article's sequence, but uses current `langchain-ollama` support where that is more reliable than manual JSON parsing.

The local LLM used for the agent experiments is the Ollama MLX-compatible model `qwen3.5:35b-a3b-coding-nvfp4`.

## Experiments

### Graphs

- Graph 1: Hello world graph
- Graph 2: Multiple inputs graph
- Graph 3: Sequential graph
- Graph 4: Conditional graph
- Graph 5: Looping graph

### Agents

- Agent 1: Simple bot
- Agent 2: Chatbot with conversation memory
- Agent 3: ReAct arithmetic agent
- Agent 4: Drafter agent with save/update tools
- Agent 5: RAG agent over a PDF

## Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the project:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

3. Copy the environment template:

```bash
cp .env.example .env
```

4. Ensure Ollama is running and has both models available:

```bash
ollama list
```

Expected models:

- `qwen3.5:35b-a3b-coding-nvfp4`
- `nomic-embed-text`

### Running the MLX-Compatible Qwen Model

This repository is configured around the Ollama MLX-compatible `qwen3.5:35b-a3b-coding-nvfp4` model for the chat and tool-calling examples.

Typical requirements to run this model locally in a usable way are:

- Apple Silicon Mac recommended so Ollama can use Metal/MLX acceleration effectively.
- High unified memory capacity. A 35B-class model is most comfortable on 64 GB RAM, and 48 GB is a practical lower bound for reduced concurrency or smaller context usage.
- Recent Ollama for macOS with the model already pulled locally.
- Sufficient free disk space for model storage, caches, and embeddings.

If your machine cannot comfortably host a 35B model, swap in a smaller Ollama model in your local configuration, but expect different tool-calling quality and response behavior.

5. For the RAG experiment, place the PDF at `./data/Stock_Market_Performance_2024.pdf` or override `PDF_PATH` in `.env`.

## Run Commands

### Graphs

```bash
python -m lang_graph_exploration.graphs.hello_world
python -m lang_graph_exploration.graphs.multiple_inputs
python -m lang_graph_exploration.graphs.sequential
python -m lang_graph_exploration.graphs.conditional
python -m lang_graph_exploration.graphs.looping
```

### Agents

```bash
python -m lang_graph_exploration.agents.simple_bot --prompt "Hello there"
python -m lang_graph_exploration.agents.chatbot --prompts "Hi my name is Senthil" "What is my name?"
python -m lang_graph_exploration.agents.react_agent --prompt "Add 40 + 12 and then multiply the result by 6. Also tell me a joke please."
python -m lang_graph_exploration.agents.drafter_agent --prompt "Write a short email about written communication." --save-as written_communication.txt
python -m lang_graph_exploration.agents.rag_agent --question "How did Tesla perform in the 2024 stock market?"
python -m lang_graph_exploration.agents.rag_agent --question "How did Tesla perform in the 2024 stock market?" --rebuild --verbose
```

### Tests

```bash
pytest
```

## Results

### Experiment #1 - Simple Bot

```bash
% source .venv/bin/activate && python -m lang_graph_exploration.agents.simple_bot --prompt "Say hello in one sentence."


Hello!
```

### Experiment #2 - Multiple Inputs Graph

```bash
% python -m lang_graph_exploration.graphs.multiple_inputs


{'values': [0, 1, 1, 2, 3, 5], 'name': 'Senthil', 'result': 'Hi there Senthil, Your sum is 12'}
```

### Experiment #3 - ReAct Agent

```bash
% python -m lang_graph_exploration.agents.react_agent --prompt "Add 40 + 12 and then multiply the result by 6. Also tell me a joke please."


The result of adding 40 + 12 and then multiplying by 6 is 312.

Here's a joke for you:
Why don't scientists trust atoms? Because they make up everything!
```

### Experiment #4 - Drafter Agent

```bash
% python -m lang_graph_exploration.agents.drafter_agent --prompt "Write a short email about why written communication matters in no more than 5 sentences." --save-as written_communication.txt


Written communication is essential because it provides a clear, permanent record of our conversations and decisions. Unlike verbal exchanges, written messages allow recipients to review information at their own pace, ensuring better understanding and retention. This clarity helps prevent misunderstandings and creates accountability across teams and organizations. Furthermore, written communication bridges time zones and languages, enabling seamless collaboration in a global environment. Ultimately, mastering written expression is a foundational skill for professional success and effective leadership.
```

### Experiment #5 - RAG Agent

```bash
% python -m lang_graph_exploration.agents.rag_agent --question "How did Tesla perform in the 2024 stock market?" --rebuild --verbose


Tesla's stock performance in 2024 was characterized by a dramatic turnaround, with virtually all of its gains occurring in the fourth quarter.

Here are the key details regarding Tesla's performance in 2024:

- Mid-year struggles: By mid-2024, Tesla's shares had fallen substantially from their late-2023 levels. This decline was driven by the company cutting vehicle prices to stimulate demand, which put pressure on its profit margins.
- Fourth quarter surge: The trend reversed dramatically in the final months of the year. Tesla's stock skyrocketed following the U.S. presidential election in November 2024. The election outcome, which resulted in a more business-friendly administration, bolstered market sentiment for high-growth and tech stocks.
- Record highs: Fueled by optimism regarding economic conditions in 2025 and hopes for renewed demand and pricing power in the EV market, Tesla's shares rallied sharply. By December 2024, the stock was trading near record highs, briefly touching an all-time closing high of approximately $480 per share in mid-December.
- Yearly gain: The stock effectively doubled from its lows earlier in the year, ending the year in the low $400s.

Source: Stock Market Performance 2024.pdf, Page 4.
```

## Notes

- The graph examples are deterministic and safe to run without Ollama.
- The agent scripts support both interactive and one-shot CLI usage so they can be validated non-interactively.
- ReAct, Drafter, and RAG prefer native Ollama tool calling through `langchain-ollama`. 