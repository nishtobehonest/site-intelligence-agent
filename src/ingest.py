"""
ingest.py
---------
Loads raw documents from data/raw/, chunks them, embeds them,
and indexes them into Chroma vector store.

Three separate Chroma collections:
  - osha         : OSHA field documentation
  - manuals      : Equipment maintenance manuals
  - job_history  : Synthetic job history records

Run this once after adding new documents to data/raw/.
Usage: python src/ingest.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

DATA_SOURCES = {
    "osha": "./data/raw/osha",
    "manuals": "./data/raw/manuals",
    "job_history": "./data/raw/job_history",
}

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def load_documents(source_dir: str):
    """Load PDFs and text files from a directory."""
    docs = []
    path = Path(source_dir)
    if not path.exists():
        print(f"  [SKIP] Directory not found: {source_dir}")
        return docs

    for file in path.rglob("*.pdf"):
        try:
            loader = PyPDFLoader(str(file))
            docs.extend(loader.load())
            print(f"  [OK] Loaded PDF: {file.name}")
        except Exception as e:
            print(f"  [ERR] Failed to load {file.name}: {e}")

    for file in path.rglob("*.txt"):
        try:
            loader = TextLoader(str(file))
            docs.extend(loader.load())
            print(f"  [OK] Loaded TXT: {file.name}")
        except Exception as e:
            print(f"  [ERR] Failed to load {file.name}: {e}")

    for file in path.rglob("*.json"):
        try:
            with open(file) as f:
                records = json.load(f)
            # Convert JSON records to LangChain Document format
            from langchain.schema import Document
            for record in records:
                content = json.dumps(record)
                metadata = {"source": str(file), "job_id": record.get("job_id", "unknown")}
                docs.append(Document(page_content=content, metadata=metadata))
            print(f"  [OK] Loaded JSON: {file.name} ({len(records)} records)")
        except Exception as e:
            print(f"  [ERR] Failed to load {file.name}: {e}")

    return docs


def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_documents(docs)


def ingest_collection(collection_name: str, source_dir: str, embeddings):
    print(f"\n--- Ingesting collection: {collection_name} ---")
    docs = load_documents(source_dir)

    if not docs:
        print(f"  [WARN] No documents found in {source_dir}. Skipping.")
        return None

    chunks = chunk_documents(docs)
    print(f"  [OK] {len(docs)} documents -> {len(chunks)} chunks")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_PERSIST_DIR
    )
    vectorstore.persist()
    print(f"  [OK] Indexed into Chroma collection: {collection_name}")
    return vectorstore


def main():
    print("=== Field Service Intelligence Assistant: Document Ingestion ===\n")
    embeddings = get_embeddings()

    for collection_name, source_dir in DATA_SOURCES.items():
        ingest_collection(collection_name, source_dir, embeddings)

    print("\n=== Ingestion complete. Run demo/demo.py to test retrieval. ===")


if __name__ == "__main__":
    main()
