"""
retriever.py
------------
Handles query embedding and retrieval from all three Chroma collections.
Returns ranked results with source metadata and similarity scores.
"""

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K_RESULTS", 5))

COLLECTIONS = ["osha", "manuals", "job_history"]


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def load_collections(embeddings):
    """Load all three Chroma collections."""
    collections = {}
    for name in COLLECTIONS:
        try:
            collections[name] = Chroma(
                collection_name=name,
                embedding_function=embeddings,
                persist_directory=CHROMA_PERSIST_DIR
            )
        except Exception as e:
            print(f"[WARN] Could not load collection '{name}': {e}")
    return collections


def retrieve(query: str, collections: dict, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve top-k results from all collections.
    Returns a list of dicts with: content, source, collection, score.
    Sorted by similarity score descending.
    """
    results = []

    for collection_name, vectorstore in collections.items():
        try:
            docs_and_scores = vectorstore.similarity_search_with_score(query, k=top_k)
            for doc, score in docs_and_scores:
                # Chroma returns L2 distance; convert to similarity (lower = more similar)
                # Normalize to 0-1 range where 1 = most similar
                similarity = max(0.0, 1.0 - score)
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "collection": collection_name,
                    "score": round(similarity, 4),
                    "metadata": doc.metadata
                })
        except Exception as e:
            print(f"[WARN] Retrieval failed for collection '{collection_name}': {e}")

    # Sort by similarity score, highest first
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k * len(COLLECTIONS)]  # Return top results across all collections


def detect_conflicts(results: list[dict]) -> bool:
    """
    Simple conflict detection: check if top results come from different
    collections and have similar scores (within 0.1 of each other).
    This is a heuristic — expand in eval phase based on real conflicts found.
    """
    if len(results) < 2:
        return False

    top_results = results[:3]
    collections_seen = set(r["collection"] for r in top_results)
    top_scores = [r["score"] for r in top_results]

    # Conflict if: multiple collections in top results AND scores are close
    multiple_sources = len(collections_seen) > 1
    scores_close = (max(top_scores) - min(top_scores)) < 0.15

    return multiple_sources and scores_close
