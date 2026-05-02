"""
LISA — RAG Memory (Gemini embeddings — matches ChromaDB)
"""

import os, time
from pathlib import Path
import chromadb
from google import genai
from dotenv import load_dotenv
from config.settings import VECTORDB_DIR, RAG_TOP_K, RAG_DISTANCE_CUTOFF

load_dotenv()
gemini_client   = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
EMBEDDING_MODEL = "gemini-embedding-001"
COLLECTION_NAME = "lisa_chats"

_client     = None
_collection = None

def _get_collection():
    global _client, _collection
    if _collection is None:
        _client     = chromadb.PersistentClient(path=str(VECTORDB_DIR))
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection

def _embed(text: str):
    for attempt in range(3):
        try:
            r = gemini_client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
            return r.embeddings[0].values
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep((attempt+1)*3)
            else:
                print(f"[RAG] Embed error: {e}")
                return None
    return None

def get_style_context(user_message: str, top_k: int = RAG_TOP_K) -> str:
    try:
        collection = _get_collection()
    except Exception as e:
        print(f"[RAG] Load error: {e}")
        return ""

    emb = _embed(user_message)
    if emb is None:
        return ""

    try:
        results   = collection.query(
            query_embeddings=[emb], n_results=top_k,
            include=["documents", "distances"]
        )
    except Exception as e:
        print(f"[RAG] Query error: {e}")
        return ""

    docs  = results.get("documents", [[]])[0]
    dists = results.get("distances",  [[]])[0]
    if not docs:
        return ""

    relevant = [d for d, dist in zip(docs, dists) if dist < RAG_DISTANCE_CUTOFF] or docs[:2]
    return "[Past conversation examples — inhi ki tarah style mein reply karna]\n\n" + "\n\n".join(relevant)