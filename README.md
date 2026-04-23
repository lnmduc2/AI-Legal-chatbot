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
├── agent.py        # DeepAgent service (checkpointer + summarization)
├── workspace.py    # Agent filesystem workspace
├── llm.py          # OpenAI-compatible model config
├── prompts.py      # System prompt + doc paths
└── config.py       # Environment and memory config

docs/
├── law/            # Law documents
├── policy/         # Company policy
└── faq/            # FAQ examples
```

## Features

- **Docs-grounded answers**: Agent reads files directly, no RAG pipeline
- **Citation-aware**: Every answer cites document source and section
- **Session memory**: Conversation state persisted across turns via LangGraph `InMemorySaver` checkpointing, keyed by browser `session_id`
- **Auto-compression**: Summarization middleware activates when context exceeds the configured threshold, keeping recent turns verbatim
- **NiceGUI chat UI**: Heineken-green theme with thinking indicator and 60s timeout
- **Benchmark script**: 5 fixed questions (3 law + 2 policy) for validation

## Memory

Conversation memory uses built-in LangGraph/DeepAgents primitives:

- **Checkpointer**: `InMemorySaver` persists thread state across invocations using the browser `session_id` as `thread_id`
- **Summarization**: DeepAgents `SummarizationMiddleware` auto-summarizes older conversation turns when context exceeds the trigger threshold (default 80k tokens), keeping the most recent messages for short-term coherence
- **Session isolation**: Each browser session gets an isolated memory state; different sessions do not share context
- **Config**: Adjust thresholds in `app/config.py` (`CONTEXT_SUMMARIZE_TRIGGER_TOKENS`, `CONTEXT_KEEP_MESSAGES`)


## Demo
uv run -m app.main