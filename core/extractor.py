import git
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