import schedule
import time
import subprocess
import os
import sys
from datetime import datetime

def job():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n==============================================")
    print(f"⏰ [{current_time}] Triggering Daily Groww Mutual Fund RAG Pipeline...")
    print(f"==============================================\n")
    sys.stdout.flush()
    
    cwd = os.path.dirname(__file__)
    
    try:
        # Execute the orchestrator python script synchronously
        subprocess.run(
            [sys.executable, "run_pipeline.py"],
            cwd=cwd,
            check=True
        )
        finish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ [{finish_time}] Daily Pipeline Execution Succeeded.\n")
    except subprocess.CalledProcessError as e:
        error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n❌ [{error_time}] Daily Pipeline Execution FAILED.")
        print(e)
    
    sys.stdout.flush()
        
def start_scheduler():
    # Schedule the job every day at the given time. 22:00 is default production time.
    schedule_time = os.environ.get("SCHEDULE_TIME", "22:00")
    
    startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{startup_time}] Initializing Groww RAG Engine Background Scheduler...")
    print(f"[{startup_time}] Next execution is scheduled for: Everyday at {schedule_time}.")
    sys.stdout.flush()
    
    schedule.every().day.at(schedule_time).do(job)
    
    # Infinite loop to keep the scheduler watching the clock
    while True:
        schedule.run_pending()
        time.sleep(5) # Sleep 5 seconds to be highly responsive for testing

if __name__ == "__main__":
    start_scheduler()
