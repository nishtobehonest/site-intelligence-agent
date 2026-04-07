"""
retriever.py
------------
Handles query embedding and retrieval from all three Chroma collections.
Returns ranked results with source metadata and similarity scores.
"""

import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

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
                # Chroma returns L2 distance for unit-normalized vectors (sentence-transformers).
                # Correct conversion to cosine similarity: cosine_sim = 1 - (L2_dist² / 2)
                similarity = max(0.0, 1.0 - (score ** 2) / 2)
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
    Conflict detection: two heuristics checked in order.

    1. Cross-collection conflict (top 3): results from different collections
       with scores within 0.15 of each other. Catches OSHA vs manual disagreements.

    2. Within-collection version conflict (top 6): multiple source files from
       the same collection with their best scores within 0.15 of each other.
       Catches two versions of the same manual (e.g., carrier-48lc-2017 vs 2023).
    """
    if len(results) < 2:
        return False

    # --- Heuristic 1: cross-collection (authoritative sources only) ---
    # job_history is anecdotal (field notes); it should not conflict with
    # authoritative specs from osha or manuals collections.
    AUTHORITATIVE = {"osha", "manuals"}
    top3_auth = [r for r in results[:3] if r["collection"] in AUTHORITATIVE]
    if len(top3_auth) >= 2:
        auth_collections = set(r["collection"] for r in top3_auth)
        auth_scores = [r["score"] for r in top3_auth]
        if len(auth_collections) > 1 and (max(auth_scores) - min(auth_scores)) < 0.15:
            return True

    # --- Heuristic 2: within-collection version conflict ---
    # For each collection, find distinct source files in the top-6 window.
    # If a collection has results from 2+ source files with close best scores,
    # flag as conflict (likely two versions of the same document).
    top6 = results[:6]
    by_collection: dict[str, dict[str, float]] = {}
    for r in top6:
        col = r["collection"]
        src = r["source"]
        if col not in by_collection:
            by_collection[col] = {}
        # Track best score per source file
        if src not in by_collection[col] or r["score"] > by_collection[col][src]:
            by_collection[col][src] = r["score"]

    for col, source_scores in by_collection.items():
        if len(source_scores) > 1:
            scores = list(source_scores.values())
            # Require at least one source to have a meaningful score; avoids
            # triggering on low-scoring noise spread across multiple documents.
            if max(scores) >= 0.50 and (max(scores) - min(scores)) < 0.15:
                return True

    return False
