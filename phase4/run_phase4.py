import json
import os
from vectorizer import store_chunks

def run_phase4():
    print("Step 1: Ingesting Semantic Chunks from Phase 3...")
    
    p3_chunks_path = os.path.join("..", "phase3", "phase3_chunks.json")
    
    if not os.path.exists(p3_chunks_path):
        print(f"Error: Could not locate Phase 3 chunks at {p3_chunks_path}")
        return

    with open(p3_chunks_path, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    if not chunks_data:
        print("Error: Phase 3 chunks are empty.")
        return
        
    print(f"Loaded {len(chunks_data)} explicit text chunk objects.")
    
    print("Step 2: Vectorizing and Persisting into Local Database...")
    store_chunks(chunks_data)
    
    print("Phase 4 complete! All semantic vectors proudly reside in ChromaDB ready for dynamic querying.")

if __name__ == "__main__":
    run_phase4()
