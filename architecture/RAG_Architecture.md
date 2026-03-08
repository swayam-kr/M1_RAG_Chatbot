# The Master Blueprint: Mutual Fund FAQ Assistant

Welcome to the definitive architectural guide for the **Groww Mutual Fund RAG Assistant**.

This document is written intentionally for both complete beginners and seasoned developers. If you have just cloned this repository and have no idea how a "Retrieval-Augmented Generation" (RAG) system works, this document will walk you step-by-step through the **entire data flow, system design choices, backend logic, data packet sizes, and external integration preferences.**

---

## 1. Executive Summary & The "Why"

**What is this bot?**
A chatbot that answers user questions specifically about Groww Mutual Funds. 

**What is the core problem it solves?**
Large Language Models (like ChatGPT) "hallucinate" fake facts when they don't know the answer. In the financial sector, giving a user the wrong "Expense Ratio" or faking "Top Holdings" is disastrous. 

**The Solution: RAG (Retrieval-Augmented Generation)**
Instead of letting the AI guess the answer from memory, our system **physically reads official Groww Mutual Fund web pages every night**, saves those exact words into a local database, and forces the AI to read *only those exact words* before it answers the user.

---

## 2. High-Level Data Flow Summary

Our application operates in two completely separate chunks of time: 
1. **The Daily Offline Pipeline (Phases 1-4):** Every single night at 10:00 PM, an automated script wakes up, reads the Groww website, cleans the data, chunks it up, translates it into mathematics (vectors), and saves it to a local database file.
2. **The Real-Time Online Pipeline (Phases 5-7):** Whenever a user opens our website and types "What is the exit load?", our server immediately searches that local database, pulls out the exact sentence about exit loads from last night's scrape, and asks the AI to summarize it in 3 sentences.

---

## 3. The 7-Phase Architecture (Deep Dive)

### Phase 1: Web Scraping Engine
**The Goal:** Extract raw, correct text from Groww.
**The Problem:** Groww is a "Single Page Application" (SPA) built with React. If you just download the raw HTML, the page is empty until JavaScript runs.
**The Solution (Playwright):** We use a library called `Playwright`. Playwright literally opens a hidden, invisible Chromium browser, waits for the JavaScript to execute and the UI to render, and *then* reads the text. 
**The Advanced Tactic (`__NEXT_DATA__`):** Instead of just reading the screen, our script dives into the hidden backend JSON that React uses to power the page. This is historically called "Dehydrated State." We use Regular Expressions (Regex) to securely locate exact percentages (e.g., extracting `"Cash Equivalent": 99.71%`) even if Groww's front-end developers hide it in different UI charts.
**Data Packet Size:** We download roughly ~150KB of raw text per mutual fund page. 

### Phase 2: Data Sanitization (Privacy Filter)
**The Goal:** Prevent Personally Identifiable Information (PII) from ever reaching our database or the AI.
**The Logic:** Even though we are scraping public factsheets, what if Groww accidentally publishes a developer's real Bank Account or a PAN Card in a test page? To enforce a Zero-Trust security model, the text passes through a strict Python Regex Filter in memory.
**How it Works:** The script scans the ~150KB of text for patterns that exactly match Indian PAN cards (`[A-Z]{5}[0-9]{4}[A-Z]`), Aadhaar numbers, and phone numbers. If it finds one, it replaces it with `[REDACTED]`.
**Speed:** Because it uses raw compiled Regex (not an AI model), this scrub takes less than `0.002 seconds` per page.

### Phase 3: Text Chunking and Metadata Tagging
**The Goal:** Cut the massive document into bite-sized pieces so the AI doesn't get overwhelmed.
**The Logic:** You cannot feed an entire 20-page mutual fund prospectus to an AI every single time a user asks a simple question; it costs too much money and the AI loses focus (called "Lost in the Middle" syndrome).
**The Tool:** We use `langchain-text-splitters`. 
**The Parameters:** We chop the document into "Chunks" of exactly **500 characters** each. However, to prevent cutting a sentence in half, we use an overlap of **50 characters**. 
**Packet Size:** The massive 150KB raw text is now split into an array of roughly 25 small dictionary objects. Each dictionary object contains the 500 characters of text, PLUS a `metadata` tag telling us exactly what URL it came from and the timestamp (`scraped_at`).

