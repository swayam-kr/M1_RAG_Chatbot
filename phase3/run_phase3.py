import json
import os
from chunker import process_and_chunk

def run_phase3():
    print("Step 1: Reading Sanitized Output from Phase 2...")
    
    p2_amc_path = os.path.join("..", "phase2", "sanitized_amc_data.json")
    p2_schemes_path = os.path.join("..", "phase2", "sanitized_schemes_data.json")
    
    if not os.path.exists(p2_amc_path) or not os.path.exists(p2_schemes_path):
        print(f"Error: Could not locate Phase 2 data at {p2_amc_path} or {p2_schemes_path}")
        return

    with open(p2_amc_path, "r", encoding="utf-8") as f:
        amc_data = json.load(f)
        
    with open(p2_schemes_path, "r", encoding="utf-8") as f:
        schemes_data = json.load(f)

    print("Step 2: Processing and Chunking AMC Data...")
    all_chunks = []
    
    # Process the overarching AMC data
    # Provide the main Groww AMC URL as the source reference for global data
    amc_chunks = process_and_chunk(amc_data, source_url="https://groww.in/mutual-funds/amc/groww-mutual-funds")
    all_chunks.extend(amc_chunks)
    
    print(f"  -> Generated {len(amc_chunks)} chunks from AMC Root.")

    print("Step 3: Processing and Chunking Individual Schemes Data...")
    for scheme in schemes_data:
        name = scheme.get("Scheme Name", "Unknown Scheme")
        
        # We need the original URL injected during Phase 1 for this specific scheme
        # Let's cross-reference amc_data's "Top 5 Funds by AUM" to extract the actual URL
        url = "Unknown URL"
        top_funds = amc_data.get("Top 5 Funds by AUM", [])
        for f in top_funds:
            # Match strictly based on scheme vs fund name mapping logic we fixed earlier
            if name.replace(" Direct Growth", "") in f.get("Fund Name", "") or f.get("Fund Name", "") in name:
                url = f.get("URL", "Unknown URL")
                break
                
        scheme_chunks = process_and_chunk(scheme, source_url=url)
        all_chunks.extend(scheme_chunks)
        print(f"  -> Generated {len(scheme_chunks)} chunks for {name}.")

    print(f"Step 4: Writing {len(all_chunks)} Total Semantic Chunks to output DB file...")
    with open("phase3_chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        
    print("Phase 3 complete! Semantic vectors ready for ML Embedding Phase 4.")

if __name__ == "__main__":
    run_phase3()
