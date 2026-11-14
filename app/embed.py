
"""
embed.py - GrahakNyay Day 07

Converts document chunks and search queries into embeddings.
"""

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def get_model():
    """Load the embedding model only when needed."""

    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def embed_documents(texts):
    """Convert document chunks into embeddings."""

    if not texts:
        return []

    model = get_model()

    embeddings = model.encode_document(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.tolist()


def embed_query(query):
    """Convert a search question into an embedding."""

    model = get_model()

    embedding = model.encode_query(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()


if __name__ == "__main__":

    sample_text = [
        "Consumers have the right to seek a remedy "
        "when a product is defective."
    ]

    result = embed_documents(sample_text)

    print("Embedding generated successfully.")
    print("Vector dimensions:", len(result[0]))
