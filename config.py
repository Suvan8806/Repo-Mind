SETTINGS = {
    "db_path": "local_memory",
    "embed_model": "snowflake-arctic-embed", # Use this official one
    # Ollama loads the full model into RAM; 7B often needs ~4+ GiB free. Use 1.5b on low-memory machines.
    "llm_model": "qwen2.5-coder:1.5b",
    "chunk_size": 800,
    "chunk_overlap": 200,
    "repo_path": "C:\\Users\\suvan\\Desktop\\Desktop\\vs code\\ACM\\ACM-Projects"
}