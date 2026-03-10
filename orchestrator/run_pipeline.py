import subprocess
import os
import time

def run_phase(phase_dir, script_name):
    print(f"\n==============================================")
    print(f"🚀 INITIALIZING {phase_dir.upper()} - {script_name}")
    print(f"==============================================")
    
    script_path = os.path.join(os.path.dirname(__file__), "..", phase_dir, script_name)
    cwd = os.path.join(os.path.dirname(__file__), "..", phase_dir)
    
    start_time = time.time()
    import sys
    try:
        # Run the python script explicitly
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        duration = time.time() - start_time
        print(f"✅ {phase_dir.upper()} Completed Successfully in {duration:.2f} seconds.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR in {phase_dir.upper()}!")
        print(e.stderr)
        raise

def main():
    print("Starting Groww Mutual Fund RAG Master Pipeline...")
    overall_start = time.time()
    
    try:
        # Phase 1: Web Scraping Engine
        run_phase("phase1", "run_phase1.py")
        
        # Phase 2: Data Sanitization (Privacy Filter)
        run_phase("phase2", "run_phase2.py")
        
        # Phase 3: Text Processing and Chunking
        run_phase("phase3", "run_phase3.py")
        
        # Phase 4: Vectorization & Local Storage (ChromaDB)
        run_phase("phase4", "run_phase4.py")
        
        # Write the final success timestamp so the Next.js API can read it
        ts_path = os.path.join(os.path.dirname(__file__), "last_refreshed.txt")
        from datetime import datetime
        with open(ts_path, "w") as f:
            f.write(datetime.now().isoformat())
            
        print("\n==============================================")
        print("🚀 AUTOMATING GITHUB DATA SYNC FOR RENDER")
        print("==============================================")
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            # Stage the localized text data
            subprocess.run(
                ["git", "add", "orchestrator/last_refreshed.txt", "phase1", "phase2", "phase3", "orchestrator/scheduler.log"], 
                cwd=repo_root, 
                check=True
            )
            # Check if there are changes to commit
            status_result = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True)
            if status_result.stdout.strip():
                subprocess.run(["git", "commit", "-m", "chore: Nightly automated data ingestion sync"], cwd=repo_root, check=True)
                subprocess.run(["git", "push", "origin", "main"], cwd=repo_root, check=True)
                print("✅ Successfully pushed fresh data to GitHub. Render and Vercel will now auto-deploy!")
            else:
                print("ℹ️ No new data changes detected to push.")
        except subprocess.CalledProcessError as e:
            print("❌ Git Sync Error:", e)
            print("Continuing despite Git error...")

        overall_duration = time.time() - overall_start
        print(f"\n🎉 MASTER PIPELINE FINISHED SUCCESSFULLY! Total time: {overall_duration:.2f} seconds.")
        print("💡 The Vector Database is now fully updated and armed with fresh data.")
        
    except Exception as e:
        print("🚨 PIPELINE HALTED DUE TO ERROR.")

if __name__ == "__main__":
    main()
