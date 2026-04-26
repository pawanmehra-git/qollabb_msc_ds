# Ansira

NLP-based automated customer service chatbot for a book shop. It answers FAQs, helps users browse and order books, checks or cancels orders, and falls back to a local LLM (Ollama **Mistral**) for open-ended questions. All persistence uses JSON files under `data/`—no database.

## Features

- **Streamlit** chat UI with sidebar (name for orders, chat preview, analytics, optional admin JSON view)
- **Ollama** integration with `generate_response(prompt, context)` for grounded replies
- **FAQ** search (`faq.json`) via keyword overlap + fuzzy scoring; LLM assists when no strong match
- **Catalog & orders** (`books.json`, `orders.json`): browse, filter by genre/author/price, place orders with stock checks, status lookup, cancel with stock restore
- **Intent routing**: FAQ, book search, order placement, order status, cancel order, general (LLM)
- **Logging** (`chat_logs.json`): each turn plus counters for total queries, book searches, orders placed
- **Extras**: “You may also like…” by genre, conversation history passed into the LLM, optional structured extraction for messy order phrases

## Project layout

```text
msc/
├── app/
│   ├── __init__.py
│   ├── main.py       # Streamlit app
│   ├── chatbot.py    # Intents, entities, routing
│   ├── llm.py        # Ollama HTTP API
│   ├── faq.py
│   ├── books.py
│   ├── orders.py
│   ├── logger.py
│   └── utils.py      # JSON helpers
├── data/
│   ├── faq.json
│   ├── books.json
│   ├── orders.json
│   └── chat_logs.json
├── requirements.txt
└── README.md
```

## Setup

### 1. Python environment

```bash
cd msc
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Ollama

Install the Ollama application for your OS from [https://ollama.com](https://ollama.com) and ensure it is running (system tray / service).

### 3. Pull the Mistral model

```bash
ollama pull mistral
```

### 4. Run the app

From the **project root** (`msc/`):

```bash
streamlit run app/main.py
```

The browser should open at `http://localhost:8501`.

## Configuration (optional)

| Environment variable | Default | Purpose |
|----------------------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `mistral` | Model name passed to Ollama |

## Deterministic Ansira model (recommended)

To make the chatbot's answers more consistent, create a wrapper model with fixed sampling parameters.

1. Build the model from the provided Modelfile:

```bash
ollama create ansira-mistral-deterministic -f ollama/AnsiraMistralDeterministic/Modelfile
```

2. Use it in the app (set `OLLAMA_MODEL`):

```bash
setx OLLAMA_MODEL ansira-mistral-deterministic
```

You can also override sampling at runtime via environment variables:
`OLLAMA_TEMPERATURE`, `OLLAMA_TOP_K`, `OLLAMA_TOP_P`, `OLLAMA_SEED`.

## Example prompts

- *What are your store hours?* (FAQ)
- *Show me fiction books* or *Books by James Clear* (browse)
- *I want to buy 2 copies of Atomic Habits* (order — set your name in the sidebar for the customer field)
- *Check my order 10002* (status)
- *Cancel my order 10002* (cancel — only if status is `Placed`)

## Development notes

- JSON reads/writes use atomic replace in `save_json`; missing files get safe defaults when loading.
- Place orders only when intent matches purchase patterns (e.g. *copies of*, *buy 2 …*) so generic “buy books” queries still route to browse or the LLM.
- Ensure Ollama is reachable before relying on LLM answers; the app surfaces a clear message if the daemon is down.

## License

Use and modify for your own projects as needed.
