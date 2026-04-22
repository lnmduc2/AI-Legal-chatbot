# AI Legal MVP

A docs-grounded AI Legal chatbot prototype using LangChain Deep Agents and NiceGUI.

## Quick Start

```bash
# 1. Copy and configure environment variables
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# 2. Install dependencies and run the app
uv run app/main.py

# 3. Open http://localhost:8080 in your browser
```

## Benchmark

Run the benchmark script to test 5 fixed questions against the loaded documents:

```bash
uv run python benchmark.py
```

## Architecture

```
app/
├── main.py         # NiceGUI entry point
├── ui.py           # Chat UI (Heineken-green theme)
├── agent.py        # DeepAgent service
├── workspace.py    # Agent filesystem workspace
├── llm.py          # OpenAI-compatible model config
├── memory.py       # Visible filesystem memory
├── prompts.py      # System prompt + doc paths
└── config.py       # Environment and path config

docs/
├── law/            # Law documents
├── policy/         # Company policy
└── faq/            # FAQ examples

demo_memory/        # Visible conversation memory
```

## Features

- **Docs-grounded answers**: Agent reads files directly, no RAG pipeline
- **Citation-aware**: Every answer cites document source and section
- **Visible memory**: Session Q&A persisted to `demo_memory/` as JSON files
- **NiceGUI chat UI**: Heineken-green theme with thinking indicator and 60s timeout
- **Benchmark script**: 5 fixed questions (3 law + 2 policy) for validation
