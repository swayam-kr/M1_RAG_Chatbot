import os
import chromadb
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

DB_DIR = os.path.join(os.path.dirname(__file__), "db")
COLLECTION_NAME = "mutual_funds"

# ── Singletons: initialized once at module import, reused across all requests ──
_embedding_fn = None
_db_client = None

def get_embedding_function():
    """Returns a cached instance of the BGE embedding model.
    First call takes ~2-4s (model load); every subsequent call is instant.
    """
    global _embedding_fn
    if _embedding_fn is None:
        print("Loading FastEmbed BGE Model locally (first time only)...")
        _embedding_fn = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        print("FastEmbed BGE Model loaded and cached.")
    return _embedding_fn

def get_db_client():
    """Returns a cached ChromaDB persistent client."""
    global _db_client
    if _db_client is None:
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        _db_client = chromadb.PersistentClient(path=DB_DIR)
    return _db_client

def store_chunks(chunks):
    """
    Purges existing DB daily collection, instantiates the embedding model,
    and upserts all vectorized chunks.
    """
    client = get_db_client()
    
    # Drop existing collection to ensure absolute freshness (Purge Mechanics)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Purged existing collection '{COLLECTION_NAME}'.")
    except Exception as e:
        print(f"Collection '{COLLECTION_NAME}' does not exist yet. Proceeding.")

    embed_fn = get_embedding_function()
    
    # Create the clean collection
    collection = client.create_collection(name=COLLECTION_NAME)
    
    documents = []
    metadatas = []
    ids = []
    
    for i, c in enumerate(chunks):
        documents.append(c["page_content"])
        metadatas.append(c["metadata"])
        ids.append(f"chunk_{i}")
        
    print(f"Generating 384D vectors for {len(documents)} documents. This might take a moment...")
    embeddings = embed_fn.embed_documents(documents)
    
    print(f"Upserting vectors into ChromaDB at {DB_DIR}...")
    collection.upsert(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    print("Vector database successfully populated.")
    return collection
