# Production Deployment Guide

Deploying this architecture requires an understanding of the persistence constraints of modern cloud platforms. Because this project utilizes a **Local Vector Database (ChromaDB)** that writes to a local SQLite file system (`phase4/db`), the deployment strategy must be split into two parts: Frontend and Backend.

**Why a Split Architecture?**
Vercel hosts Serverless Functions, which destroy their hard drives after every request. If we deployed the Python backend to Vercel, the local vector database would be wiped instantly, resulting in constant errors. Therefore, the Python backend must live on a platform supporting containerized workflows (like Render), while the Next.js UI lives on Vercel.

---

## Step 0: Push Code to GitHub (Required)
Both Vercel and Render deploy directly from GitHub.

1. Create a new empty repository on **GitHub** (e.g., `groww-rag-chatbot`).
2. Run the following commands in your terminal at the root of `M1_RAG_Chatbot`:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Production"
   git branch -M main
   # Replace the URL below with your actual GitHub repo URL
   git remote add origin https://github.com/your-username/groww-rag-chatbot.git
   git push -u origin main
   ```

---

## Step 1: Deploy Backend (FastAPI + ChromaDB) on Render

Render will host the Python API, scrape data daily, and maintain the vector database in memory while its container is alive.

### 1. Create Web Service
1. Log into **Render.com** and go to your Dashboard.
2. Click **New +** -> **Web Service**.
3. Connect your GitHub account and select your `groww-rag-chatbot` repository.

### 2. Configure Settings
Fill out the configuration page exactly like this:
*   **Name:** `groww-rag-api` (or any name you like)
*   **Language:** Python 3
*   **Branch:** `main`
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `./render_start.sh`

*(Note: The `render_start.sh` file runs the pipeline once on startup to build the database, launches the daily scheduler in the background, and boots the FastAPI server.)*

### 3. Environment Variables
Scroll down to **Environment Variables** and add:
*   **Key:** `GROQ_API_KEY`
*   **Value:** `[Paste your Groq API Key here]`

### 4. Deploy
1. Click **Create Web Service**. 
2. Wait a few minutes. Render will install dependencies, install Playwright, run the initial pipeline (scraping and chunking), and finally output: `Application startup complete`.
3. Locate your public URL at the top left (e.g., `https://groww-rag-api.onrender.com`), and copy it.

---

## Step 2: Deploy Frontend (Next.js) on Vercel

Once your backend is live, deploying the Next.js React app to Vercel takes 1 minute.

1. Go to **Vercel.com** and click **Add New...** -> **Project**.
2. Import your `groww-rag-chatbot` GitHub repository.
3. 🚨 **CRITICAL: Configure Project**
   *   Under "Framework Preset", ensure **Next.js** is selected.
   *   Next to **Root Directory**, click **Edit** and change it to `phase7`.
4. **Environment Variables**
   *   Expand the Environment Variables section and add:
   *   **Key:** `BACKEND_URL` 
   *   **Value:** The Render URL you copied in Step 1 (e.g., `https://groww-rag-api.onrender.com`). *Ensure there is no trailing slash.*
5. Click **Deploy**.

Vercel will build the React app and give you a live frontend URL. Your RAG Chatbot is now fully functional in production!
