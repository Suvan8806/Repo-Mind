# Repo-Mind: Local RAG Forensic Tool

**Repo-Mind** is a local-first AI assistant for repository analysis. It cross-references **Git history** (commit diffs and intent) with **current source code** so you can ask forensic-style questions: regressions, how a fix evolved, and whether past changes still appear in the tree.

All inference runs on your machine via **Ollama**; vectors live in **ChromaDB** under `local_memory/`.

---

<img width="1895" height="882" alt="image" src="https://github.com/user-attachments/assets/78c75e39-5a61-425b-9235-77c273229c2a" />

## Features

- **Hybrid retrieval**: Similarity search splits **current source** (`hash == LATEST`) and **historical commits** (`hash != LATEST`) so both appear in context.
- **Full-history ingest**: Walks **`git log --all`** and indexes commits that include a patch (`diff --git` / `diff --cc`) — no keyword filter on commit messages.
- **Interactive ingest**: Prompts for which repo to index (name under `data/repos/` or a full path).
- **Per-repo indexes**: Each ingest writes vectors to `local_memory/<repo_basename>/` so multiple repos do not overwrite each other.
- **Streamlit UI**: Sidebar **ingestion** dropdown to choose which index to query; model choice, `k`, latency and chunk metrics.
- **Docker**: One-command run with `docker compose`; Ollama stays on the host (GPU/RAM friendly).

---

## How it works

1. **Ingest** embeds chunked commit diffs plus the current `.py` tree into Chroma.
2. **Query** embeds your question with the same Ollama embedding model, retrieves top‑`k` chunks from both streams, and sends them to the LLM with a forensic-style system prompt.

Default models (override in `config.py`):

| Role | Default (`config.py`) |
|------|------------------------|
| Embeddings | `snowflake-arctic-embed` |
| LLM | `qwen2.5-coder:1.5b` |

---

## Prerequisites

- **Git**
- **[Ollama](https://ollama.com)** installed and running on the host
- **Docker Desktop** (or Docker Engine + Compose) — only if you use the container workflow
- Optional: **Python 3.11+** for running without Docker

Pull the models you use (at minimum the defaults above):

```bash
ollama pull snowflake-arctic-embed
ollama pull qwen2.5-coder:1.5b
```

Pull any extra tags you select in the Streamlit UI (e.g. `qwen2.5-coder:7b`).

---

## Clone

```bash
git clone https://github.com/Suvan8806/Repo-Mind.git
cd Repo-Mind
```

Use the folder that contains `docker-compose.yml`, `Dockerfile`, and `app.py`.

---

## Run with Docker (recommended)

From the project root:

```bash
docker compose up --build
```

Open **http://localhost:8501**

The container uses **`OLLAMA_BASE_URL=http://host.docker.internal:11434`** so it talks to Ollama on your machine. **Linux**: `extra_hosts` in `docker-compose.yml` maps `host.docker.internal` to the host gateway.

**Ingest** (interactive; use a **second** terminal while the app keeps running):

```bash
docker compose run --rm -it repo-mind python ingest_git.py
```

`-it` is required for the repo path prompt.

**Stop** the app: `Ctrl+C` in the first terminal, or `docker compose down`.

---

## Run without Docker

```bash
python -m venv .venv
```

Windows: `.\.venv\Scripts\activate`  
macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
streamlit run app.py
```

Ingest:

```bash
python ingest_git.py
```

---

## Prepare a repository to index

Clone (or copy) a **git** repo under `data/repos/` so layout is:

```text
data/repos/<YourRepo>/.git/...
```

Example:

```bash
mkdir -p data/repos
cd data/repos
git clone https://github.com/org/project.git YourRepo
cd ../..
```

Run ingest and enter **`YourRepo`** when asked (or paste an absolute path). Vectors are written to **`local_memory/YourRepo/`**.

In the Streamlit sidebar, choose **Ingestion to use (Chroma index)** — each subdirectory of `local_memory/` is one index.

---

## Configuration

Edit **`config.py`**:

| Key | Purpose |
|-----|---------|
| `db_path` | Parent folder for Chroma stores (default `local_memory`). Indexes are `db_path/<repo_name>/`. |
| `embed_model` | Ollama embedding model (must match what you used at ingest). |
| `llm_model` | Default LLM tag in the UI. |
| `ollama_base_url` | Set via **`OLLAMA_BASE_URL`** or **`OLLAMA_HOST`** env (default `http://127.0.0.1:11434`). Docker sets this to reach the host. |

---

## Project layout

```text
Repo-Mind/
├── app.py              # Streamlit UI + hybrid RAG
├── ingest_git.py       # Interactive ingest; Git history + current source
├── config.py           # Models, db_path, Ollama base URL
├── agent.py            # Optional CLI-style RAG helper
├── core/
│   └── extractor.py    # Legacy keyword-filtered history (unused by main ingest path)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/
│   └── repos/          # Clone targets (gitignored contents; keep .gitkeep)
└── local_memory/       # Chroma per-repo dirs (gitignored)
```

---

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| Empty ingestion dropdown | Run ingest once; ensure `local_memory/<name>/` exists. |
| Bad retrieval | Same embedding model at ingest and query; re-ingest after changing `embed_model`. |
| Docker cannot reach Ollama | Ollama running on host; port **11434**; check `OLLAMA_BASE_URL`. |
| Ingest prompt does nothing | Use **`-it`** with `docker compose run`. |

---

## License

Add your license here if applicable.
