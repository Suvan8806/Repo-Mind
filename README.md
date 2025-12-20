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

## 🔍 How It Works: Hybrid Forensic RAG
Standard RAG on large repos suffers from vector crowding — thousands of historical commits can overshadow current source code in similarity searches.

### Repo-Mind's Dual-Stream Solution:

Stream A (Current Source): Queries filtered to hash: LATEST for up-to-date file implementations.
Stream B (Historical Context): Retrieves relevant commits and diffs to reveal intent, fixes, and "why" behind changes.

The LLM (Qwen2.5-Coder) acts as a Senior Forensic Auditor, cross-referencing both streams to:

Verify if past security fixes remain intact.
Detect architectural drift or unintended reversions.
Provide reasoned explanations with source references.

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
'''
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
'''

---

## 🛠️ Step-by-Step Setup Guide

## 1. Prerequisites
- Python 3.10 or higher
- [Ollama](https://ollama.com) installed and running
- NVIDIA GPU recommended for optimal performance (30+ tokens/sec)

## 2. Clone and Setup the Project

- git clone https://github.com/your-username/repo-mind.git  # Replace with your actual repo URL
'''bash
cd repo-mind
'''

Create and activate virtual environment
- python -m venv venv

On Windows:
- .\venv\Scripts\activate

On macOS/Linux:
- source venv/bin/activate

Install dependencies
- pip install -r requirements.txt


## 3. Pull Local AI Models
Repo-Mind uses local models via Ollama for privacy and speed:

LLM for code analysis and reasoning
'''
- ollama pull qwen2.5-coder:7b
'''

Embedding model for vector search
- ollama pull nomic-embed-text

## 4. Prepare the Target Repository
Clone the repository you want to audit into the data/repos/ directory:

- ' mkdir -p data/repos '
- cd data/repos

Example: Auditing the 'requests' library
- git clone https://github.com/psf/requests.git
- cd ../..

## 5. Ingest Data and Launch

Step A: Run the dual-stream ingestor

This processes Git history (commits/diffs) and current source code into the vector database
- python ingest_git.py

Step B: Launch the Streamlit UI

- streamlit run app.py

Open your browser to the provided local URL (usually http://localhost:8501) to start forensic queries.