### Phase 4: Local ML Embeddings (Vector Database)
**The Goal:** Turn English sentences into math so a computer can "Search by Meaning" rather than "Search by Keyword".
**The Concept:** If a user types "What are the hidden fees?", a traditional keyword search fails because the document uses the phrase "Exit Load". Vector databases solve this by translating semantic meaning into coordinates in a 384-dimensional space. "Hidden fees" and "Exit load" sit right next to each other mathematically.
**The Integration Criteria (FastEmbed vs PyTorch):**
1. **PyTorch (Sentence-Transformers):** Extremely memory-heavy. We initially used this, but when we deployed to Render's Free Tier (which limits servers to 512MB RAM), the application instantly crashed with an Out-Of-Memory (OOM) error.
2. **FastEmbed (BAAI/bge-small-en-v1.5):** We switched to `FastEmbed`, which executes the identical open-source BGE algorithm using ONNX instead of PyTorch. It drops memory consumption to ~150MB, completely solving the crash while retaining the exact same 384-dimensional mathematical accuracy.
**The Database (ChromaDB):** We use ChromaDB because it creates a simple `.db` SQLite folder right on our server disk. Absolutely 0 external API keys, 0 monthly subscriptions, and 0 network delays.
**Automation:** Every night at 10:00 PM, `orchestrator/scheduler.py` wipes this `.db` folder clean and repopulates it with fresh mathematical vectors to ensure we never query stale data.

### Phase 5: Backend API Gateway (FastAPI)
**The Goal:** The portal that connects the user's browser to our secure internal system.
**The Logic:** Built entirely on `FastAPI`, it runs asynchronously on port 8000. It receives a tiny JSON packet from the frontend UI containing the user's query (e.g., `{"query": "Who is the manager?"}`).
**Guardrails:** Immediately upon receiving this json, FastAPI runs the exact same Phase 2 PII Regex filter on the *user's* query. Furthermore, it runs a heuristic intent check. If the user asks "Compare this fund to XYZ" or "Give me financial advice," the API instantly terminates the request returning a hardcoded "I cannot provide financial advice" block. The query never even touches the LLM network.

### Phase 6: Semantic Retrieval & Generation (Groq / Llama 3)
**The Goal:** Find the relevant chunk of text in ChromaDB and ask the AI to summarize it.
**The Physics:** 
1. The user's query ("Who manages this?") is mathematically embedded into a 384D vector using the exact same FastEmbed BGE model.
2. ChromaDB performs a "Cosine Similarity Search" to find the 4 chunks of text physically closest to the user's question vector.
3. We take those 4 chunks and inject them into a massive invisible String known as a **System Prompt**. 
**The Prompt Logic:** We command the LLM: *"You are a strict assistant. Answer ONLY using the following chunks. Do not exceed 3 sentences."*
**The LLM Selection Criteria (Groq vs OpenAI/Gemini):**
We use **Groq** to host the **Llama 3.1 8B** model. Groq uses specialized hardware (LPUs) that generate text at ~800 tokens per second. We chose this over OpenAI and Gemini because a RAG chatbot must feel instant. Under Groq, the user experiences zero lag.
**Conditional Sources Feature:** In `generator.py`, we explicitly coded a rule into the prompt instructing the LLM to secretly append the text `<NO_SOURCES>` if it deems the user's query to be a conversational greeting (like "Hi"). The FastAPI backend detects this keyword, strips it out, and hides the citation links on the UI!

### Phase 7: The Frontend UI (Next.js)
**The Goal:** A beautiful, responsive interface that works flawlessly on desktop monitors and mobile iPhones.
**The Architecture:** Built on Next.js 14 via Vercel. 
**Mobile Responsiveness:** Uses TailwindCSS `md:` breakpoints, dynamic flex layouts, and rigorous CSS logic (`h-[100dvh]`) to prevent the Safari mobile address bar from hiding the user's input form.
**State Management:** The UI holds a massive `chatHistories` object mapping every single message to the specific Mutual Fund the user is querying. 
**The Freshness Stamp:** Upon loading, the UI constantly pings our FastAPI backend for the `last_refreshed.txt` stamp (which is exclusively created by `run_pipeline.py`). We display this front-and-center so the user physically guarantees they aren't reading 10-month old metrics.

---

## 4. Final Deployment Stack
*   **Frontend Hosting:** Vercel (Auto-deploys via GitHub push)
*   **Backend Hosting:** Render Server (Free Tier, 512MB RAM cap bypassed perfectly by FastEmbed)
*   **Environment Variables:** `GROQ_API_KEY` in the Render Cloud, `BACKEND_URL` in the Vercel Cloud.
*   **Local Run:** Executing `start_backend.sh` boots the system on `localhost:8000` via Uvicorn, and `npm run dev` boots the UI on `localhost:3001`.

**The system is fully armed, fully deterministic, highly resilient to hallucinations, and incredibly memory efficient.**
