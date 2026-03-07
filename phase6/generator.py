import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

# Load API key once at module level (not per request)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SYSTEM_PROMPT = """
You are a highly restricted, factual Mutual Fund assistant for Groww Mutual Funds. 

RULES:
1. MAX LENGTH: Your answer must be 3 sentences or fewer. No exceptions.
2. CONVERSATIONAL: If the user asks a generic greeting (like "Hi" or "What can you do"), introduce yourself politely as the Groww Mutual Fund Assistant.
3. RAG FACTUALITY: If the user asks specific questions about Mutual Funds, AUM, NAV, or managers, you must ONLY answer using the exact provided context. 
4. OUT OF CONTEXT FALLBACK: If the provided context does not contain the answer, you MUST respond exactly with this string: "Oops, I don't think I have idea about this. Please let me know if you want to know anything about Groww Mutual Fund AMC in general or about any of the top existing schemes in it like Groww Large Cap Fund, Groww Multicap Fund, Groww Liquid Fund, Groww Nifty EV ETF, or Groww Overnight Fund."
5. NO ADVICE: Never provide financial advice, NEVER suggest investments, and NEVER predict future returns.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT
)

# ── Singleton LLM: created once, reused across all requests ──
_llm = None

def get_llm():
    """Returns a cached Groq LLM instance. Created once, reused for all requests."""
    global _llm
    if _llm is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file. Get your free key at https://console.groq.com")
        # llama-3.1-8b-instant: fastest Groq model, ideal for short factual RAG responses
        _llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.0,
            max_tokens=200,
            groq_api_key=api_key
        )
    return _llm

def generate_answer(query: str, retrieved_chunks: list) -> str:
    llm = get_llm()
    
    context_blocks = []
    for c in retrieved_chunks:
        context_blocks.append(f"[Source: {c['metadata'].get('source_url', 'Unknown')}]\n{c['content']}\n")
        
    compiled_context = "\n".join(context_blocks)
    prompt = prompt_template.format(context=compiled_context, question=query)
    
    response = llm.invoke(prompt)
    return response.content
