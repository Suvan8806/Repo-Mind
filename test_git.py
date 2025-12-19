import git
import os

# Set this to your actual requests folder path
repo_path = os.path.join("data", "repos", "requests")

def test_extraction():
    try:
        repo = git.Repo(repo_path)
        # Testing a specific known commit that has a Proxy fix
        commit_hash = "38f3f8e" 
        
        print(f"🧐 Checking Commit: {commit_hash}")
        
        # This is exactly what your extractor does
        diff = repo.git.show(commit_hash, patch=True, unified=3)
        
        if "diff --git" in diff:
            print("✅ SUCCESS: Found code diff!")
            print("-" * 30)
            # Print the first 500 characters of the diff to see the + and - signs
            print(diff[:500])
            print("-" * 30)
        else:
            print("❌ FAILURE: Diff found but contains no code changes.")
            
    except Exception as e:
        print(f"❌ ERROR: Could not access repo or commit. {e}")

if __name__ == "__main__":
    test_extraction()