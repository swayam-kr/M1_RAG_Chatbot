from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
from datetime import datetime

# Add phase2 into the path so we can import the sanitizer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'phase2')))

from sanitizer import sanitize_text
from intent_guard import guard_query, HARDCODED_REFUSAL

app = FastAPI(title="Phase 5 - RAG intent API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the timestamp file written by the scheduler
LAST_REFRESHED_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'orchestrator', 'last_refreshed.txt')
)

def get_last_refreshed() -> str:
    """Read last scheduler run timestamp from file. Returns a formatted string."""
    try:
        with open(LAST_REFRESHED_PATH, "r") as f:
            raw = f.read().strip()
        dt = datetime.fromisoformat(raw)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return "Not yet run"

class ChatRequest(BaseModel):
    query: str
    selected_fund: Optional[str] = None  # e.g. "Groww Multicap Fund" or None for "All Funds"

class ChatResponse(BaseModel):
    status: str
    message: str
    answer: str = None
    sources: list = []
    last_refreshed: str = ""

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    raw_query = request.query
    selected_fund = request.selected_fund

    if not raw_query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # ── Step 1: PII check on RAW query (before redaction strips the patterns) ──
    pii_refusal = guard_query(raw_query)
    if pii_refusal:
        return ChatResponse(
            status="blocked",
            message="PII or Prohibited Intent Detected",
            answer=pii_refusal,
            last_refreshed=get_last_refreshed()
        )

    # ── Step 2: Sanitize (redact PII tokens even if check passed) ──
    sanitized_query = sanitize_text(raw_query)
        
    # Phase 6 Integration: Retrieve and Generate
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'phase6')))
        from retriever import retrieve_top_k
        from generator import generate_answer
        
        # Pass the selected fund so the retriever can apply a hard source_url filter
        chunks = retrieve_top_k(sanitized_query, k=4, selected_fund=selected_fund)
        
        if isinstance(chunks, str):
            # This means retriever.py returned a Python stack trace
            return ChatResponse(
                status="error",
                message="Render Python Backend Crashed",
                answer=f"**CRITICAL PYTHON ERROR:**\n\n```python\n{chunks}\n```",
                sources=[],
                last_refreshed=get_last_refreshed()
            )

        if not chunks:
            return ChatResponse(
                status="error",
                message="No context retrieved from ChromaDB. Is Phase 4 complete?",
                answer="I'm sorry, my database is offline.",
                sources=[],
                last_refreshed=get_last_refreshed()
            )
            
        sources = list(set([c['metadata'].get('source_url') for c in chunks if c['metadata'].get('source_url')]))
        
        answer = generate_answer(sanitized_query, chunks)
        
        # If the generated answer is the explicit Fallback, suppress sources
        if "Oops, I don't think I have idea about this" in answer:
            sources = []
        
        return ChatResponse(
            status="allowed",
            message="Success",
            answer=answer,
            sources=sources,
            last_refreshed=get_last_refreshed()
        )
    except Exception as e:
        import traceback
        print("======== GENERATION ERROR ========", flush=True)
        traceback.print_exc()
        print(f"Error Message: {str(e)}", flush=True)
        print("==================================", flush=True)
        
        return ChatResponse(
            status="error",
            message=f"Internal Generation Error: {str(e)}",
            answer="I encountered an error synthesizing the response.",
            last_refreshed=get_last_refreshed()
        )

@app.get("/api/status")
async def status_endpoint():
    return {"status": "online", "last_refreshed": get_last_refreshed()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
