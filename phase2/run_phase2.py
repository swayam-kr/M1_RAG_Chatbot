import json
import os
from sanitizer import sanitize_json

def run_phase2():
    print("Step 1: Ingesting Raw Data from Phase 1...")
    p1_amc_path = os.path.join("..", "phase1", "amc_data.json")
    p1_schemes_path = os.path.join("..", "phase1", "all_schemes_data.json")
    
    if not os.path.exists(p1_amc_path) or not os.path.exists(p1_schemes_path):
        print(f"Error: Could not locate Phase 1 data at {p1_amc_path} or {p1_schemes_path}")
        return

    with open(p1_amc_path, "r", encoding="utf-8") as f:
        amc_data = json.load(f)
        
    with open(p1_schemes_path, "r", encoding="utf-8") as f:
        schemes_data = json.load(f)

    print("Step 2: Scrubbing PII from AMC Data (In-Memory)...")
    clean_amc = sanitize_json(amc_data)
    
    print("Step 3: Scrubbing PII from All Schemes Data (In-Memory)...")
    clean_schemes = sanitize_json(schemes_data)
    
    print("Step 4: Writing Secured Outputs to Phase 2 Datastore...")
    with open("sanitized_amc_data.json", "w", encoding="utf-8") as f:
        json.dump(clean_amc, f, indent=2, ensure_ascii=False)
        
    with open("sanitized_schemes_data.json", "w", encoding="utf-8") as f:
        json.dump(clean_schemes, f, indent=2, ensure_ascii=False)
        
    print("Phase 2 complete. Secure sanitized files saved locally.")

if __name__ == "__main__":
    run_phase2()
