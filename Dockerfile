# Repo-Mind: Streamlit + Chroma; Ollama runs on the host (or another service).
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_HEADLESS=true \
    OLLAMA_BASE_URL=http://host.docker.internal:11434

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address", "0.0.0.0"]
