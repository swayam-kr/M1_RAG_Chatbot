import schedule
import time
import subprocess
import os

def job():
    print("\n⏰ [SCHEDULER] Triggering Daily Groww Mutual Fund RAG Pipeline...")
    script_path = os.path.join(os.path.dirname(__file__), "run_pipeline.py")
    cwd = os.path.dirname(__file__)
    
    try:
        # Execute the orchestrator python script synchronously
        subprocess.run(
            ["python3", "run_pipeline.py"],
            cwd=cwd,
            check=True
        )
        # Store last refresh timestamp so the API can surface it
        ts_path = os.path.join(os.path.dirname(__file__), "last_refreshed.txt")
        with open(ts_path, "w") as f:
            from datetime import datetime
            f.write(datetime.now().isoformat())
        print("⏰ [SCHEDULER] Daily Pipeline Execution Succeeded.\n")
    except subprocess.CalledProcessError as e:
        print("⏰ [SCHEDULER] Daily Pipeline Execution FAILED.")
        print(e)
        
def start_scheduler():
    # Schedule the job every day at exactly 10:00 PM local time.
    # 10:00 PM is selected to scrape the mutual fund data after trading hours.
    print("Initializing Groww RAG Engine Scheduler...")
    print("Next execution is scheduled for: Everyday at 10:00 PM.")
    
    schedule.every().day.at("22:00").do(job)
    
    # Infinite loop to keep the scheduler watching the clock
    while True:
        schedule.run_pending()
        time.sleep(60) # Sleep 60 seconds to prevent CPU pinning

if __name__ == "__main__":
    start_scheduler()
