"""
vectorstore.py - GrahakNyay Day 07

Stores document chunks and embeddings in persistent ChromaDB.
"""

from pathlib import Path

from app.chunking import chunk_documents
from app.embed import embed_documents, embed_query

BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_PATH = BASE_DIR / "data" / "chroma_db"

COLLECTION_NAME = "grahaknyay_legal_documents"


def get_collection():
    """Connect to the persistent ChromaDB collection."""
    import chromadb

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
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
            "title": str(chunk.get("title", "Unknown")),
            "source": str(chunk.get("source", "Unknown")),
            "page": int(chunk.get("page", 0)),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas
    )

    print("Documents indexed successfully.")
    print("Total chunks indexed:", len(chunks))
    print("Total chunks in collection:", collection.count())

    return len(chunks)


def semantic_search(query, top_k=5):
    """Find relevant document chunks for a question."""

    if not query or not query.strip():
        return []

    if top_k <= 0:
        return []

    collection = get_collection()

    total_chunks = collection.count()

    if total_chunks == 0:
        print("ChromaDB collection is empty.")
        return []

    query_embedding = embed_query(query.strip())

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total_chunks),
        include=["documents", "metadatas", "distances"],
    )

    matches = []

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, chunk_id in enumerate(ids):
        metadata = metadatas[index] or {}

        matches.append(
            {
                "id": chunk_id,
                "text": documents[index] or "",
                "title": metadata.get("title", "Unknown"),
                "source": metadata.get("source", "Unknown"),
                "page": metadata.get("page", 0),
                "distance": distances[index],
            }
        )

    return matches


if __name__ == "__main__":
    index_documents()
