"""
assistant.py
------------
Main assistant pipeline. Wires together retrieval, confidence scoring,
LLM generation, and graceful degradation routing.

Usage:
    from src.assistant import FieldServiceAssistant
    assistant = FieldServiceAssistant()
    result = assistant.ask("What is the lockout/tagout procedure for a Carrier RTU-48XL?")
    print(result["response"])
"""

import os
from dotenv import load_dotenv

from src.retriever import get_embeddings, load_collections, retrieve
from src.confidence import score_confidence
from src.degradation import route
from src import llm

load_dotenv()

SYSTEM_PROMPT = """You are a Field Service Intelligence Assistant helping technicians, inspectors, and field engineers retrieve accurate information during a job.

Your rules:
1. Answer ONLY based on the provided context. Do not use outside knowledge.
2. If the context does not contain enough information to answer, say so explicitly. Do not guess or fabricate.
3. Always cite your source (document name or section) in your answer.
4. Use plain, direct language. Technicians need clear instructions, not corporate language.
5. If a procedure involves safety risks, flag it explicitly.
6. Keep answers concise. If the procedure has steps, use a numbered list.

If you cannot answer reliably from the context provided, respond with:
"I do not have sufficient information in my documents to answer this reliably. Please contact your office or supervisor."
"""


def build_context_block(results: list[dict], max_results: int = 5) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    if not results:
        return "No relevant documents found."
    lines = []
    for i, r in enumerate(results[:max_results]):
        lines.append(f"[Source {i+1}: {r['collection'].upper()} | {r['source']} | relevance: {r['score']:.2f}]")
        lines.append(r["content"].strip())
        lines.append("")
    return "\n".join(lines)


class FieldServiceAssistant:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.collections = load_collections(self.embeddings)

        if not self.collections:
            print("[WARN] No Chroma collections loaded. Run src/ingest.py first.")

    def ask(self, query: str) -> dict:
        """
        Main entry point. Takes a technician query, returns a routed response.

        Returns:
            {
                "query": str,
                "route_type": "HIGH" | "PARTIAL" | "LOW",
                "response": str,
                "confidence_level": str,
                "escalate": bool,
                "sources": str,
                "top_score": float
            }
        """
        # Step 1: Retrieve
        results = retrieve(query, self.collections)

        # Step 2: Score confidence
        confidence = score_confidence(results)

        # Step 3: Generate LLM answer (only if confidence is HIGH or PARTIAL)
        llm_answer = None
        if confidence["level"] in ("HIGH", "PARTIAL") and results:
            context_block = build_context_block(results)
            user_message = f"Context:\n{context_block}\n\nTechnician question: {query}"
            try:
                llm_answer = llm.generate(user_message, system=SYSTEM_PROMPT)
            except Exception as e:
                llm_answer = f"[LLM generation failed: {e}]"

        # Step 4: Route through graceful degradation
        routed = route(query, results, confidence, llm_answer)

        return {
            "query": query,
            "route_type": routed["route_type"],
            "response": routed["response"],
            "confidence_level": routed["confidence_level"],
            "escalate": routed["escalate"],
            "sources": routed["sources"],
            "top_score": confidence["top_score"]
        }
