import os
import json
from vectorizer import store_chunks, get_db_client, COLLECTION_NAME, get_embedding_function

def test_chroma_db_initialization_and_search():
    # 1. Create Mock Vector Data
    mock_chunks = [
        {"page_content": "Groww Large Cap Fund has a very high risk profile.", "metadata": {"source_url": "url1", "fund_name": "Groww LCF", "scraped_at_timestamp": "now"}},
        {"page_content": "The exit load for Liquid fund is zero if redeemed after 7 days.", "metadata": {"source_url": "url2", "fund_name": "Groww LF", "scraped_at_timestamp": "now"}},
        {"page_content": "Fund manager Anupam Tiwari manages the Large Cap fund.", "metadata": {"source_url": "url3", "fund_name": "Groww LCF", "scraped_at_timestamp": "now"}}
    ]
    
    # 2. Store Chunks (which tests purging, Collection creation, and BGE embedding generation)
    collection = store_chunks(mock_chunks)
    
    assert collection.count() == 3, f"Expected 3 vectors, found {collection.count()}"
    
    # 3. Test Vector Search
    embed_fn = get_embedding_function()
    query = "Who manages the Large Cap fund?"
    query_vector = embed_fn.embed_query(query)
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=1
    )
    
    # We expect the 'Anupam Tiwari' string to be the most relevant (top 1) result
    retrieved_content = results['documents'][0][0]
    assert "Anupam Tiwari" in retrieved_content, f"Similarity search failed. Top match was: {retrieved_content}"
    
    # 4. Assert Persistence
    client = get_db_client()
    collections = [c.name for c in client.list_collections()]
    assert COLLECTION_NAME in collections, f"{COLLECTION_NAME} did not persist correctly."
    
    print("Phase 4 Vector database verification tests passed strictly!")

if __name__ == "__main__":
    test_chroma_db_initialization_and_search()
