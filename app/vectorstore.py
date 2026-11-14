
"""
vectorstore.py - GrahakNyay Day 07

Stores document chunks and embeddings in persistent ChromaDB.
"""

from pathlib import Path

import chromadb

from app.chunking import chunk_documents
from app.embed import embed_documents, embed_query


BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_PATH = BASE_DIR / "data" / "chroma_db"

COLLECTION_NAME = "grahaknyay_legal_documents"


def get_collection():
    """Connect to the persistent ChromaDB collection."""

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    return collection


def index_documents():
    """Chunk, embed, and store all legal documents."""

    chunks = chunk_documents()

    if not chunks:
        print("No document chunks found.")
        return 0

    collection = get_collection()

    texts = [chunk["text"] for chunk in chunks]

    embeddings = embed_documents(texts)

    ids = [chunk["id"] for chunk in chunks]

    metadatas = [
        {
            "title": chunk["title"],
            "source": chunk["source"],
            "page": chunk["page"]
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print("Documents indexed successfully.")
    print("Total chunks indexed:", len(chunks))
    print("Total chunks in collection:", collection.count())

    return len(chunks)


def semantic_search(query, top_k=5):
    """Find relevant document chunks for a question."""

    if not query.strip():
        return []

    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    matches = []

    for index in range(len(results["ids"][0])):

        matches.append({
            "text": results["documents"][0][index],
            "title": results["metadatas"][0][index]["title"],
            "source": results["metadatas"][0][index]["source"],
            "page": results["metadatas"][0][index]["page"],
            "distance": results["distances"][0][index]
        })

    return matches


if __name__ == "__main__":
    index_documents()
