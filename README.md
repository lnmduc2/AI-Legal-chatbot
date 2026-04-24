# AI Legal MVP

A docs-grounded AI Legal chatbot prototype using LangChain Deep Agents and NiceGUI, now extended with a demo automation flow for legal document ingestion via Gmail.

## Quick Start

### Local advisory app only

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

uv sync
uv run -m app.main
```

Open [http://localhost:8080](http://localhost:8080).

### Full automation demo with two apps

1. Copy `.env.example` to `.env`.
2. Fill in:
   - `OPENAI_API_KEY`
   - `LEGAL_MAIL_SOURCE_EMAIL`
   - `LEGAL_MAIL_SOURCE_APP_PASSWORD`
   - `LEGAL_MAIL_ADMIN_EMAIL`
   - `LEGAL_MAIL_ADMIN_APP_PASSWORD`
   - `LEGAL_MAIL_TEAM_RECIPIENTS`
3. Make sure IMAP is enabled for the admin Gmail inbox and both Gmail accounts use App Passwords.
4. Start the stack:

```bash
docker compose up --build
```

Then open:

- `http://localhost:8080` for the advisory chat and `/events`
- `http://localhost:8081` for the fake legal-source portal

## Benchmark

Run the benchmark script to test 5 fixed questions against the loaded documents:

```bash
uv run python benchmark.py
```

## Architecture

```
app/
├── main.py         # NiceGUI entry point
├── source_main.py  # Fake legal-source entry point
├── ui.py           # Chat UI (Heineken-green theme)
├── agent.py        # DeepAgent service (checkpointer + summarization)
├── workspace.py    # Agent filesystem workspace
├── llm.py          # OpenAI-compatible model config
├── prompts.py      # System prompt + doc paths
├── config.py       # Environment and memory config
└── automation/     # Gmail, ingestion, event log, source UI, poller

docs/
├── law/            # Law documents
├── policy/         # Company policy
└── faq/            # FAQ examples

data/
├── event_log.json  # Automation event log
└── mail_state.json # Processed mail state and UID cursor
```

## Features

- **Docs-grounded answers**: Agent reads files directly, no RAG pipeline
- **Citation-aware**: Every answer cites document source and section
- **Session memory**: Conversation state persisted across turns via LangGraph `InMemorySaver` checkpointing, keyed by browser `session_id`
- **Auto-compression**: Summarization middleware activates when context exceeds the configured threshold, keeping recent turns verbatim
- **NiceGUI chat UI**: Heineken-green theme with thinking indicator and 60s timeout
- **Automation event log**: `/events` shows processed, ignored, and failed ingestion events
- **Fake source portal**: separate NiceGUI app sends realistic Gmail notices with markdown attachments
- **Background poller**: main app polls the admin Gmail inbox, ingests matching `.md` legal documents, refreshes doc indexes, and notifies the Legal team
- **Benchmark script**: 5 fixed questions (3 law + 2 policy) for validation

## Memory

Conversation memory uses built-in LangGraph/DeepAgents primitives:

- **Checkpointer**: `InMemorySaver` persists thread state across invocations using the browser `session_id` as `thread_id`
- **Summarization**: DeepAgents `SummarizationMiddleware` auto-summarizes older conversation turns when context exceeds the trigger threshold (default 80k tokens), keeping the most recent messages for short-term coherence
- **Session isolation**: Each browser session gets an isolated memory state; different sessions do not share context
- **Config**: Adjust thresholds in `app/config.py` (`CONTEXT_SUMMARIZE_TRIGGER_TOKENS`, `CONTEXT_KEEP_MESSAGES`)


## Demo
uv run -m app.main