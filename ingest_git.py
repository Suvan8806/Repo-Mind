import os
import shutil
from core.extractor import get_current_source_tree, get_git_history
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from config import SETTINGS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def get_current_source_tree(repo_path):
    from langchain_core.documents import Document
    source_docs = []
    # We want to be thorough
    valid_exts = {'.py'} 
    
    print(f"📂 Scanning directory: {os.path.abspath(repo_path)}")
    
    for root, dirs, files in os.walk(repo_path):
        if '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                # print(f"  📄 Found file: {file}") # Uncomment to see every file found
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                    content = f"FILE_PATH: {full_path}\nTYPE: Current Source Code\nCONTENT:\n{code}"
                    source_docs.append(Document(
                        page_content=content, 
                        metadata={"hash": "LATEST", "file": file, "type": "source"}
                    ))
    return source_docs

def build_git_db():

    print("🚀 Starting Git History Ingestion...")
    repo_path = os.path.join("data", "repos", "requests")
    
    # 1. Get History (The "Why")
    history_docs = get_git_history(repo_path, max_commits=1000)
    
    # 2. Get Source Tree (The "What")
    # Make sure this function is defined above!
    source_docs = get_current_source_tree(repo_path)
    
    # --- IMPORTANT: VITAL CHECK ---
    print(f"📦 DEBUG: Found {len(history_docs)} History Commits")
    print(f"📦 DEBUG: Found {len(source_docs)} Current Source Files")
    
    if len(source_docs) == 0:
        print("❌ ERROR: No source files found! Check your repo_path.")
        return 

    raw_docs = history_docs + source_docs
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