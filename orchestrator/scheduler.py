import schedule
import time
import subprocess
import os

def job():
    print("\n⏰ [SCHEDULER] Triggering Daily Groww Mutual Fund RAG Pipeline...")
    script_path = os.path.join(os.path.dirname(__file__), "run_pipeline.py")
    cwd = os.path.dirname(__file__)
    
    import sys
    try:
        # Execute the orchestrator python script synchronously
        subprocess.run(
            [sys.executable, "run_pipeline.py"],
            cwd=cwd,
            check=True
        )
        print("⏰ [SCHEDULER] Daily Pipeline Execution Succeeded.\n")
    except subprocess.CalledProcessError as e:
        print("⏰ [SCHEDULER] Daily Pipeline Execution FAILED.")
        print(e)
        
def start_scheduler():
    # Schedule the job every day at the given time. 22:00 is default production time.
    schedule_time = os.environ.get("SCHEDULE_TIME", "22:00")
    print("Initializing Groww RAG Engine Scheduler...")
    print(f"Next execution is scheduled for: Everyday at {schedule_time}.")
    
    schedule.every().day.at(schedule_time).do(job)
    
    # Infinite loop to keep the scheduler watching the clock
    while True:
        schedule.run_pending()
        time.sleep(5) # Sleep 5 seconds to be highly responsive for testing

if __name__ == "__main__":
    start_scheduler()
