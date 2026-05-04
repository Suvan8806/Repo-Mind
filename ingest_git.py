import os
import shutil
import git
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


def _safe_index_id(repo_abs: str) -> str:
    base = os.path.basename(os.path.normpath(repo_abs))
    if not base or base in (".", ".."):
        base = "repo"
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in base)


def _resolve_repo_input(raw: str) -> str | None:
    raw = raw.strip().strip('"').strip("'")
    if not raw:
        return None
    cwd = os.getcwd()
    if os.path.isabs(raw):
        cand = os.path.normpath(raw)
        return cand if os.path.isdir(cand) else None
    if "/" in raw or "\\" in raw:
        cand = os.path.normpath(os.path.join(cwd, raw))
        return cand if os.path.isdir(cand) else None
    cand = os.path.normpath(os.path.join(cwd, "data", "repos", raw))
    if os.path.isdir(cand):
        return cand
    cand = os.path.normpath(os.path.join(cwd, raw))
    return cand if os.path.isdir(cand) else None


def iter_all_git_history_docs(repo_path: str):
    """Every commit on all branches with a patch diff — no keyword filter."""
    repo = git.Repo(repo_path)
    for commit in repo.iter_commits("--all"):
        try:
            diff = repo.git.show(commit.hexsha, patch=True, unified=3)
            if "diff --git" not in diff and "diff --cc" not in diff:
                continue
            diff_text = str(diff)[:50000]
            content = f"COMMIT_ID: {commit.hexsha[:7]}\n"
            content += f"AUTHOR: {commit.author}\n"
            content += f"SUMMARY: {commit.message.strip()}\n"
            content += f"CODE_CHANGES:\n{diff_text}"
            metadata = {"hash": commit.hexsha[:7], "author": str(commit.author)}
            yield Document(page_content=content, metadata=metadata)
        except Exception as e:
            print(f"⚠️ Skip commit {commit.hexsha[:7]}: {e}")


def build_git_db():

    print("🚀 Starting Git History Ingestion...")
    raw = input(
        "Repository to ingest (name under data/repos, e.g. LIDA, or a full path): "
    ).strip()
    repo_path = _resolve_repo_input(raw)
    if not repo_path:
        print(f"❌ Could not resolve repository path from: {raw!r}")
        return

    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        abs_path = os.path.abspath(repo_path)
        print("❌ Not a Git clone (missing .git). Clone the repo first, e.g.:")
        print(f'   git clone https://github.com/psf/requests.git "{abs_path}"')
        if os.path.isdir(repo_path):
            print(f"   (Folder exists but is not a repo: remove it or init/clone inside it.)")
        return

    persist_dir = os.path.normpath(
        os.path.join(SETTINGS["db_path"], _safe_index_id(repo_path))
    )

    print(f"📌 Index id: {_safe_index_id(repo_path)} → vectors: {persist_dir}")

    # 1. Get History (The "Why") — all commits on all branches
    history_docs = list(iter_all_git_history_docs(repo_path))
    
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
    
    # 4. Wipe only this index (do not delete other ingested repos)
    if os.path.exists(persist_dir):
        print(f"🧹 Clearing existing database at {persist_dir}...")
        shutil.rmtree(persist_dir)
        
    # 5. Build Vector Store in Batches
    # This is critical for RTX 3050 stability to prevent OOM/Timeout errors
    print(f"🧠 Embedding chunks into ChromaDB (using {SETTINGS['embed_model']})...")
    
    # Initialize the DB with the first batch
    batch_size = 50
    vector_db = Chroma.from_documents(
        documents=docs[:batch_size],
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    # Add remaining batches
    for i in range(batch_size, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        vector_db.add_documents(batch)
        print(f"  ✅ Indexed {i + len(batch)}/{len(docs)} chunks...")
    
    print(f"🏁 Success! Repo-Mind is ready.")

if __name__ == "__main__":
    build_git_db()