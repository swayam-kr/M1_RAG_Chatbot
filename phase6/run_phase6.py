import sys
import os

# Ensure we can import Phase 5 intent guards
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'phase5')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'phase2')))

from intent_guard import guard_query
from sanitizer import sanitize_text
from retriever import retrieve_top_k
from generator import generate_answer

def interactive_chat():
    print("==================================================")
    print("Phase 6 End-to-End Terminal Chat Interface")
    print("Type 'exit' to quit.")
    print("==================================================")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            if not user_input.strip():
                continue
                
            # 1. Sanitize
            safe_query = sanitize_text(user_input)
            
            # 2. Guardrails
            refusal = guard_query(safe_query)
            if refusal:
                print(f"\nAssistant (Guardrail blocked): {refusal}")
                continue
                
            # 3. Retrieve
            print("\n[Searching ChromaDB...]")
            chunks = retrieve_top_k(safe_query, k=4)
            if not chunks:
                print("Assistant: I cannot access the database. Are you sure Phase 4 ran?")
                continue
                
            # Displaying retrieved sources computationally
            sources = set([c['metadata'].get('source_url') for c in chunks])
            print(f"[Retrieved {len(chunks)} chunks from {len(sources)} sources]")
            
            # 4. Generate
            print("[Generating via Gemini 1.5 Flash...]")
            answer = generate_answer(safe_query, chunks)
            
            print(f"\nAssistant: {answer}")
            print("\nSources used:")
            for s in sources:
                print(f" - {s}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nSystem Error: {e}")

if __name__ == "__main__":
    interactive_chat()
