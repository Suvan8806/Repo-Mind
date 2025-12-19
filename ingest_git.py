import os
import shutil
from core.extractor import get_git_history
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from config import SETTINGS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def build_git_db():
    print("🚀 Starting Git History Ingestion...")
    
    # 1. Extract raw documents from Git
    repo_path = os.path.join("data", "repos", "requests")
    raw_docs = get_git_history(repo_path, max_commits=1000)
    
    # 2. Text Splitting with "Sticky" Metadata logic
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=200,
        separators=["COMMIT_ID:", "CODE_CHANGES:", "\ndiff", "\n@@", "\n", " ", ""]
    )
    
    docs = []
    for raw_doc in raw_docs:
        split_chunks = text_splitter.split_text(raw_doc.page_content)
        commit_hash = raw_doc.metadata.get("hash", "Unknown")
        
        for chunk in split_chunks:
            # Re-attach the header to every chunk to ensure UI clarity
            if "COMMIT_ID" not in chunk:
                full_text = f"COMMIT_ID: {commit_hash} (Cont.)\n{chunk}"
            else:
                full_text = chunk
                
            docs.append(Document(page_content=full_text, metadata=raw_doc.metadata))
            
    print(f"✂️ Split {len(raw_docs)} commits into {len(docs)} chunks.")

    # 3. Setup Embeddings
    embeddings = OllamaEmbeddings(model=SETTINGS["embed_model"])
    
    # 4. Wipe old memory
    if os.path.exists(SETTINGS["db_path"]):
        print(f"🧹 Clearing existing database at {SETTINGS['db_path']}...")
        shutil.rmtree(SETTINGS["db_path"])
        
    # 5. Build Vector Store in Batches
    # This is critical for RTX 3050 stability to prevent OOM/Timeout errors
    print(f"🧠 Embedding chunks into ChromaDB (using {SETTINGS['embed_model']})...")
    
    # Initialize the DB with the first batch
    batch_size = 50
    vector_db = Chroma.from_documents(
        documents=docs[:batch_size],
        embedding=embeddings,
        persist_directory=SETTINGS["db_path"]
    )
    
    # Add remaining batches
    for i in range(batch_size, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        vector_db.add_documents(batch)
        print(f"  ✅ Indexed {i + len(batch)}/{len(docs)} chunks...")
    
    print(f"🏁 Success! Repo-Mind is ready.")

if __name__ == "__main__":
    build_git_db()