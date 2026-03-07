import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'phase4')))
from vectorizer import get_db_client, COLLECTION_NAME, get_embedding_function

# Load fund URL mapping from amc_data.json once at module level
_AMC_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'phase1', 'amc_data.json'))
_AMC_URL = "https://groww.in/mutual-funds/amc/groww-mutual-funds"

def _load_fund_url_map() -> dict:
    """Returns a dict of {fund_name_lower: source_url} using amc_data.json"""
    try:
        with open(_AMC_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        url_map = {}
        for fund in data.get("Top 5 Funds by AUM", []):
            name = fund.get("Fund Name", "").strip().lower()
            url = fund.get("URL", "").strip()
            if name and url:
                url_map[name] = url
        return url_map
    except Exception as e:
        print(f"[retriever] Warning: Could not load amc_data.json: {e}")
        return {}

_FUND_URL_MAP = _load_fund_url_map()


def retrieve_top_k(query: str, k: int = 4, selected_fund: str = None):
    """
    Vectorizes the user query and searches ChromaDB for the top K matching factual chunks.

    If selected_fund is provided (and is not "All Funds"), applies a hard equality filter
    on source_url so that only chunks from that specific fund are returned.
    Falls back to heuristic AMC/scheme routing when no fund is explicitly selected.
    """
    client = get_db_client()
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print("Database collection not found. Please ensure Phase 4 ran successfully.")
        return []

    embed_fn = get_embedding_function()
    query_vector = embed_fn.embed_query(query)

    # --- Priority 1: Hard filter when a specific fund is selected by the user ---
    where_filter = None

    if selected_fund and selected_fund.strip().lower() not in ("", "all funds"):
        fund_key = selected_fund.strip().lower()
        # Try exact match first, then partial match
        matched_url = _FUND_URL_MAP.get(fund_key)
        if not matched_url:
            for name, url in _FUND_URL_MAP.items():
                if fund_key in name or name in fund_key:
                    matched_url = url
                    break
        
        if matched_url:
            # Lock the retrieval strictly to this fund's source URL
            where_filter = {"source_url": matched_url}
        else:
            # Fund selected but URL not found — don't restrict (fallback to heuristics)
            print(f"[retriever] Warning: No URL mapping for selected_fund='{selected_fund}'")

    # --- Priority 2: Heuristic routing when no fund is explicitly selected ---
    if where_filter is None:
        query_lower = query.lower()

        scheme_keywords = [
            "scheme", "large cap", "nifty", "liquid", "multicap", "ev",
            "automotive", "overnight", "nav", "sip", "expense ratio",
            "exit load", "lock-in", "minimum", "holdings", "sector"
        ]
        amc_keywords = [
            "amc", "groww mutual fund", "ceo", "aum", "sponsor",
            "total aum", "overall", "company", "trustee", "compliance"
        ]

        is_scheme_query = any(kw in query_lower for kw in scheme_keywords)
        is_amc_query = any(kw in query_lower for kw in amc_keywords)

        if is_amc_query and not is_scheme_query:
            where_filter = {"source_url": _AMC_URL}
        elif is_scheme_query:
            where_filter = {"source_url": {"$ne": _AMC_URL}}
        elif "fund" in query_lower:
            where_filter = {"source_url": {"$ne": _AMC_URL}}
        # else: no filter — search across all vectors

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where_filter
    )

    chunks = []
    if results and results.get("documents") and len(results["documents"]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, dists):
            chunks.append({
                "content": doc,
                "metadata": meta,
                "distance": dist
            })

    return chunks
