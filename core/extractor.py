import git
import os
from langchain_core.documents import Document

def get_git_history(repo_path, max_commits=200):
    repo = git.Repo(repo_path)
    docs = []
    target_keywords = ["fix", "security", "auth", "header", "ssl", "redirect", "proxy", "cve", "leak"]
    commits = list(repo.iter_commits(max_count=2000)) 
    
    for commit in commits:
        msg = commit.message.lower()
        if any(word in msg for word in target_keywords):
            try:
                # Use --patch to force the code diff to show up
                diff = repo.git.show(commit.hexsha, patch=True, unified=3)
                
                # Check if we actually got code
                if "diff --git" not in diff:
                    continue

                # Ensure we have a clean string and cap it
                diff_text = str(diff)[:2000]
                
                content = f"COMMIT_ID: {commit.hexsha[:7]}\n"
                content += f"AUTHOR: {commit.author}\n"
                content += f"SUMMARY: {commit.message.strip()}\n"
                content += f"CODE_CHANGES:\n{diff_text}" # Label must match what LLM expects
                
                metadata = {"hash": commit.hexsha[:7], "author": str(commit.author)}
                docs.append(Document(page_content=content, metadata=metadata))
            except Exception as e:
                print(f"Error extracting {commit.hexsha[:7]}: {e}")
                continue
            
            if len(docs) >= max_commits:
                break
    return docs

def get_current_source_tree(repo_path):
    """Recursively pulls the latest version of all Python files."""
    source_docs = []
    # Extension whitelist to avoid ingesting binaries or junk
    valid_exts = {'.py', '.md', '.txt', '.yaml'}
    
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden folders like .git
        if '.git' in root: continue
        
        for file in files:
            if any(file.endswith(ext) for ext in valid_exts):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        # We label it as SOURCE_FILE so the AI knows this is current state
                        content = f"FILE: {file}\nPATH: {full_path}\nTYPE: Current Source Code\nCONTENT:\n{code}"
                        source_docs.append(Document(
                            page_content=content, 
                            metadata={"hash": "CURRENT", "file": file}
                        ))
                except Exception as e:
                    print(f"Skipping {file}: {e}")
    return source_docs