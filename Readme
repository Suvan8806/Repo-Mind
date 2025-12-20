# 🧠 Repo-Mind: Local RAG Forensic Tool

**Repo-Mind** is a high-performance, local-first AI auditor designed for deep-dive forensic analysis of software repositories. Unlike standard AI assistants that only see the current state of code, Repo-Mind cross-references **historical Git intent** (from commits and diffs) with **active source code** to identify security regressions, architectural drift, and reverted fixes.

---

## 🚀 Key Features

- **Forensic Auditing**: Automatically compares historical bug fixes and security patches (via Git diffs) against current implementations to detect regressions.
- **Hybrid Retrieval Engine**: A custom "Dual-Stream" RAG pipeline that balances historical commits and live source files using metadata-aware filtering (e.g., `hash: LATEST` for current code).
- **Local & Private**: Fully powered by **Ollama** — your proprietary code and Git history never leave your machine.
- **High-Performance Telemetry**: Real-time monitoring of token throughput, latency, and resource utilization.
- **Streamlit UI**: Interactive forensic interface for querying and visualizing results.

---

## 📊 Performance Benchmarks

*Tested on: NVIDIA RTX 3050 (6GB VRAM) | Model: Qwen2.5-Coder-7B*

| Metric              | Result                          |
|---------------------|---------------------------------|
| **Inference Speed** | ~31.5 tokens/sec                |
| **Search Depth**    | k=20 (Hybrid Context Split)     |
| **Vector Store**    | ChromaDB (Persistent)           |
| **Embedding Model** | nomic-embed-text                |

---

## 📂 Project Structure
repo-mind/
├── data/
│   └── repos/
│       └── <target-repo>/  # Clone the repository to analyze here (e.g., requests)
├── db/                     # Automatically created by ChromaDB for persistent storage
├── app.py                  # Streamlit Forensic UI & core RAG logic
├── ingest_git.py           # Dual-stream ingestor (Git history + current source code)
├── requirements.txt        # Project dependencies
└── README.md               # This documentation
text
